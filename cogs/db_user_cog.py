# Copyright (C) 2021-2022 Katelynn Cadwallader
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations
import os
import logging
from typing import Union
import sqlite3

import discord
from discord import app_commands
from discord.ext import commands

from core import utils
from core import utils_permissions
from core import utils_embeds
from core import AMP_Handler
from core import DB
from core import i18n

# This is used to force cog order to prevent missing methods.
Dependencies = None


class DB_User(commands.Cog):
    def __init__(self, client: discord.Client):
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
        self.eBot = utils_embeds.botEmbeds(client)

        self.logger.info(f'**SUCCESS** Initializing {self.name.title().replace("Db","DB")}')

    @commands.Cog.listener('on_member_update')
    async def on_member_update(self, user_before: discord.User, user_after: discord.User):
        # Lets see if the name is different from before.
        if user_before.name != user_after.name:
            # Lets look up the previous ID to gaurentee a proper search, could use the newer user ID; both in theory should be the same.
            db_user = self.DB.GetUser(user_before.id)
            # If we found the DB User
            if db_user != None:
                db_user.DiscordName = user_after.name
            else:  # Lets Add them with the info we have!
                self.DB.AddUser(DiscordID=user_before.id, DiscordName=user_after.name)

            self.logger.dev(f'User Update {self.name}: {user_before.name} into {user_after.name}')
            return user_after

    @commands.Cog.listener('on_member_remove')
    async def on_member_remove(self, member: discord.Member):
        self.logger.dev(f'Member has left the server {member.name}')
        return member

    @utils_permissions.role_check()
    @commands.hybrid_group(name='user', description=i18n.t('commands.user.description'))
    async def user(self, context: commands.Context):
        if context.invoked_subcommand is None:
            await context.send(i18n.t('common.try_again'), ephemeral=True, delete_after=self._client.Message_Timeout)

    @user.group(name='info', description=i18n.t('commands.user.info.description'))
    @utils_permissions.role_check()
    async def user_info(self, context: commands.Context):
        if context.invoked_subcommand is None:
            await context.send(i18n.t('common.try_again'), ephemeral=True, delete_after=self._client.Message_Timeout)

    @user_info.command(name='discord', description=i18n.t('commands.user.info.discord.description'))
    @utils_permissions.role_check()
    @app_commands.describe(user=i18n.t('commands.user.info.discord.params.user.description'))
    async def user_info_discord(self, context: commands.Context, user: Union[discord.Member, discord.User]):
        self.logger.command(f'{context.author.name} used User Information (Discord)')
        await self._send_user_info(context, user.id, user)

    @user_info.command(name='minecraft', description=i18n.t('commands.user.info.minecraft.description'))
    @utils_permissions.role_check()
    @app_commands.describe(identifier=i18n.t('commands.user.info.minecraft.params.identifier.description'))
    async def user_info_minecraft(self, context: commands.Context, identifier: str):
        self.logger.command(f'{context.author.name} used User Information (Minecraft)')
        await self._send_user_info(context, identifier)

    @user_info.command(name='steam', description=i18n.t('commands.user.info.steam.description'))
    @utils_permissions.role_check()
    @app_commands.describe(identifier=i18n.t('commands.user.info.steam.params.identifier.description'))
    async def user_info_steam(self, context: commands.Context, identifier: str):
        self.logger.command(f'{context.author.name} used User Information (Steam)')
        await self._send_user_info(context, identifier)

    async def _send_user_info(self, context: commands.Context, search_value, discord_user: Union[discord.Member, discord.User, None] = None):
        db_user = self.DB.GetUser(search_value)
        if db_user == None:
            return await context.send(i18n.t('messages.db_user.user_info.not_found', search_value=search_value), ephemeral=True, delete_after=self._client.Message_Timeout)

        if discord_user == None:
            discord_user = self._client.get_user(int(db_user.DiscordID))
            if discord_user == None:
                try:
                    discord_user = await self._client.fetch_user(int(db_user.DiscordID))
                except discord.NotFound:
                    discord_user = None

        await context.send(embed=self.eBot.user_info_embed(db_user, discord_user), ephemeral=True, delete_after=self._client.Message_Timeout)

    @user.command(name='add', description=i18n.t('commands.user.add.description'))
    @utils_permissions.role_check()
    async def user_add(self, context: commands.Context, user: Union[discord.Member, discord.User], mc_ign: str | None = None, mc_uuid: str | None = None, steamid: str | None = None):
        self.logger.command(f'{context.author.name} used User Add Function')

        if mc_ign != None:
            mc_uuid = self.uBot.name_to_uuid_MC(mc_ign)

        db_user = self.DB.GetUser(user.id)
        if db_user == None:
            self.DB.AddUser(DiscordID=user.id, DiscordName=user.name, MC_IngameName=mc_ign, MC_UUID=mc_uuid, SteamID=steamid)
            await context.send(i18n.t('messages.db_user.user_add.success', user_name=user.name), ephemeral=True, delete_after=self._client.Message_Timeout)
        else:
            await context.send(i18n.t('messages.db_user.user_add.already_exists', user_name=user.name), ephemeral=True, delete_after=self._client.Message_Timeout)

    @user.command(name='update', description=i18n.t('commands.user.update.description'))
    @utils_permissions.role_check()
    async def user_update(self, context: commands.Context, user: Union[discord.Member, discord.User], mc_ign: str | None = None, steamid: str | None = None):
        self.logger.command(f'{context.author.name} used User Update Function')

        db_user = None
        updated_vals = []
        params = locals()
        db_params = {'user': 'DiscordName',
                     'mc_ign': 'MC_IngameName',
                     'mc_uuid': 'MC_UUID',
                     'steamid': 'SteamID'
                     }

        params['mc_uuid'] = None
        if mc_ign != None:
            if mc_ign.lower() == 'none':
                params['mc_uuid'] = 'none'
            else:
                mc_uuid = self.uBot.name_to_uuid_MC(mc_ign)
                params['mc_uuid'] = mc_uuid

        db_user = self.DB.GetUser(user.id)
        if db_user != None:
            for entry in db_params:
                if params[entry] == None:
                    continue
                elif entry == 'user':
                    continue
                elif params[entry].lower() == 'none':
                    setattr(db_user, db_params[entry], None)
                    updated_vals.append(i18n.t('messages.db_user.user_update.field_cleared', field=db_params[entry]))

                else:
                    try:
                        setattr(db_user, db_params[entry], params[entry])
                        updated_vals.append(i18n.t('messages.db_user.user_update.field_set', field=db_params[entry], value=params[entry]))

                    except sqlite3.IntegrityError as e:
                        if "UNIQUE constraint failed" in e.args[0]:
                            self.logger.error(f'SQLITE Exception {e}')
                            await context.send(i18n.t('messages.db_user.user_update.unique_violation', field=db_params[entry], user_name=db_user.DiscordName), ephemeral=True, delete_after=self._client.Message_Timeout)

            updated_vals = "\n".join(updated_vals)
            await context.send(i18n.t('messages.db_user.user_update.success', user_name=db_user.DiscordName, updated_fields=updated_vals), ephemeral=True, delete_after=self._client.Message_Timeout)
        else:
            await context.send(i18n.t('messages.db_user.user_update.not_found'), ephemeral=True, delete_after=self._client.Message_Timeout)


async def setup(client):
    await client.add_cog(DB_User(client))
