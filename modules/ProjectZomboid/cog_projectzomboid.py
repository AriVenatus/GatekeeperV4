# Copyright (C) 2021-2022 Katelynn Cadwallader
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations
from discord.ext import commands
import os
import logging

from core import utils
from core import AMP_Handler
from core import DB

DisplayImageSources = ['steam:108600']


class Projectzomboid(commands.Cog):
    def __init__(self, client):
        self._client = client
        self.name = os.path.basename(__file__)
        self.logger = logging.getLogger(__name__)  # Point all print/logging statments here!

        self.AMPHandler = AMP_Handler.getAMPHandler()
        self.AMP = self.AMPHandler.AMP  # Main AMP object
        self.AMPInstances = self.AMPHandler.AMP_Instances  # Main AMP Instance Dictionary

        self.DBHandler = DB.getDBHandler()
        self.DB = self.DBHandler.DB  # Main Database object
        self.DBCOnfig = self.DB.DBConfig

        self.uBot = utils.botUtils(client)
        self.dBot = utils.discordBot(client)
        # self.uBot.sub_command_handler('user',self.info) #This is used to add a sub command(self,parent_command,sub_command)
        self.logger.info(f'**SUCCESS** Initializing Module **{self.name.capitalize()}**')


async def setup(client):
    await client.add_cog(Projectzomboid(client))
