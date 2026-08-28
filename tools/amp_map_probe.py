#!/usr/bin/env python3
"""One-off diagnostic: why can't Gatekeeper read an AMP Instance's Map setting?

Standalone on purpose -- it does NOT import the bot (no threads, no DB, no Discord, no
permission bootstrap). It logs into AMP with the same credentials from the same env file
the service uses, then dumps the RAW HTTP status and body of every call involved, so the
failure is attributable instead of collapsing into `None` at a call site.

Run it on the server, as the bot's own AMP user, e.g.:

    set -a && . /opt/gatekeeper/gatekeeper.env && set +a
    /opt/gatekeeper/venv/bin/python3 tools/amp_map_probe.py

Optionally pass a substring of the Instance's FriendlyName to probe just that one:

    /opt/gatekeeper/venv/bin/python3 tools/amp_map_probe.py ARK

Nothing here writes to AMP -- every call is a read.
"""
from __future__ import annotations

import json
import os
import sys

import requests

try:
    import pyotp
except ImportError:
    pyotp = None

HEADERS = {
    'Accept': 'text/javascript',
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'X-Requested-With': 'XMLHttpRequest',
}

# Candidate nodes for the ARK Map, per AMP's official ark-seminapi template.
MAP_NODES = ['GenericModule.App.Map', 'ARKSEModule.Game.Map', 'Map']

# Settings permission nodes to test the session against. `core/amp_permissions.py` currently
# denies `Settings.*` outright, on the (now outdated) premise that nothing calls Settings APIs.
PERMISSION_NODES = ['Settings.*', 'Settings.GenericModule.*', 'Core.*', 'Core.AppManagement.*']

MAX_BODY = 1500


# Values AMP stores for the stock ARK maps, plus the labels it shows for them. Used to spot the
# Map in an arbitrary JSON blob without knowing which key it hides under.
KNOWN_MAP_VALUES = (
    'TheIsland', 'TheCenter', 'Ragnarok', 'Aberration_P', 'ScorchedEarth_P', 'Extinction',
    'Valguero_P', 'Genesis', 'Gen2', 'CrystalIsles', 'LostIsland', 'Fjordur', 'Aquatica',
)


def find_maps(obj, path='') -> list[str]:
    """Recursively reports `path = value` for anything that looks like a Map setting --
    either a key named Map, or a value matching a known ARK map name."""
    hits = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            here = f'{path}.{key}' if path else str(key)
            if 'map' in str(key).lower() and isinstance(value, (str, int, float, bool)):
                hits.append(f'{here} = {value!r}')
            hits.extend(find_maps(value, here))
    elif isinstance(obj, list):
        for i, value in enumerate(obj):
            hits.extend(find_maps(value, f'{path}[{i}]'))
    elif isinstance(obj, str) and obj in KNOWN_MAP_VALUES:
        hits.append(f'{path} = {obj!r}')

    return hits


def call_quiet(session: requests.Session, url: str, endpoint: str, params: dict, session_id: str = '') -> object:
    """Like `call()` but without printing the body -- for responses we summarise ourselves."""
    body = dict(params)
    body['SESSIONID'] = session_id
    headers = dict(HEADERS)
    if session_id:
        headers['Authorization'] = f'Bearer {session_id}'

    resp = session.post(url + endpoint, headers=headers, data=json.dumps(body))
    print(f'    HTTP {resp.status_code}  ({len(resp.text)} chars)')
    try:
        return resp.json()
    except ValueError:
        return None



def collect_permission_nodes(obj) -> list[str]:
    """Collects every permission node string out of Core/GetPermissionsSpec.

    AMP's nodes are ALREADY fully qualified at every level of the tree (`Settings`,
    `Settings.ADSModule`, `Settings.ADSModule.ADS`, `Settings.ADSModule.ADS.AlertMessage`),
    so this must NOT prepend the parent's path -- doing so produced unreadable garbage like
    `Settings.Settings.ADSModule.Settings.ADSModule.ADS....` on the first run, which then hit
    the output cap before any GenericModule branch became visible."""
    nodes = []
    if isinstance(obj, dict):
        name = obj.get('Node') or obj.get('Name')
        if isinstance(name, str) and name:
            nodes.append(name)
        for key, value in obj.items():
            if key in ('Node', 'Name', 'Description'):
                continue
            nodes.extend(collect_permission_nodes(value))
    elif isinstance(obj, list):
        for value in obj:
            nodes.extend(collect_permission_nodes(value))

    return nodes



