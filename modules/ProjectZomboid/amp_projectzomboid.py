# Copyright (C) 2021-2022 Katelynn Cadwallader
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

import re
import secrets

from core import AMP
from core import AMP_Console
from core import DB
from core.DB import DBUser


DisplayImageSources = ['steam:108600']

_USERNAME_MAX_LENGTH = 20


class AMPProjectzomboid(AMP.AMPInstance):
    def __init__(self, instanceID: int = 0, serverdata: dict = {}, default_console: bool = False, Handler=None, TargetName: str | None = None):
        self.perms = [
            'Core.AppManagement.*',  # addWhitelist()/removeWhitelist() send adduser/addusertowhitelist/removeuserfromwhitelist console commands
        ]
        self.APIModule = 'Project Zomboid'

        super().__init__(instanceID, serverdata, Handler=Handler, TargetName=TargetName)
        self.Console = AMPProjectzomboidConsole(AMPInstance=self)

        self.default_background_banner_path = 'resources/banners/Project_Zomboid_banner_1.jpg'

        self._apply_default_avatar('https://github.com/AriVenatus/GatekeeperV4/blob/main/resources/avatars/project_zomboid_avatar.png?raw=true')

    # This isn't the best implementation...
    # Project Zomboid has one-way chat from game to Discord. You need to enable that.
    # This method will allow messages from Discord to be posted in-game.
    # However, they are server broadcasts and will be posted in the middle of the screen.
    def Chat_Message(self, message: str, author: str | None = None, author_prefix: str | None = None, server_prefix: str | None = None):
        """Sends a customized message via servermsg through the console."""
        # Replace double quotes with single quotes so untrusted text can't break out of the
        # double-quote-delimited console command and inject new console input.
        if message != None:
            message = message.replace('"', "'")
        if author != None:
            author = author.replace('"', "'")
        if author_prefix != None:
            author_prefix = author_prefix.replace('"', "'")
        if server_prefix != None:
            server_prefix = server_prefix.replace('"', "'")

        self.Login()
        content = 'servermsg "[Discord]'
        if server_prefix != None:
            content += f'({server_prefix}) '

        if author_prefix != None:
            content += f'({author_prefix}) '

        content += f'[{author}]: {message}"'
        self.ConsoleMessage(content)

    def Broadcast_Message(self, message, prefix: str | None = None):
        """Used to Send a Broadcast Message to the Server"""
        self.Login()
        content = 'servermsg "'
        if prefix != None:
            content += f'<{prefix}> '

        content += f'{message}"'
        self.ConsoleMessage(content)

    # Whitelisting ------------------------------------------------------------------------------
    # Unlike Minecraft (IGN/UUID) or ARK (SteamID64), PZ has no pre-existing external identity to
    # whitelist -- whitelisting IS creating a server-side username/password login account (via the
    # `adduser` console command), and the player must be told that password to actually get in.
    # So Gatekeeper owns the credential: it generates it once, stores it on the DBUser, and the
    # `/pz credentials` command (cog_projectzomboid.py) is how the player retrieves it -- there is
    # no DM push, since a bot-initiated DM silently fails for anyone with DMs disabled.

    def _generate_username(self, db_user: DBUser) -> str:
        """Derives a PZ login username from the User's Discord name, falling back to a Discord-ID-based
        name if that sanitizes to nothing, and disambiguating against any existing Gatekeeper User with
        the same candidate name (PZ_Username is only DB-unique-constrained on fresh installs -- upgraded
        DBs can't get a UNIQUE constraint added via ALTER TABLE -- so this check is what actually prevents
        two Discord Users from being handed the same PZ login)."""
        base = re.sub(r'[^A-Za-z0-9_]', '', db_user.DiscordName or '')[:_USERNAME_MAX_LENGTH]
        if not base:
            base = 'Survivor'

        db = DB.getDBHandler().DB
        candidate = base
        # Capped, not `while True`: appending a suffix then re-truncating to _USERNAME_MAX_LENGTH
        # can reproduce the exact same candidate every time (eg. a 20-char `base` with a 1-char
        # suffix truncated back off), which would otherwise spin forever -- this call runs
        # synchronously on the bot's event loop from a Discord command handler.
        for suffix in range(2, 100):
            existing = db.GetUser(candidate)
            if existing is None or existing.ID == db_user.ID:
                return candidate
            suffix_str = str(suffix)
            candidate = f'{base[:_USERNAME_MAX_LENGTH - len(suffix_str)]}{suffix_str}'

        # Practically unreachable (98 real collisions against the same sanitized base name) --
        # fall back to something unique by construction (DiscordIDs are themselves unique)
        # instead of looping any further.
        return f'{base[:10]}{db_user.DiscordID}'

    def addWhitelist(self, db_user: DBUser | None = None, in_gamename: str | None = None) -> bool:
        """Grants `db_user` access -- creates a new PZ login account on first call (`adduser`), or
        re-enables a previously-removed one on any later call (`addusertowhitelist`), since
        `removeWhitelist()` only un-whitelists, it doesn't delete the account. Returns `True` only if
        the Console command actually reached the server."""
        if db_user is None:
            return False

        self.Login()
        if db_user.PZ_Username:
            result = self.ConsoleMessage(f'addusertowhitelist "{db_user.PZ_Username}"')
            if not bool(result):
                return False
            db_user.PZ_Whitelisted = True
            return True

        username = self._generate_username(db_user)
        password = secrets.token_urlsafe(9)
        result = self.ConsoleMessage(f'adduser "{username}" "{password}"')
        if not bool(result):
            return False

        db_user.PZ_Username = username
        db_user.PZ_Password = password
        db_user.PZ_Whitelisted = True
        return True

    def removeWhitelist(self, db_user: DBUser | None = None, in_gamename: str | None = None) -> bool:
        """Un-whitelists `db_user`'s PZ login account. Returns `True` only if the Console command
        actually reached the server. Does NOT delete the account or clear `PZ_Username`/`PZ_Password`
        -- a later `addWhitelist()` re-enables the same login rather than minting a new one."""
        if db_user is None or not db_user.PZ_Username:
            return False

        self.Login()
        result = self.ConsoleMessage(f'removeuserfromwhitelist "{db_user.PZ_Username}"')
        if not bool(result):
            return False

        db_user.PZ_Whitelisted = False
        return True

    def check_Whitelist(self, db_user: DBUser | None = None, in_gamename: str | None = None):
        """Returns `None` if `db_user` is currently whitelisted \n
        Returns `True` if they aren't (eligible, needs `addWhitelist()`) -- this includes a User
        who has a PZ login (`PZ_Username`) from a PAST Whitelist that was since removed, since
        `PZ_Whitelisted` (not account existence) is what tracks current status \n
        Returns `False` if there's no `db_user` to check at all -- PZ has no free-text
        identity (`in_gamename`) to fall back to look up, unlike Minecraft/ARK."""
        if db_user is None:
            return False

        return None if db_user.PZ_Whitelisted else True


class AMPProjectzomboidConsole(AMP_Console.AMPConsole):
    def __init__(self, AMPInstance=AMPProjectzomboid):
        super().__init__(AMPInstance)
