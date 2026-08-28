# Copyright (C) 2021-2022 Katelynn Cadwallader
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

import base64
import time

from core import AMP
from core import AMP_Console
from core.DB import DBUser

DisplayImageSources = ['steam:346110', 'steam:376030']  # 346110 = ARK: Survival Evolved (the base game -- what AMP's current official ARK template, ark-seminapi.kvp, actually reports as DisplayImageSource). 376030 = the Dedicated Server tool's AppID, kept for any instance still on AMP's older/legacy ARK ADS module.


class AMPArk(AMP.AMPInstance):
    def __init__(self, instanceID: int = 0, serverdata: dict = {}, default_console: bool = False, Handler=None, TargetName: str | None = None):
        # NOT an empty list. `self.perms` is what BOTH check_SessionPermissions() and
        # check_GatekeeperRole_Permissions() iterate over, so an empty one makes them verify
        # nothing and report success -- which is how an ARK Instance whose `Gatekeeper` role was
        # never provisioned still logged "We have proper permissions" on every startup while its
        # delegate session actually held only `Instances.*` (no FileManager, no Settings). AMP
        # named the gap itself once a file listing was attempted: "This method requires the
        # FileManager.FileManager.BrowseFiles permission."
        #
        # These strings must match VERBATIM what setup_Gatekeeper_Permissions() grants -- ARK
        # doesn't override it, so that's perms_super() plus perms_instance_only(), and
        # check_GatekeeperRole_Permissions() compares by exact string membership, not by
        # wildcard expansion. Listing a subset is fine (and deliberate: the ADS-only nodes in
        # perms_super() have nothing to verify on a game Instance); inventing a narrower spelling
        # of one is not, it would warn about a permission that is in fact granted.
        self.perms = [
            'FileManager.*',            # getWhitelist() browses/reads PlayersJoinNoCheckList.txt
            'Core.AppManagement.*',     # addWhitelist()/removeWhitelist() send RCON console commands
            'LocalFileBackup.Backup.CreateBackup',  # /server backup -> takeBackup()
        ]
        self.APIModule = 'Ark'

        super().__init__(instanceID, serverdata, Handler=Handler, TargetName=TargetName)
        self.Console = AMPArkConsole(AMPInstance=self)

        self.default_background_banner_path = 'resources/banners/Ark_Banner.png'

        self._apply_default_avatar('https://github.com/AriVenatus/GatekeeperV4/blob/main/resources/avatars/ark_avatar.png?raw=true')

    def _is_valid_steamid64(self, value: str | None) -> bool:
        """Validates that `value` looks like a well-formed SteamID64 before it's interpolated into a console command."""
        if value is None:
            return False
        if not value.isdigit():
            return False
        if len(value) != 17:
            return False

        return value.startswith('7656119')

    def addWhitelist(self, db_user: DBUser | None = None, in_gamename: str | None = None) -> bool:
        """Adds a User to the Whitelist *Supports SteamID64*. Returns `True` only if the
        Console command actually reached the server (eg. `False` on a missing
        Core.AppManagement.SendConsoleInput permission)."""
        steamid = in_gamename if db_user is None else db_user.SteamID
        if not self._is_valid_steamid64(steamid):
            return False

        self.Login()
        result = self.ConsoleMessage(f'AllowPlayerToJoinNoCheck {steamid}')
        return bool(result)

    def removeWhitelist(self, db_user: DBUser | None = None, in_gamename: str | None = None) -> bool:
        """Removes a User from the Whitelist *Supports SteamID64*. Returns `True` only if the
        Console command actually reached the server."""
        steamid = in_gamename if db_user is None else db_user.SteamID
        if not self._is_valid_steamid64(steamid):
            return False

        self.Login()
        result = self.ConsoleMessage(f'DisallowPlayerToJoinNoCheck {steamid}')
        return bool(result)

    def getWhitelist(self) -> list[str]:
        """Checks the Whitelist File for Ark Users (SteamID64 entries)"""
        for directory in ('ShooterGame/Binaries/Linux', 'ShooterGame/Binaries/Win64'):
            try:
                file_directory = self.getDirectoryListing(directory)
            except Exception:
                continue

            # CallAPI() returns False (not a list) on a permission/transport failure -- guard
            # against that instead of crashing with a confusing "'bool' object is not iterable".
            if not isinstance(file_directory, list):
                continue

            for entry in file_directory:
                if entry['Filename'] == 'PlayersJoinNoCheckList.txt':
                    chunk = self.getFileChunk(f'{directory}/PlayersJoinNoCheckList.txt', 0, 33554432)
                    if not isinstance(chunk, dict) or 'Base64Data' not in chunk:
                        continue
                    whitelist_data = base64.b64decode(chunk['Base64Data'])
                    lines = (line.strip() for line in whitelist_data.decode('utf-8').splitlines())
                    return [line for line in lines if line]

        return []

    # AMP config nodes that may hold the currently selected Map, most likely first. Verified against
    # AMP's own official ARK template in CubeCoders/AMPTemplates (`ark-seminapi.kvp` +
    # `ark-seminapiconfig.json`): the Map is a Generic-module *app setting* with `FieldName: "Map"`,
    # and the template itself addresses app settings by their full node path -- its
    # `Meta.EndpointURIFormat` references `{GenericModule.App.Ports.$QueryPort}` -- which is where
    # `GenericModule.App.Map` comes from. The remaining entries cover the legacy dedicated ARK ADS
    # module. Each is read with its own `Core/GetConfig` call -- see _get_map_configs() for why
    # the plural `Core/GetConfigs` is unusable here.
    _MAP_CONFIG_NODES = ('GenericModule.App.Map', 'ARKSEModule.Game.Map', 'Map')
    # Selecting "Custom" in the Map dropdown stores the literal placeholder `{{CustomMap}}` as the
    # value; the real name then lives in this companion setting (`FieldName: "CustomMap"`).
    _CUSTOM_MAP_CONFIG_NODES = ('GenericModule.App.CustomMap', 'CustomMap')
    # `Core/GetSettingsSpec` fallback: the Map setting's category on the current template is
    # `"ARK SE:stadia_controller"` -- the part after the colon is just an icon name, so match the
    # prefix only. NOTE this whole path is known NOT to work on a Generic-module-template Instance
    # (confirmed live 2026-08-26: the spec came back with Core/AMP categories only, no ARK category
    # at all), it's kept purely for the legacy dedicated ARK ADS module.
    _MAP_SPEC_CATEGORY_PREFIX = 'ARK SE:'
    # Cache both hits and misses for this long. getMap() is called from the Banner Group loop on
    # every tick, per ARK Instance -- without this, a miss would also re-log its diagnostic every
    # tick, and the Map realistically only changes on an Instance restart.
    _MAP_CACHE_SECONDS = 300

    def _map_display_name(self, value: str, enum_values: dict | None) -> str:
        """Maps a raw AMP setting value (eg. `TheIsland`) to the label AMP shows for it
        (eg. `The Island`), falling back to the raw value when there's no enum entry."""
        label = value
        if isinstance(enum_values, dict) and value in enum_values and isinstance(enum_values[value], str):
            label = enum_values[value]
        # AMP marks the template default as eg. `The Island (default)`; that suffix is noise in an embed.
        if label.endswith(' (default)'):
            label = label[:-len(' (default)')]

        return label.strip()

    def _get_map_configs(self, nodes: tuple[str, ...]) -> tuple[dict, list]:
        """Reads `nodes` from AMP and returns `({key: setting_dict}, raw_responses)`.

        Uses `Core/GetConfig` (singular, one call per node) rather than `Core/GetConfigs`.
        The plural form is never routed through to the Instance on this setup -- the ADS answers
        it with `{"Title": "Instance Unavailable"}` regardless of permissions, while the singular
        form resolves normally against the very same session (confirmed live: it returned
        `FileManagerPlugin.FileManager.BasePath` in full while the plural failed). A handful of
        extra calls every 5 minutes is a fine price for an endpoint that actually works.

        Settings are indexed under their `Node`, `Name` AND `FieldName`, since which of those AMP
        puts on a response isn't guaranteed. Raw responses are returned so a miss can log what
        actually came over the wire."""
        configs = {}
        raw = []
        for node in nodes:
            setting = self.CallAPI('Core/GetConfig', {'node': node})
            raw.append({node: setting})
            if not isinstance(setting, dict):
                continue
            # AMP reports an unknown/invisible node as an error object rather than an empty result.
            if 'CurrentValue' not in setting:
                continue
            for key in (setting.get('Node'), setting.get('Name'), setting.get('FieldName'), node):
                if isinstance(key, str) and key not in configs:
                    configs[key] = setting

            # `nodes` is ordered most-likely-first and only one of them can be the Map, so stop
            # at the first that resolved rather than spending calls on the legacy spellings.
            break

        return configs, raw

    def _getMap_from_settings_spec(self) -> str | None:
        """Legacy dedicated-ARK-ADS-module fallback: scan `Core/GetSettingsSpec` for a `Map` entry."""
        result = self.CallAPI('Core/GetSettingsSpec', {})
        if not isinstance(result, dict):
            return None

        for category, settings in result.items():
            if not isinstance(settings, list):
                continue
            if isinstance(category, str) and not category.startswith(self._MAP_SPEC_CATEGORY_PREFIX):
                continue
            for setting in settings:
                if not isinstance(setting, dict) or setting.get('Name') != 'Map':
                    continue
                value = setting.get('CurrentValue')
                if isinstance(value, str) and value.strip():
                    return self._map_display_name(value.strip(), setting.get('EnumValues'))

        return None

    def getMap(self) -> str | None:
        """Returns the human-readable Map name currently configured for this Instance (eg. `Crystal Isles`),
        or `None` if it couldn't be found. Reads AMP's config node directly via `Core/GetConfig` rather
        than hunting through `Core/GetSettingsSpec` -- see `_MAP_CONFIG_NODES` for where the node name is
        verified from, and for why the spec-scanning approach can't work on the current template. The result
        (including a miss) is cached for `_MAP_CACHE_SECONDS`, since the Banner Group loop calls this on
        every tick."""
        now = time.time()
        if now - getattr(self, '_map_cache_time', 0) < self._MAP_CACHE_SECONDS:
            return getattr(self, '_map_cache_value', None)

        self._map_cache_time = now
        self._map_cache_value = None

        self.Login()
        configs, raw = self._get_map_configs(self._MAP_CONFIG_NODES)

        map_value = None
        enum_values = None
        # `'Map'` is both the last entry in _MAP_CONFIG_NODES and the `Name`/`FieldName` every
        # candidate node resolves to, so this covers the `Node`-less response shape too.
        for node in self._MAP_CONFIG_NODES:
            setting = configs.get(node)
            if not isinstance(setting, dict):
                continue
            value = setting.get('CurrentValue')
            if isinstance(value, str) and value.strip():
                map_value = value.strip()
                enum_values = setting.get('EnumValues')
                break

        if map_value is not None:
            # `{{CustomMap}}` (or any other unresolved placeholder) means "Custom" is selected.
            if '{{' in map_value:
                custom, custom_raw = self._get_map_configs(self._CUSTOM_MAP_CONFIG_NODES)
                for setting in custom.values():
                    value = setting.get('CurrentValue')
                    if isinstance(value, str) and value.strip():
                        self._map_cache_value = value.strip()
                        return self._map_cache_value

                self.logger.error(
                    f'{self.FriendlyName} has a Custom Map selected but no Custom Map Name is set; '
                    f'`Core/GetConfig` for {list(self._CUSTOM_MAP_CONFIG_NODES)} returned {custom_raw!r}'
                )
                return None

            self._map_cache_value = self._map_display_name(map_value, enum_values)
            return self._map_cache_value

        spec_map = self._getMap_from_settings_spec()
        if spec_map is not None:
            self._map_cache_value = spec_map
            return self._map_cache_value

        self.logger.error(
            f'Unable to find the Map setting for {self.FriendlyName}. `Core/GetConfig` for '
            f'{list(self._MAP_CONFIG_NODES)} returned {raw!r}, and no `Map` entry was found under a '
            f'{self._MAP_SPEC_CATEGORY_PREFIX!r} category in `Core/GetSettingsSpec` either.'
        )
        return None

    def check_Whitelist(self, db_user: DBUser | None = None, in_gamename: str | None = None):
        self.logger.dev(f'Checking if {in_gamename if db_user == None else db_user.DiscordName} is whitelisted on {self.FriendlyName}...')
        """Checks if the User is already in the whitelist file. Supports DB User and SteamID64.\n
        Returns `None` if the SteamID64 is whitelisted \n
        Returns `False` if no SteamID64 exists \n
        Returns `True` if not in Whitelisted"""
        steamid = None
        if db_user == None and in_gamename != None:
            steamid = in_gamename

        if db_user != None:
            if db_user.SteamID == None:
                if in_gamename != None and self._is_valid_steamid64(in_gamename):
                    db_user.SteamID = in_gamename
                    steamid = in_gamename

                else:
                    return False

            else:
                steamid = db_user.SteamID

        if steamid == None or not self._is_valid_steamid64(steamid):
            return False

        self.Login()
        whitelist = self.getWhitelist()
        if steamid in whitelist:
            return None

        return True

    def Chat_Message(self, message: str, author: str | None = None, author_prefix: str | None = None, server_prefix: str | None = None):
        """Sends a customized message via ServerChat through the console."""
        self.Login()
        content = '[Discord]'
        if server_prefix != None:
            content += f' ({server_prefix})'

        if author_prefix != None:
            content += f' ({author_prefix})'

        content += f' <{author}> {message}'
        self.ConsoleMessage(f'ServerChat {content}')

    def Broadcast_Message(self, message, prefix: str | None = None):
        """Used to Send a Broadcast Message to the Server"""
        self.Login()
        content = f'<{prefix}> {message}' if prefix != None else message
        self.ConsoleMessage(f'ServerChat {content}')


class AMPArkConsole(AMP_Console.AMPConsole):
    def __init__(self, AMPInstance=AMPArk):
        super().__init__(AMPInstance)
