# Copyright (C) 2021-2022 Katelynn Cadwallader
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations
from core import AMP_Console
from core import AMP

DisplayImageSources = ['steam:892970']


class AMPValheim(AMP.AMPInstance):
    def __init__(self, instanceID: int = 0, serverdata: dict = {}, default_console: bool = False, Handler=None, TargetName: str = None):
        self.perms = []
        self.APIModule = 'Valheim'

        super().__init__(instanceID, serverdata, Handler=Handler, TargetName=TargetName)
        self.Console = AMPValheimConsole(AMPInstance=self)

        self.default_background_banner_path = 'resources/banners/Valheim_Banner.png'

        if self.Avatar_url == None:
            self.DB_Server.Avatar_url = 'https://github.com/AriVenatus/GatekeeperV4/blob/main/resources/avatars/valheim_avatar.png?raw=true'


class AMPValheimConsole(AMP_Console.AMPConsole):
    def __init__(self, AMPInstance=AMPValheim):
        super().__init__(AMPInstance)
