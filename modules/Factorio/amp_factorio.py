# Copyright (C) 2021-2022 Katelynn Cadwallader
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations
from core import AMP
from core import AMP_Console


# Resources
# https://wiki.factorio.com/Console

DisplayImageSources = ['steam:427520']


class AMPFactorio(AMP.AMPInstance):
    def __init__(self, instanceID: int = 0, serverdata: dict = {}, default_console: bool = False, Handler=None, TargetName: str | None = None):
        self.APIModule = 'Factorio'

        super().__init__(instanceID, serverdata, Handler=Handler, TargetName=TargetName)
        self.Console = AMPFactorioConsole(AMPInstance=self)

        self.default_background_banner_path = 'resources/banners/Factorio_Banner.jpg'

        if self.Avatar_url == None:
            self.DB_Server.Avatar_url = 'https://github.com/AriVenatus/GatekeeperV4/blob/main/resources/avatars/factorio_avatar.png?raw=true'

    def setup_Gatekeeper_Permissions(self):
        """Sets the Permissions for Factorio Modules"""
        self.logger.warning(f'Setting up {self.FriendlyName} Factorio Module permissions...')
        for perm in self.perms:
            enabled = True
            if perm.startswith('-'):
                enabled = False
                perm = perm[1:]

            if self.setAMPRolePermissions(self.AMP_BotRoleID, perm, enabled):
                self.logger.dev(f'Set {perm} for {self.AMP_BotRoleID} to {enabled}')

    def Chat_Message(self, message: str, author: str | None = None, author_prefix: str | None = None, server_prefix: str | None = None):
        # See https://wiki.factorio.com/Rich_text
        # Replace bracket characters so untrusted text can't close the current rich-text tag
        # early or inject a new/malformed tag (e.g. [gps=...], [item=...]).
        if message != None:
            message = message.replace('[', '(').replace(']', ')')
        if author != None:
            author = author.replace('[', '(').replace(']', ')')
        if author_prefix != None:
            author_prefix = author_prefix.replace('[', '(').replace(']', ')')
        if server_prefix != None:
            server_prefix = server_prefix.replace('[', '(').replace(']', ')')

        content = '[color=blue]"[Discord]"[/color] '
        if server_prefix != None:
            content += f'[color=gold]({server_prefix})[/color] '

        if author_prefix != None:
            content += f'[color=yellow]({author_prefix})[/color] '

        content += f'[color=default]<{author}>: {message}[/color]'
        self.ConsoleMessage(content)


class AMPFactorioConsole(AMP_Console.AMPConsole):
    def __init__(self, AMPInstance=AMPFactorio):
        super().__init__(AMPInstance)
