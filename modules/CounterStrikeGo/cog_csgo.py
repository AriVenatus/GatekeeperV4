# Copyright (C) 2021-2022 Katelynn Cadwallader
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations
import discord
from discord import app_commands
from discord.ext import commands
import os
import logging

from core import utils
from core import AMP_Handler
from core import DB as DB

DisplayImageSources = ['steam:730']


class Csgo(commands.Cog):
    def __init__(self, client: commands.Bot):
        self._client = client
        self.name = os.path.basename(__file__)

        self.logger = logging.getLogger(__name__)  # Point all print/logging statments here!

        self.AMPHandler = AMP_Handler.getAMPHandler()
        self.AMP = self.AMPHandler.AMP  # Main AMP object
        self.AMPInstances = self.AMPHandler.AMP_Instances  # Main AMP Instance Dictionary

        # use DBHandler for all DB related needs.
        self.DBHandler = DB.getDBHandler()
        self.DB = self.DBHandler.DB  # Main Database object
        self.DBCOnfig = self.DB.DBConfig

        # utils.botUtils provide access to utility functions such as serverparse,role_parse,channel_parse,user_parse.
        self.uBot = utils.botUtils(client)
        # utils.discordBot provides access to utility functions such as sending/deleting messages, kicking/ban users.
        self.dBot = utils.discordBot(client)

        # Leave this commented out unless you need to create a sub-command.
        # self.uBot.sub_command_handler('user',self.info) #This is used to add a sub command(self,parent_command,sub_command)
        self.logger.info(f'**SUCCESS** Loading Module **{self.name.upper()}**')


async def setup(client):
    await client.add_cog(Csgo(client))