def dump_permission_nodes(session: requests.Session, url: str, session_id: str) -> list[str]:
    """Dumps AMP's own permission-node list for whichever scope `url` points at.

    Scope matters and is easy to get wrong: the MAIN ADS instance runs no game module, so its
    spec can never contain a `Settings.GenericModule` branch no matter what the game Instance
    supports. The branch that decides whether Gatekeeper may read the ARK settings only exists
    in the game Instance's OWN spec, which is why this runs against both."""
    spec = call_quiet(session, url, 'Core/GetPermissionsSpec', {}, session_id)
    if isinstance(spec, dict) and 'result' in spec:
        spec = spec['result']

    nodes = sorted(set(collect_permission_nodes(spec)))
    print(f'    total permission nodes: {len(nodes)}')

    settings_nodes = [n for n in nodes if n.split('.')[0] == 'Settings']
    module_nodes = [n for n in settings_nodes if n.split('.')[1:2] == ['GenericModule']]
    print(f'    Settings subtree: {len(settings_nodes)} nodes, '
          f'top-level branches: {sorted({n.split(".")[1] for n in settings_nodes if "." in n})}')
    if module_nodes:
        print(f'    >> Settings.GenericModule branch EXISTS here ({len(module_nodes)} nodes):')
        for node in module_nodes:
            print(f'       {node}')
    else:
        print('    >> No Settings.GenericModule branch in this scope.')

    backup = [n for n in nodes if 'backup' in n.lower()]
    print(f'    backup-related nodes: {backup if backup else "NONE"}')

    return nodes



def call(session: requests.Session, url: str, endpoint: str, params: dict, session_id: str = '') -> object:
    """POSTs one AMP API call and prints the raw status + body. Returns the parsed JSON or None."""
    body = dict(params)
    body['SESSIONID'] = session_id
    headers = dict(HEADERS)
    if session_id:
        headers['Authorization'] = f'Bearer {session_id}'

    resp = session.post(url + endpoint, headers=headers, data=json.dumps(body))
    text = resp.text
    truncated = '' if len(text) <= MAX_BODY else f' ...[{len(text) - MAX_BODY} more chars]'
    print(f'    HTTP {resp.status_code}  {text[:MAX_BODY]}{truncated}')

    try:
        return resp.json()
    except ValueError:
        return None


def login(session: requests.Session, url: str, user: str, password: str, auth_secret: str) -> str | None:
    token = ''
    if auth_secret:
        if pyotp is None:
            print('  !! pyotp is not installed in this interpreter, cannot compute the 2FA token.')
            return None
        token = pyotp.TOTP(auth_secret).now()

    print(f'  Core/Login at {url}')
    result = call(session, url, 'Core/Login', {
        'username': user,
        'password': password,
        'token': token,
        'rememberMe': True,
    })
    if isinstance(result, dict) and isinstance(result.get('sessionID'), str):
        return result['sessionID']

    print('  !! Login did not return a sessionID.')
    return None


