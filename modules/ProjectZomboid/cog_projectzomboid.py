# Copyright (C) 2021-2022 Katelynn Cadwallader
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations
from discord.ext import commands
import os
import logging

from core import utils
from core import AMP_Handler
from core import DB
from core import i18n

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
        # self.uBot.sub_command_handler('user',self.info) #This is used to add a sub command(self,parent_command,sub_command)
        self.logger.info(f'**SUCCESS** Initializing Module **{self.name.capitalize()}**')

    @commands.hybrid_group(name='pz', description=i18n.t('commands.pz.description'))
    async def pz_group(self, context: commands.Context):
        if context.invoked_subcommand is None:
            await context.send(i18n.t('common.invalid_command'), ephemeral=True, delete_after=self._client.Message_Timeout)

    @pz_group.command(name='credentials', description=i18n.t('commands.pz.credentials.description'))
    async def pz_credentials(self, context: commands.Context):
        """Reveals the caller's Project Zomboid login (bot-generated on Whitelist grant, via
        `AMPProjectzomboid.addWhitelist()`). Ephemeral rather than a DM -- an ephemeral reply
        only needs the caller and bot to share a server, unlike `member.send()`, which silently
        fails for anyone with DMs disabled and would otherwise strand them with no way to
        retrieve a password that was never persisted anywhere else."""
        self.logger.command(f'{context.author.name} used PZ Credentials')

        db_user = self.DB.GetUser(context.author.id)
        if db_user is None or db_user.PZ_Username is None:
            return await context.send(i18n.t('messages.pz.credentials.none'), ephemeral=True, delete_after=self._client.Message_Timeout)

        await context.send(i18n.t('messages.pz.credentials.result', username=db_user.PZ_Username, password=db_user.PZ_Password), ephemeral=True)


async def setup(client):
    await client.add_cog(Projectzomboid(client))
