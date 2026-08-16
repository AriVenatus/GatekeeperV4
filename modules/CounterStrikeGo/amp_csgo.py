# Copyright (C) 2021-2022 Katelynn Cadwallader
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations
from core import AMP
from core import AMP_Console


DisplayImageSources = ['steam:730']


class AMPCsgo(AMP.AMPInstance):
    def __init__(self, instanceID: int = 0, serverdata: dict = {}, default_console: bool = False, Handler=None, TargetName: str | None = None):
        self.perms = []
        self.APIModule = 'Counterstrike_GO'

        super().__init__(instanceID, serverdata, Handler=Handler, TargetName=TargetName)
        self.Console = AMPCsgoConsole(AMPInstance=self)

        self.default_background_banner_path = 'resources/banners/CS_Go_Banner_3.png'

        if self.Avatar_url == None:
            self.DB_Server.Avatar_url = 'https://github.com/AriVenatus/GatekeeperV4/blob/main/resources/avatars/csgo_avatar.png?raw=true'


class AMPCsgoConsole(AMP_Console.AMPConsole):
    def __init__(self, AMPInstance=AMPCsgo):
        super().__init__(AMPInstance)
