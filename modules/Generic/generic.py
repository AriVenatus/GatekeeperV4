# Copyright (C) 2021-2022 Katelynn Cadwallader
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations
import os
import logging

import discord
from discord.ext import commands

from core import utils
from core import AMP_Handler
from core import DB as DB


class Generic(commands.Cog):
    def __init__(self, client):
        self._client = client
        self.name = os.path.basename(__file__)
        self.logger = logging.getLogger(__name__)  # Point all print/logging statments here!

        self.AMPHandler = AMP_Handler.getAMPHandler()
        self.AMP = self.AMPHandler.AMP  # Main AMP object
        self.AMPInstances = self.AMPHandler.AMP_Instances  # Main AMP Instance Dictionary

        self.DBHandler = DB.getDBHandler()
        self.DB = self.DBHandler.DB  # Main Database object
        self.DBConfig = self.DBHandler.DBConfig

        self.uBot = utils.botUtils(client)
        self.dBot = utils.discordBot(client)
        # self.uBot.sub_command_handler(self,'user',self.info)
        self.logger.info(f'**SUCCESS** Initializing Module **{self.name.capitalize()}**')


async def setup(client):
    await client.add_cog(Generic(client))
