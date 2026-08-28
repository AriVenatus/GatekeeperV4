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

        print('  -- Core/Login (Instance-scoped session) --')
        inst_session = login(session, inst_url, user, password, auth_secret)
        if inst_session is None:
            continue

        print('\n  -- Core/CurrentSessionHasPermission --')
        for node in PERMISSION_NODES:
            print(f'    node={node!r}')
            call(session, inst_url, 'Core/CurrentSessionHasPermission', {'PermissionNode': node}, inst_session)

        print('\n  -- Core/GetConfig (one node at a time; an error body names the real reason) --')
        for node in MAP_NODES:
            print(f'    node={node!r}')
            call(session, inst_url, 'Core/GetConfig', {'node': node}, inst_session)

        print('\n  -- Core/GetConfigs (all candidate nodes at once) --')
        call(session, inst_url, 'Core/GetConfigs', {'nodes': MAP_NODES}, inst_session)

        print('\n  -- Core/GetSettingsSpec (category names only) --')
        spec = call(session, inst_url, 'Core/GetSettingsSpec', {}, inst_session)
        if isinstance(spec, dict) and 'result' in spec and isinstance(spec['result'], dict):
            spec = spec['result']
        if isinstance(spec, dict):
            print(f'    categories: {sorted(spec)}')
            for category, settings in spec.items():
                if not isinstance(settings, list):
                    continue
                names = [s.get('Name') or s.get('FieldName') for s in settings if isinstance(s, dict)]
                if any(n == 'Map' for n in names):
                    print(f'    !! category {category!r} DOES contain a Map entry')
                    for s in settings:
                        if isinstance(s, dict) and (s.get('Name') == 'Map' or s.get('FieldName') == 'Map'):
                            print(f'       {s}')

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
