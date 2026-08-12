# Copyright (C) 2021-2022 Katelynn Cadwallader
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations
from core import AMP
from core import AMP_Console


DisplayImageSources = ['steam:251570']


class AMPSevendays(AMP.AMPInstance):
    def __init__(self, instanceID: int = 0, serverdata: dict = {}, default_console: bool = False, Handler=None, TargetName: str = None):
        self.perms = []
        self.APIModule = 'Seven Days To Die'

        super().__init__(instanceID, serverdata, Handler=Handler, TargetName=TargetName)
        self.Console = AMPSevendaysConsole(AMPInstance=self)

        self.default_background_banner_path = 'resources/banners/7Days_Banner_2.jpg'

        if self.Avatar_url == None:
            self.DB_Server.Avatar_url = 'https://github.com/AriVenatus/GatekeeperV4/blob/main/resources/avatars/7days_avatar.png?raw=true'

        self.SenderFilterList.append('Server')

    def Chat_Message(self, message: str, author: str = None, author_prefix: str = None, server_prefix: str = None):
        """Sends a customized message via say through the console."""
        self.Login()
        content = 'say "[Discord] '
        if server_prefix != None:
            content += f'({server_prefix}) '

        if author_prefix != None:
            content += f'({author_prefix}) '

        content += f'<{author}> {message}"'
        self.ConsoleMessage(content)

    def Broadcast_Message(self, message, prefix: str = None):
        """Used to Send a Broadcast Message to the Server"""
        self.Login()
        content = 'say "'
        if prefix != None:
            content += f'<{prefix}> '

        content += f'{message}"'
        self.ConsoleMessage(content)


class AMPSevendaysConsole(AMP_Console.AMPConsole):
    def __init__(self, AMPInstance=AMPSevendays):
        super().__init__(AMPInstance)
