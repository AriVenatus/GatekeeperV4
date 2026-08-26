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

    # Attribute name substrings that must never be logged by getMap()'s diagnostic dump below --
    # AMPInstance carries live auth state (eg. self.SessionID, used as a Bearer token) as plain attributes.
    _SENSITIVE_ATTR_SUBSTRINGS = ('session', 'password', 'token', 'auth', 'key', 'cookie', 'secret')

    def getMap(self) -> str | None:
        """Returns the human-readable Map name currently configured for this Instance (eg. `Crystal Isles`),
        or `None` if it couldn't be found. `Core/GetSettingsSpec` turned out NOT to carry ARK-specific settings
        at all for a Generic-module-template Instance (confirmed live -- it only returned Core/AMP categories
        like 'File Manager'/'System Settings', no ARK category whatsoever), so that approach is unusable here.
        This instead checks a `Metadata` attribute -- `ADSModule/GetInstances`' per-Instance fields get applied
        directly onto this object via `setattr()` in `AMP._updateInstanceAttributes()`, and AMP commonly surfaces
        a one-line Metadata string per Instance, which is the next most likely place for this. On a miss it logs
        every other short string/bool/int attribute already on this object (skipping anything that looks like
        live auth state) so the real field can be found from the log instead of guessed at again."""
        metadata = getattr(self, 'Metadata', None)
        if isinstance(metadata, str) and metadata.strip():
            return metadata.strip()

        seen = {}
        for name, value in vars(self).items():
            if any(bad in name.lower() for bad in self._SENSITIVE_ATTR_SUBSTRINGS):
                continue
            if isinstance(value, (str, int, float, bool)) and len(str(value)) <= 200:
                seen[name] = value
        self.logger.error(f"Unable to find a Map/Metadata attribute for {self.FriendlyName}. Other short attributes seen on this Instance: {seen!r}")
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
