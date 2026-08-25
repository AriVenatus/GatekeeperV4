# Copyright (C) 2021-2022 Katelynn Cadwallader
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations
import discord
from discord.ext import commands
import os
import logging

from core import utils
from core import AMP_Handler
from core import DB

DisplayImageSources = ['steam:376030']


class Ark(commands.Cog):
    def __init__(self, client):
        self._client = client
        self.name = os.path.basename(__file__)
        self.logger = logging.getLogger(__name__)  # Point all print/logging statments here!

        self.AMPHandler = AMP_Handler.getAMPHandler()
        self.AMP = self.AMPHandler.AMP  # Main AMP object
        self.AMPInstances = self.AMPHandler.AMP_Instances

        self.DBHandler = DB.getDBHandler()
        self.DB = self.DBHandler.DB  # Main Database object
        self.DBConfig = self.DBHandler.DBConfig

        self.uBot = utils.botUtils(client)
        # self.uBot.sub_command_handler(self,'user',self.info)
        self.logger.info(f'**SUCCESS** Initializing Module **{self.name.capitalize()}**')

    @commands.Cog.listener('on_member_remove')
    async def on_member_remove(self, member: discord.Member):
        """Called when a member is kicked or leaves the Server/Guild. Returns a <discord.Member> object."""
        self.logger.dev(f'Member Leave {self.name}: {member.name} {member}')

        db_user = self.DB.GetUser(str(member.id))
        if db_user != None and db_user.SteamID != None:
            for server in list(self.AMPInstances):
                # Use `APIModule` (set by AMPArk itself) rather than `Module` (from AMP's own API
                # response) -- see the identical precedent/reasoning in whitelist_sync_cog.py's
                # `_cleanup_steam_whitelist`, AMP's `Module` value for ARK instances is unverified.
                if getattr(self.AMPInstances[server], 'APIModule', None) == 'Ark':
                    self.AMPInstances[server].removeWhitelist(in_gamename=db_user.SteamID)

        return member


async def setup(client):
    await client.add_cog(Ark(client))