def main() -> int:
    user = os.getenv('GATEKEEPER_AMP_USER', '')
    password = os.getenv('GATEKEEPER_AMP_PASSWORD', '')
    base = os.getenv('GATEKEEPER_AMP_URL', '').rstrip('/')
    auth_secret = os.getenv('GATEKEEPER_AMP_AUTH', '')

    if not user or not password or not base:
        print('Missing GATEKEEPER_AMP_USER / GATEKEEPER_AMP_PASSWORD / GATEKEEPER_AMP_URL in the environment.')
        print('Source the service env file first, e.g.  set -a && . /opt/gatekeeper/gatekeeper.env && set +a')
        return 1

    name_filter = sys.argv[1].lower() if len(sys.argv) > 1 else ''
    session = requests.Session()
    main_url = base + '/API/'

    print('== Main AMP instance ==')
    session_id = login(session, main_url, user, password, auth_secret)
    if session_id is None:
        return 1

    print('\n== Core/GetPermissionsSpec -- MAIN ADS instance ==')
    dump_permission_nodes(session, main_url, session_id)

    print('\n== ADSModule/GetInstances ==')
    instances = call(session, main_url, 'ADSModule/GetInstances', {}, session_id)
    if isinstance(instances, dict) and 'result' in instances:
        instances = instances['result']

    targets = []
    if isinstance(instances, list):
        for target in instances:
            for inst in (target or {}).get('AvailableInstances', []):
                print(f"    {inst.get('InstanceID')}  {inst.get('FriendlyName')!r}  "
                      f"Module={inst.get('Module')!r}  DisplayImageSource={inst.get('DisplayImageSource')!r}")
                if inst.get('Module') == 'ADS':
                    continue
                if name_filter and name_filter not in str(inst.get('FriendlyName', '')).lower():
                    continue
                targets.append(inst)

    if not targets:
        print('\nNo matching Instances to probe.')
        return 1

    for inst in targets:
        friendly = inst.get('FriendlyName')
        inst_url = f"{base}/API/ADSModule/Servers/{inst.get('InstanceID')}/API/"
        print(f'\n\n======== {friendly} ========')

        # (1) Does the Map already come back from ADSModule/GetInstances, with no extra
        # permission and no extra API call? The per-Instance object is large and was truncated
        # on the first run, so dump it whole and scan it for anything Map-shaped.
        print('  -- Full Instance object from ADSModule/GetInstances --')
        print(json.dumps(inst, indent=2, default=str))
        hits = find_maps(inst)
        print(f'  >> Map-shaped values found in the Instance object: {hits if hits else "NONE"}')

        print('\n  -- Core/Login (Instance-scoped session) --')
        inst_session = login(session, inst_url, user, password, auth_secret)
        if inst_session is None:
            continue

        print('\n  -- Core/GetPermissionsSpec -- this Instance --')
        dump_permission_nodes(session, inst_url, inst_session)

        # (2) Control call on a node we KNOW exists and is visible (it came back in the spec on
        # the first run). If this works while the Map node says "No such node", then GetConfig
        # itself is fine and the Map node is either named differently or filtered out.
        print('\n  -- Core/GetConfig control node (known to exist and be readable) --')
        call(session, inst_url, 'Core/GetConfig', {'node': 'FileManagerPlugin.FileManager.BasePath'}, inst_session)

        print('\n  -- Core/GetConfig candidate Map nodes --')
        for node in MAP_NODES:
            print(f'    node={node!r}')
            call(session, inst_url, 'Core/GetConfig', {'node': node}, inst_session)

        # (3) The decisive test for the permission theory: if EVERY setting the spec returns is
        # marked AlwaysAllowRead, the spec is being filtered by permission, not by what exists.
        print('\n  -- Core/GetSettingsSpec (permission-filter analysis) --')
        spec = call_quiet(session, inst_url, 'Core/GetSettingsSpec', {}, inst_session)
        if isinstance(spec, dict) and 'result' in spec and isinstance(spec['result'], dict):
            spec = spec['result']
        if not isinstance(spec, dict):
            print(f'    unexpected spec response: {spec!r}')
            continue

        always, gated, nodes = 0, [], []
        for category, settings in spec.items():
            if not isinstance(settings, list):
                continue
            for setting in settings:
                if not isinstance(setting, dict):
                    continue
                nodes.append(setting.get('Node'))
                if setting.get('AlwaysAllowRead') is True:
                    always += 1
                else:
                    gated.append(setting.get('Node'))
                if setting.get('Name') == 'Map' or setting.get('FieldName') == 'Map':
                    print(f'    !! Map entry found: {setting}')

        print(f'    categories: {sorted(spec)}')
        print(f'    settings returned: {len(nodes)}  |  AlwaysAllowRead=True: {always}  |  gated: {len(gated)}')
        if gated:
            print(f'    gated nodes returned anyway (permission theory WEAKENED): {gated[:20]}')
        else:
            print('    >> Every returned setting is AlwaysAllowRead -- the spec is being filtered')
            print('       by permission. `-Settings.*` in core/amp_permissions.py is the cause.')
        print(f'    node prefixes seen: {sorted({str(n).split(".")[0] for n in nodes if n})}')

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
