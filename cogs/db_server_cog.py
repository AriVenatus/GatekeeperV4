# Copyright (C) 2021-2022 Katelynn Cadwallader
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations
import os
import logging
from typing import Union

import discord
from discord.ext import commands
from discord import app_commands

from core import utils
from core import utils_ui
from core import AMP_Handler
from core import DB
from core import i18n

# This is used to force cog order to prevent missing methods.
Dependencies = None


class DB_Server(commands.Cog):
    def __init__(self, client: discord.Client):
        self._client = client
        self.name = os.path.basename(__file__)
        self.logger = logging.getLogger()  # Point all print/logging statments here!

        self.AMPHandler = AMP_Handler.getAMPHandler()
        self.AMP = self.AMPHandler.AMP  # Main AMP object
        self.AMPInstances = self.AMPHandler.AMP_Instances  # Main AMP Instance Dictionary

        self.DBHandler = DB.getDBHandler()
        self.DB = self.DBHandler.DB  # Main Database object
        self.DBConfig = self.DBHandler.DBConfig

        self.uBot = utils.botUtils(client)
        self.uiBot = utils_ui
        self.dBot = utils.discordBot(client)
        self.logger.info(f'**SUCCESS** Initializing {self.name.title().replace("Db","DB")}')

    async def autocomplete_db_servers(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        """Autocomplete for Database Server Names for Change Instance IDs"""
        db_server_list = self.DB.GetAllServers()
        for key, value in self.DB.GetAllServers().items():
            if key in self.AMPInstances:
                db_server_list.pop(key)
        return [app_commands.Choice(name=f"{value} | ID: {key}", value=key)for key, value in db_server_list.items()][:25]

    @commands.hybrid_group(name='dbserver', description=i18n.t('commands.dbserver.description'))
    @utils.role_check()
    async def db_server(self, context: commands.Context):
        if context.invoked_subcommand is None:
            await context.send(i18n.t('common.invalid_command'), ephemeral=True, delete_after=30)

    @db_server.command(name='cleanup', description=i18n.t('commands.dbserver.cleanup.description'))
    @utils.role_check()
    async def db_server_cleanup(self, context: commands.Context):
        self.logger.command(f'{context.author.name} used Database Clean-Up in progress...')

        amp_instance_keys = self.AMPInstances.keys()
        db_server_list = self.DB.GetAllServers()
        found_server = False
        for key, value in db_server_list.items():
            db_server = self.DB.GetServer(InstanceID=key)
            if db_server != None and db_server.InstanceID not in amp_instance_keys:
                db_server.delServer()
                found_server = True
                await context.send(i18n.t('messages.db_server.cleanup.removing', server_name=db_server.InstanceName), ephemeral=True, delete_after=self._client.Message_Timeout)

        if not found_server:
            await context.send(i18n.t('messages.db_server.cleanup.none_found'), ephemeral=True, delete_after=self._client.Message_Timeout)

    @db_server.command(name='change_instance_id', description=i18n.t('commands.dbserver.change_instance_id.description'))
    @utils.role_check()
    @app_commands.autocomplete(from_server=autocomplete_db_servers)  # The DB Information we want to copy onto the Destination Server
    @app_commands.autocomplete(to_server=utils.autocomplete_servers)
    @app_commands.describe(from_server=i18n.t('commands.dbserver.change_instance_id.params.from_server.description'))
    @app_commands.describe(to_server=i18n.t('commands.dbserver.change_instance_id.params.to_server.description'))
    async def db_server_changeinstanceid(self, context: Union[commands.Context, discord.Interaction], from_server: str, to_server: str):
        self.logger.command(f'{context.author.name} used Database Instance swap...')

        from_db_server = self.DB.GetServer(InstanceID=from_server)

        to_db_server = self.DB.GetServer(to_server)

        content = i18n.t('messages.db_server.change_instance_id.confirm', from_name=from_db_server.InstanceName, to_name=to_db_server.InstanceName)
        message = await context.send(content, delete_after=self._client.Message_Timeout, ephemeral=True)

        _view = self.uiBot.DB_Instance_ID_Swap(discord_message=message, timeout=self._client.Message_Timeout, from_db_server=from_db_server, to_db_server=to_db_server)
        await message.edit(view=_view)


async def setup(client):
    await client.add_cog(DB_Server(client))
