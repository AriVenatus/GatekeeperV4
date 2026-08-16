# Copyright (C) 2021-2022 Katelynn Cadwallader
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations
from core import AMP
from core import AMP_Console


DisplayImageSources = ['steam:108600']


class AMPProjectzomboid(AMP.AMPInstance):
    def __init__(self, instanceID: int = 0, serverdata: dict = {}, default_console: bool = False, Handler=None, TargetName: str | None = None):
        self.perms = []
        self.APIModule = 'Project Zomboid'

        super().__init__(instanceID, serverdata, Handler=Handler, TargetName=TargetName)
        self.Console = AMPProjectzomboidConsole(AMPInstance=self)

        self.default_background_banner_path = 'resources/banners/Project_Zomboid_banner_1.jpg'

        if self.Avatar_url == None:
            self.DB_Server.Avatar_url = 'https://github.com/AriVenatus/GatekeeperV4/blob/main/resources/avatars/project_zomboid_avatar.png?raw=true'

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


class AMPProjectzomboidConsole(AMP_Console.AMPConsole):
    def __init__(self, AMPInstance=AMPProjectzomboid):
        super().__init__(AMPInstance)
