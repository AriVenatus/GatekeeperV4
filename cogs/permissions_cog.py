# Copyright (C) 2021-2022 Katelynn Cadwallader
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations
import discord
from discord import app_commands
from discord.ext import commands

import os
import logging
from typing import Union

from core import utils
from core import AMP_Handler
from core import DB as DB
from core import i18n

# This is used to force cog order to prevent missing methods.
Dependencies = ["db_user_cog.py"]


class Permissions(commands.Cog):
    def __init__(self, client: discord.Client):
        self._client = client
        self.name = os.path.basename(__file__)
        self.logger = logging.getLogger()  # Point all print/logging statments here!

        # use DBHandler for all DB related needs.
        self.DBHandler = DB.getDBHandler()
        self.DB = self.DBHandler.DB  # Main Database object
        self.DBCOnfig = self.DB.DBConfig

        self.uBot = utils.botUtils(client)
        self.bPerms = utils.get_botPerms()

        # Leave this commented out unless you need to create a sub-command.
        self.uBot.sub_command_handler('user', self.user_role)  # This is used to add a sub command(self,parent_command,sub_command)
        self.logger.info(f'**SUCCESS** Loading Module **{self.name.title()}**')

    async def autocomplete_permission_roles(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        """This is for roles inside of the bot_perms file. Returns a list of all the roles.."""
        bPerms = utils.get_botPerms()
        choice_list = bPerms.get_roles()
        return [app_commands.Choice(name=choice, value=choice) for choice in choice_list if current.lower() in choice.lower()][:25]

    @commands.hybrid_command(name='role', description=i18n.t('commands.user.role.description'))
    @utils.role_check()
    @app_commands.autocomplete(role=autocomplete_permission_roles)
    async def user_role(self, context: commands.Context, user: Union[discord.User, discord.Member], role: str):
        self.logger.command(f'{context.author.name} used User Role Function')

        if role not in self.bPerms.get_roles():
            await context.send(i18n.t('messages.permissions.user_role.invalid_role', user_name=user.name, role=role), ephemeral=True, delete_after=self._client.Message_Timeout)
            return

        db_user = self.DB.GetUser(user.id)
        if db_user != None:
            db_user.Role = role
            await context.send(i18n.t('messages.permissions.user_role.success', user_name=user.name, role=role), ephemeral=True, delete_after=self._client.Message_Timeout)
        else:
            await context.send(i18n.t('messages.permissions.user_role.not_found', user_name=user.name), ephemeral=True, delete_after=self._client.Message_Timeout)


async def setup(client):
    await client.add_cog(Permissions(client))
