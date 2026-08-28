# Copyright (C) 2021-2022 Katelynn Cadwallader
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations
from core import AMP_Console
from core import AMP

# Resources - https://www.dexerto.com/gaming/terraria-console-commands-explained-a-simple-controls-guide-1663852/
DisplayImageSources = ['steam:105600']


class AMPTerraria(AMP.AMPInstance):
    def __init__(self, instanceID: int = 0, serverdata: dict = {}, default_console: bool = False, Handler=None, TargetName: str | None = None):
        self.perms = []
        self.APIModule = 'Terraria'

        super().__init__(instanceID, serverdata, Handler=Handler, TargetName=TargetName)
        self.Console = AMPTerrariaConsole(AMPInstance=self)

        self.default_background_banner_path = 'resources/banners/Terraria_Banner.png'
        self.SenderFilterList.append('Server')

        self._apply_default_avatar('https://github.com/AriVenatus/GatekeeperV4/blob/main/resources/avatars/terraria_avatar.jpg?raw=true')

    def Chat_Message(self, message: str, author: str | None = None, author_prefix: str | None = None, server_prefix: str | None = None):
        """Sends a customized message via say through the console."""
        # Replace bracket characters so untrusted text can't close the current [c/...:...] tag
        # early or inject a new/malformed rich-text tag.
        if message != None:
            message = message.replace('[', '(').replace(']', ')')
        if author != None:
            author = author.replace('[', '(').replace(']', ')')
        if author_prefix != None:
            author_prefix = author_prefix.replace('[', '(').replace(']', ')')
        if server_prefix != None:
            server_prefix = server_prefix.replace('[', '(').replace(']', ')')

        self.Login()
        # Colors:
        # To write colors, you have to use the "color" variable. To write the command, use 'say [c/(insert color):text]' Ex: /say [c/ff0000:Hi!]
        # Colors must be entered as hex codes
        content = 'say [c/0000ff:[Discord][c/0000ff:]] '
        if server_prefix != None:
            content += f'[c/ffd700:({server_prefix})]'

        if author_prefix != None:
            content += f'[c/ffff00:({author_prefix})]'

        content += f'[c/ffffff:<{author}> {message}]'
        self.ConsoleMessage(content)

    def Broadcast_Message(self, message, prefix: str | None = None):
        """Used to Send a Broadcast Message to the Server"""
        self.Login()
        content = 'say '
        if prefix != None:
            content += f'<{prefix}> '

        content += f'{message}'
        self.ConsoleMessage(content)


class AMPTerrariaConsole(AMP_Console.AMPConsole):
    def __init__(self, AMPInstance=AMPTerraria):
        super().__init__(AMPInstance)
