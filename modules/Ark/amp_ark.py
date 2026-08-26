# Copyright (C) 2021-2022 Katelynn Cadwallader
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

import base64

from core import AMP
from core import AMP_Console
from core.DB import DBUser

DisplayImageSources = ['steam:346110', 'steam:376030']  # 346110 = ARK: Survival Evolved (the base game -- what AMP's current official ARK template, ark-seminapi.kvp, actually reports as DisplayImageSource). 376030 = the Dedicated Server tool's AppID, kept for any instance still on AMP's older/legacy ARK ADS module.


class AMPArk(AMP.AMPInstance):
    def __init__(self, instanceID: int = 0, serverdata: dict = {}, default_console: bool = False, Handler=None, TargetName: str | None = None):
        self.perms = []
        self.APIModule = 'Ark'

        super().__init__(instanceID, serverdata, Handler=Handler, TargetName=TargetName)
        self.Console = AMPArkConsole(AMPInstance=self)

        self.default_background_banner_path = 'resources/banners/Ark_Banner.png'

        if self.Avatar_url == None:
            self.DB_Server.Avatar_url = 'https://github.com/AriVenatus/GatekeeperV4/blob/main/resources/avatars/ark_avatar.png?raw=true'

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

    def getMap(self) -> str | None:
        """Returns the human-readable Map name currently configured for this Instance (eg. `Crystal Isles`),
        or `None` if the setting couldn't be found. Sourced from `Core/GetSettingsSpec`. The `Map` setting's
        category name is unverified against this specific Instance/template version -- rather than assume a
        prefix, this scans every category for a `Name == 'Map'` entry. On a miss it logs the actual category
        and setting names it saw, so the real structure can be confirmed from the log instead of guessing at
        another hardcoded name/prefix."""
        self.Login()
        result = self.CallAPI('Core/GetSettingsSpec', {})
        if not isinstance(result, dict):
            self.logger.error(f"Core/GetSettingsSpec returned unexpected payload for {self.FriendlyName} while looking up the Map: {result!r}")
            return None

        for category, settings in result.items():
            if not isinstance(settings, list):
                continue
            for setting in settings:
                if not isinstance(setting, dict) or setting.get('Name') != 'Map':
                    continue
                current_value = setting.get('CurrentValue')
                enum_values = setting.get('EnumValues') or {}
                return enum_values.get(current_value, current_value)

        seen = {
            category: [s.get('Name') for s in settings if isinstance(s, dict)]
            for category, settings in result.items() if isinstance(settings, list)
        }
        self.logger.error(f"Unable to find a 'Map' setting for {self.FriendlyName} in Core/GetSettingsSpec. Categories and setting names seen: {seen!r}")
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
