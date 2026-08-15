# Copyright (C) 2021-2022 Katelynn Cadwallader
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

import logging
import os
import random
import sqlite3
import traceback
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Optional, Union

import discord
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import commands, tasks

from core import AMP_Handler
from core import DB
from core import utils
from core import utils_embeds
from core import utils_ui
from core import i18n
from core.discordBot import Gatekeeper

if TYPE_CHECKING:
    from core.discordBot import Gatekeeper


# This is used to force cog order to prevent missing methods.
# MUST USE ENTIRE FILENAME!
Dependencies = ["amp_server_cog.py"]

Whitelist_settings_choices = [app_commands.Choice(name='True', value=True),
                              app_commands.Choice(name='False', value=False)
                              ]


class Whitelist(commands.Cog):
    def __init__(self, client: Gatekeeper):
        self._client: Gatekeeper = client
        self.name = os.path.basename(__file__)
        self.logger = logging.getLogger()

        self.AMPHandler = AMP_Handler.getAMPHandler()

        self.DBHandler = DB.getDBHandler()
        self.DB = self.DBHandler.DB  # Main Database object
        self.DBConfig = self.DBHandler.DBConfig

        self.uBot = utils.botUtils(client)
        self.uiBot = utils_ui
        self.dBot = utils.discordBot(client)
        self.eBot = utils_embeds.botEmbeds(client)

        self.Whitelist_Request_Channel = None

        self.failed_whitelist = []
        self._client.Whitelist_wait_list = {}  # [message.id] : {'ampserver' : amp_server, 'context' : context, 'dbuser' : db_user}

        self.uBot.sub_command_handler('server', self.server_whitelist)
        self.uBot.sub_group_command_handler('server settings', self.server_settings_whitelist_set)
        self.uBot.sub_group_command_handler('server settings', self.server_settings_whitelist_auto)
        self.uBot.sub_group_command_handler('server settings', self.server_settings_whitelist_wait_time)
        self.uBot.sub_command_handler('bot', self.db_bot_whitelist)
        self.uBot.sub_command_handler('bot', self.db_bot_whitelist_reply)

        # Because of the similar named hybrid group; we get a duplicate command under `/whitelist`
        # I am not overly found of doing it this way; but it currently works.
        self.whitelist_command_cleanup.start()

        self.logger.info(f'**SUCCESS** Initializing {self.name.title()}')

    def __getattribute__(self, __name: str):
        if __name == 'Whitelist__Request_Channel':
            db_get = self.DBConfig.GetSetting('Whitelist_Request_Channel')
            if db_get != None:
                db_get = int(db_get)
            return db_get
        return super().__getattribute__(__name)

    @tasks.loop(count=1)
    async def whitelist_command_cleanup(self):
        await self._client.wait_until_ready()
        self.uBot._remove_commands("whitelist", "add")
        self.uBot._remove_commands("whitelist", "remove")
        self.uBot._remove_commands('bot whitelist', 'add')
        self.uBot._remove_commands('bot whitelist', 'remove')
        self.whitelist_command_cleanup.stop()

    # Discord Auto Completes ---------------------------------------------------------------------------------------------------------------
    async def autocomplete_whitelist_replies(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        """Autocomplete for Whitelist Replies"""
        choice_list = self.DB.GetAllWhitelistReplies()
        return [app_commands.Choice(name=self.whitelist_reply_formatter(choice), value=self.whitelist_reply_formatter(choice)) for choice in choice_list if current.lower() in choice.lower()]

    def whitelist_reply_formatter(self, parameter: str):
        if len(parameter) > 100:
            return parameter[0:96] + '...'
        return parameter

    # Discord Listener Events -------------------------------------------------------------------------------------------------------------

    @commands.Cog.listener('on_member_remove')
    async def on_member_remove(self, member: discord.Member):
        """Called when a member is kicked or leaves the Server/Guild. Returns a <discord.Member> object."""
        self.logger.dev(f'Member Leave Event {self.name}: {member.name} {member}')

        for key, value in list(self._client.Whitelist_wait_list.items()):
            if member.id == value['context'].message.author.id:
                self._client.Whitelist_wait_list.pop(key)
                self.logger.info(f'Removed {member.name} from Whitelist Wait List.')

        db_user: None | DB.DBUser = self.DB.GetUser(value=str(member.id))
        if db_user != None and db_user.MC_IngameName != None:
            for instance_id, amp_instance in list(self.AMPHandler.AMP_Instances.items()):
                if amp_instance.Module == 'Minecraft':
                    self.logger.info(f"Removing {db_user.MC_IngameName} from {amp_instance.FriendlyName} Whitelist.")
                    amp_instance.removeWhitelist(in_gamename=db_user.MC_IngameName)

    # Server Whitelist Commands ------------------------------------------------------------

    @commands.hybrid_command(name='whitelist', description=i18n.t('commands.server.settings.whitelist.description'))
    @utils.role_check()
    @app_commands.autocomplete(server=utils.autocomplete_servers)
    @app_commands.choices(flag=[
        Choice(name=i18n.t('common.bool.false'), value=0),
        Choice(name=i18n.t('common.bool.true'), value=1),
        Choice(name=i18n.t('commands.server.settings.whitelist.params.flag.choices.2'), value=2),
    ])
    async def server_settings_whitelist_set(self, context: commands.Context, server: str, flag: Choice[int]):
        self.logger.command(f'{context.author.name} used {context.command.name}')

        amp_server = await self.uBot._serverCheck(context, server, False)
        if amp_server:
            if flag.value in [0, 1]:
                # Set our Whitelist Flag
                self.DB.GetServer(InstanceID=amp_server.InstanceID).Whitelist = flag.value
                # Unhide our Whitelist Open/Closed on the Server Banners
                self.DB.GetServer(InstanceID=amp_server.InstanceID).Whitelist_disabled = False
                amp_server._setDBattr()  # This will update the AMPInstance Attributes

            elif flag.value == 2:
                # Hides the Whitelist Open/Closed on the Server Banners
                self.DB.GetServer(InstanceID=amp_server.InstanceID).Whitelist_disabled = True
                amp_server._setDBattr()  # This will update the AMPInstance Attributes

            server_name = amp_server.FriendlyName if amp_server.FriendlyName != None else amp_server.InstanceName
            await context.send(i18n.t('messages.whitelist.server_set.result', server_name=server_name, flag_name=flag.name), ephemeral=True, delete_after=self._client.Message_Timeout)

    @commands.hybrid_command(name='whitelist_auto', description=i18n.t('commands.server.settings.whitelist_auto.description'))
    @utils.role_check()
    @app_commands.autocomplete(server=utils.autocomplete_servers)
    @app_commands.choices(flag=[Choice(name=i18n.t('common.bool.true'), value=1), Choice(name=i18n.t('common.bool.false'), value=0)])
    async def server_settings_whitelist_auto(self, context: commands.Context, server: str, flag: Choice[int]):
        self.logger.command(f'{context.author.name} used Server Whitelist Auto...')

        amp_server = await self.uBot._serverCheck(context, server, False)
        if amp_server:
            # lets validate our Whitelist_request_channel still exists.
            db_setting = self.DBConfig.GetSetting('Whitelist_request_channel')
            if db_setting != None and context.guild.get_channel(db_setting) == None:
                return await context.send(i18n.t('messages.whitelist.auto.invalid_channel'), ephemeral=True, delete_after=self._client.Message_Timeout)

            server_name = amp_server.FriendlyName if amp_server.FriendlyName != None else amp_server.InstanceName
            self.DB.GetServer(InstanceID=amp_server.InstanceID).Auto_Whitelist = flag.value
            amp_server._setDBattr()

            if flag.value == 1:
                return await context.send(i18n.t('messages.whitelist.auto.enabled', server_name=server_name), ephemeral=True, delete_after=self._client.Message_Timeout)
            else:
                return await context.send(i18n.t('messages.whitelist.auto.disabled', server_name=server_name), ephemeral=True, delete_after=self._client.Message_Timeout)

    @commands.hybrid_command(name='whitelist_wait_time', description=i18n.t('commands.server.settings.whitelist_wait_time.description'))
    @utils.role_check()
    @app_commands.autocomplete(server=utils.autocomplete_servers)
    @app_commands.describe(time=i18n.t('commands.server.settings.whitelist_wait_time.params.time.description'))
    async def server_settings_whitelist_wait_time(self, context: commands.Context, server: str, time: app_commands.Range[int, 0, 60] = 5):
        self.logger.command(f'{context.author.name} used Server Whitelist Wait Time...')

        amp_server = await self.uBot._serverCheck(context, server, False)
        if amp_server:
            server_name = amp_server.FriendlyName if amp_server.FriendlyName != None else amp_server.InstanceName
            self.DB.GetServer(InstanceID=amp_server.InstanceID).Whitelist_Wait_Time = time
            amp_server._setDBattr()

            interval_str = i18n.t_plural('common.minutes', count=time)
            await context.send(i18n.t('messages.whitelist.wait_time.success', server_name=server_name, interval=interval_str), ephemeral=True, delete_after=self._client.Message_Timeout)

    @commands.hybrid_group(name='whitelist', description=i18n.t('commands.server.whitelist.description'))
    @utils.role_check()
    async def server_whitelist(self, context: commands.Context):
        if context.invoked_subcommand is None:
            await context.send(i18n.t('common.invalid_command'), ephemeral=True, delete_after=self._client.Message_Timeout)

    @server_whitelist.command(name='add', description=i18n.t('commands.server.whitelist.add.description'))
    @utils.role_check()
    @app_commands.autocomplete(server=utils.autocomplete_servers)
    async def amp_server_whitelist_add(self, context: commands.Context, server, name):
        self.logger.command(f'{context.author.name} used AMP Server Whitelist Add...')

        amp_server = await self.uBot._serverCheck(context, server)
        if amp_server:
            whitelist = amp_server.check_Whitelist(in_gamename=name)
            server_name = amp_server.FriendlyName if amp_server.FriendlyName != None else amp_server.InstanceName
            if whitelist:
                canonical_name = amp_server.resolve_canonical_IGN(name)
                amp_server.addWhitelist(in_gamename=canonical_name)
                await context.send(i18n.t('messages.whitelist.add.success', server_name=server_name, name=canonical_name), ephemeral=True, delete_after=self._client.Message_Timeout)
            if whitelist == False:
                await context.send(i18n.t('messages.whitelist.uuid_not_found', name=name), ephemeral=True, delete_after=self._client.Message_Timeout)
            if whitelist == None:
                await context.send(i18n.t('messages.whitelist.add.already', name=name), ephemeral=True, delete_after=self._client.Message_Timeout)

    @server_whitelist.command(name='remove', description=i18n.t('commands.server.whitelist.remove.description'))
    @utils.role_check()
    @app_commands.autocomplete(server=utils.autocomplete_servers)
    async def amp_server_whitelist_remove(self, context: commands.Context, server, name):
        self.logger.command(f'{context.author.name} used AMP Server Whitelist Remove...')

        amp_server = await self.uBot._serverCheck(context, server)
        if amp_server:
            whitelist = amp_server.check_Whitelist(in_gamename=name)
            server_name = amp_server.FriendlyName if amp_server.FriendlyName != None else amp_server.InstanceName
            if whitelist:
                await context.send(i18n.t('messages.whitelist.remove.not_whitelisted', name=name), ephemeral=True, delete_after=self._client.Message_Timeout)
            if whitelist == False:
                await context.send(i18n.t('messages.whitelist.uuid_not_found', name=name), ephemeral=True, delete_after=self._client.Message_Timeout)
            if whitelist == None:
                canonical_name = amp_server.resolve_canonical_IGN(name)
                amp_server.removeWhitelist(in_gamename=canonical_name)
                await context.send(i18n.t('messages.whitelist.remove.success', server_name=server_name, name=canonical_name), ephemeral=True, delete_after=self._client.Message_Timeout)

    # All DBConfig Whitelist Specific function settings --------------------------------------------------------------
    @commands.hybrid_group(name='whitelist_reply', description=i18n.t('commands.bot.whitelist_reply.description'))
    @utils.role_check()
    async def db_bot_whitelist_reply(self, context: commands.Context):
        if context.invoked_subcommand is None:
            await context.send(i18n.t('common.invalid_command'), ephemeral=True, delete_after=self._client.Message_Timeout)

    @db_bot_whitelist_reply.command(name='add', description=i18n.t('commands.bot.whitelist_reply.add.description'))
    @utils.role_check()
    async def db_bot_whitelist_reply_add(self, context: commands.Context, message: str):
        self.logger.command(f'{context.author.name} used Database Bot Whitelist Reply Add...')

        self.DB.AddWhitelistReply(message)
        await context.send(i18n.t('messages.whitelist_reply.add.success'), ephemeral=True, delete_after=self._client.Message_Timeout)
        message = self.uBot.whitelist_reply_handler(message, context)
        await context.send(f'{message}', ephemeral=True, delete_after=self._client.Message_Timeout)

    @db_bot_whitelist_reply.command(name='remove', description=i18n.t('commands.bot.whitelist_reply.remove.description'))
    @utils.role_check()
    @app_commands.autocomplete(message=autocomplete_whitelist_replies)
    async def db_bot_whitelist_reply_remove(self, context: commands.Context, message: str):
        self.logger.command(f'{context.author.name} used Database Bot Whitelist Reply Remove...')
        reply_list = self.DB.GetAllWhitelistReplies()
        for reply in reply_list:
            if message in reply:
                self.DB.DeleteWhitelistReply(reply)
                return await context.send(i18n.t('messages.whitelist_reply.remove.success'), ephemeral=True, delete_after=self._client.Message_Timeout)
            else:
                continue
        return await context.send(i18n.t('messages.whitelist_reply.remove.not_found'), ephemeral=True, delete_after=self._client.Message_Timeout)

    @db_bot_whitelist_reply.command(name='list', description=i18n.t('commands.bot.whitelist_reply.list.description'))
    @utils.role_check()
    async def db_bot_whitelist_reply_list(self, context: commands.Context):
        self.logger.command(f'{context.author.name} used Database Bot Whitelist Reply List...')

        replies = self.DB.GetAllWhitelistReplies()
        await context.send(i18n.t('messages.whitelist_reply.list.header'), ephemeral=True, delete_after=self._client.Message_Timeout)
        for reply in replies:
            await context.send(f'{reply}', ephemeral=True, delete_after=self._client.Message_Timeout)

    @commands.hybrid_group(name='whitelist', description=i18n.t('commands.bot.whitelist.description'))
    @utils.role_check()
    async def db_bot_whitelist(self, context: commands.Context):
        if context.invoked_subcommand is None:
            await context.send(i18n.t('common.invalid_command'), ephemeral=True, delete_after=self._client.Message_Timeout)

    @db_bot_whitelist.command(name='request_channel', description=i18n.t('commands.bot.whitelist.request_channel.description'))
    @utils.role_check()
    async def db_bot_whitelist_request_channel_set(self, context: commands.Context, channel: discord.abc.GuildChannel):
        self.logger.command(f'{context.author.name} used Bot Whitelist Channel Set...')

        self.DBConfig.SetSetting('Whitelist_request_channel', channel.id)
        await context.send(i18n.t('messages.whitelist.request_channel.success', channel_name=channel.name), ephemeral=True, delete_after=self._client.Message_Timeout)

    @commands.hybrid_command(name='whitelist_request', description=i18n.t('commands.whitelist_request.description'))
    @app_commands.autocomplete(server=utils.autocomplete_servers_public)
    async def whitelist_request(self, context: commands.Context, server: str, ign: str = None):
        self.logger.command(f'{context.author.name} used Bot Whitelist Request...')
        amp_server = await self.uBot._serverCheck(context, server)

        if amp_server:
            # if this succeeds, then we can check if the user is whitelisted since we have updated the DB
            message = await context.send(i18n.t('messages.whitelist_request.handling'), ephemeral=True)  # delete_after= self._client.Message_Timeout)
            temp_Whitelist_wait_list = self._client.Whitelist_wait_list
            for key, value in temp_Whitelist_wait_list.items():
                if value['context'].author.id == context.author.id and value['ampserver'].InstanceID == amp_server.InstanceID:
                    server_name = amp_server.InstanceName if amp_server.FriendlyName == None else amp_server.FriendlyName
                    await context.send(i18n.t('messages.whitelist_request.already_pending', server_name=server_name))

            await self.whitelist_request_handler(context=context, message=message, discord_user=context.author, server=amp_server, ign=ign)

    async def whitelist_request_handler(self, context: commands.Context, message: discord.Message, discord_user: discord.Member, server: AMP_Handler.AMP.AMPInstance, ign: str = None):
        """Whitelist request handler checks for a DB User, checks for their IGN, checks if they are Whitelisted and any other required checks to whitelist a user. """
        self.logger.command(f'Whitelist Request: ign: {ign} servers: {server.FriendlyName} user: {discord_user.name}')

        if self._client.get_channel(self.DBConfig.GetSetting('Whitelist_Request_Channel')) == None:
            return await message.edit(content=i18n.t('messages.whitelist_request.no_channel_configured', guild_name=context.guild.name))

        server_name = f"{server.FriendlyName if server.FriendlyName != None else server.InstanceName}"
        db_user = self.DB.GetUser(discord_user.id)

        if db_user == None:
            db_user = self.DB.AddUser(DiscordID=discord_user.id, DiscordName=discord_user.name)
            self.logger.info(f'Added new user to the DB: {discord_user.name}')

        # Its possible that the IGN already exists in the DB; this is to prevent people from requesting whitelist for other people/etc..
        # check_whitelist can fail with a UNIQUE constraint exception from the SQLite DB.
        try:
            exists = server.check_Whitelist(db_user, ign)
        except sqlite3.IntegrityError as e:
            # We check the first entry of the tuple.
            if "UNIQUE constraint failed" in e.args[0]:
                duplicate_ign_db_user = self.DB.GetUser(ign)
                return await message.edit(content=i18n.t('messages.whitelist_request.duplicate_ign', ign=ign, mention=context.guild.get_member(duplicate_ign_db_user.DiscordID).mention))
            else:  # Any other errors need to be presented
                return await message.edit(content=i18n.t('messages.whitelist_request.sqlite_error', traceback=traceback.format_exc()))

        if exists == False:
            reason = i18n.t('messages.whitelist_request.invalid_ign_reason', ign=ign) if ign != None else i18n.t('messages.whitelist_request.need_ign_reason')
            return await message.edit(content=i18n.t('messages.whitelist_request.cannot_handle', reason=reason))

        elif exists == None:
            return await message.edit(content=i18n.t('messages.whitelist_request.already_whitelisted', server_name=server_name))

        db_server = self.DB.GetServer(server.InstanceID)
        if db_server.DisplayName != None:
            server_name = db_server.DisplayName

        if db_server.Whitelist == False:
            return await message.edit(content=i18n.t('messages.whitelist_request.whitelist_closed', server_name=server_name))

        if db_server.Donator == True:
            donator_role_ids = db_server.GetDonatorRoles()
            if not len(donator_role_ids):
                return await message.edit(content=i18n.t('messages.whitelist_request.no_donator_role_configured'))

            author_role_ids = {role.id for role in discord_user.roles}
            if author_role_ids.isdisjoint(donator_role_ids):
                return await message.edit(content=i18n.t('messages.whitelist_request.donator_only', server_name=server_name))

        wait_time_value = db_server.Whitelist_Wait_Time
        self._client.Whitelist_wait_list[context.message.id] = {'ampserver': server, 'context': context, 'dbuser': db_user}

        format_1 = f'Current wait time is {wait_time_value} {"minutes" if wait_time_value > 1 else "minute"}'
        self.logger.info(f'Added {context.author} to Whitelist Wait List. {"Auto-Whitelist is Disabled, waiting for Staff Approval Only" if not db_server.Auto_Whitelist else format_1}')
        self.logger.dev(f'MessageID: {context.message.id}')

        # If Auto-Whitelist is disabled; means we are waiting for STAFF Approval ONLY!
        if not db_server.Auto_Whitelist:
            wait_time_value = None
            await message.edit(content=i18n.t('messages.whitelist_request.awaiting_approval'))

        # If Auto-whitelist is enabled
        elif db_server.Auto_Whitelist:
            # and the wait time is instant.
            if wait_time_value == 0:
                # Remove them from the waitlist
                self._client.Whitelist_wait_list.pop(context.message.id)
                server.addWhitelist(db_user=db_user)

                # Lets get all the custom Whitelist Replies in the DB and randomly pick one.
                if len(self.DB.GetAllWhitelistReplies()) >= 1:
                    whitelist_reply = random.choice(self.DB.GetAllWhitelistReplies())
                    await message.edit(content=self.uBot.whitelist_reply_handler(whitelist_reply, context, server))
                else:
                    await message.edit(content=i18n.t('messages.whitelist_request.success_no_reply', author_name=context.author.name, server_name=db_server.FriendlyName))

                if db_server.Discord_Role != None:
                    discord_role = self.uBot.role_parse(db_server.Discord_Role, context, context.guild.id)
                    await context.author.add_roles(discord_role, reason='Auto Whitelisting')

                self.logger.command(f'Whitelisting {context.author.name} on {server.FriendlyName}')
                return

            # and the Wait time isnt Instant (!= 0 mins); let them know.. etc etc..
            elif wait_time_value != 0:
                cur_time = datetime.now(timezone.utc)
                display_time = discord.utils.format_dt((cur_time + timedelta(minutes=wait_time_value)))
                await message.edit(content=i18n.t('messages.whitelist_request.awaiting_approval_with_timer', display_time=display_time))
                # Checks if the Tasks is running, if not starts the task.
                if not self.whitelist_waitlist_handler.is_running():
                    self.whitelist_waitlist_handler.start()

        # Send view to specific channel
        whitelist_request_channel = self._client.get_channel(self.DBConfig.GetSetting('Whitelist_Request_Channel'))  # Whitelist Channel #This will point to a Staff Channel/Similar
        whitelist_request_message = await whitelist_request_channel.send(content=i18n.t('messages.whitelist_request.staff_channel_notice', author_name=context.message.author.name, server_name=server.FriendlyName))
        await whitelist_request_message.edit(view=self.uiBot.Whitelist_view(client=self._client, discord_message=whitelist_request_message, whitelist_message=context.message, amp_server=server, context=context, timeout=wait_time_value))

    @tasks.loop(seconds=30)
    async def whitelist_waitlist_handler(self):
        """This is the Whitelist Wait list handler, every 30 seconds it will check the list and whitelist them after the alotted wait time."""
        self.logger.command('Checking the Whitelist Wait List...')
        if len(self._client.Whitelist_wait_list) == 0:
            self.logger.dev(f'It Appears the Whitelist Wait List is empty; stopping the Task loop.')
            self.whitelist_waitlist_handler.stop()

        cur_time = datetime.now(timezone.utc)

        temp_Whitelist_wait_list = self._client.Whitelist_wait_list
        for key, value in list(temp_Whitelist_wait_list.items()):
            cur_message = value['context'].channel.get_partial_message(key)
            cur_amp_server = value['ampserver']  # AMPInstance Object
            cur_message_context = value['context']
            cur_db_user = value['dbuser']  # This is the DB User object
            db_server = self.DB.GetServer(cur_amp_server.InstanceID)

            # Wait time is per-Server, so it must be read fresh for each entry rather than once globally.
            try:
                wait_time = timedelta(minutes=db_server.Whitelist_Wait_Time)  # This may error if someone changes the wait time to 0 inbetween a loop..
            except Exception:
                wait_time = timedelta(minutes=1)  # Fallback to 1 min delay if somehow the value fails to get parsed.

            # This should compare datetime objects and if the datetime of when the message was created plus the wait time is greater than or equal the cur_time they get whitelisted.
            if cur_message.created_at + wait_time <= cur_time:
                if cur_amp_server.check_Whitelist(cur_db_user):
                    self.logger.dev(f'Whitelist Request time has come up; Attempting to Whitelist {cur_message_context.author.name} on {db_server.FriendlyName}')

                    # This handles all the Discord Role stuff.
                    if db_server != None and db_server.Discord_Role != None:
                        discord_role = self.uBot.role_parse(db_server.Discord_Role, cur_message_context, cur_message_context.guild.id)
                        discord_user = self.uBot.user_parse(cur_message.author.id, cur_message_context, cur_message_context.guild.id)
                        await discord_user.add_roles(discord_role, reason='Auto Whitelisting')

                    # This is for all the Replies
                    if len(self.DB.GetAllWhitelistReplies()) != 0:
                        whitelist_reply = random.choice(self.DB.GetAllWhitelistReplies())
                        #
                        await cur_message_context.channel.send(content=f'{cur_message_context.author.mention} \n{self.uBot.whitelist_reply_handler(whitelist_reply, cur_message_context, cur_amp_server)}', reference=cur_message, delete_after=self._client.Message_Timeout)
                    else:
                        await cur_message_context.channel.send(content=i18n.t('messages.whitelist_request.waitlist_success_no_reply', mention=cur_message_context.author.mention, server_name=db_server.FriendlyName), reference=cur_message, delete_after=self._client.Message_Timeout)

                    cur_amp_server.addWhitelist(db_user=cur_db_user)
                    self.logger.command(f'Whitelisting {cur_message_context.author.name} on {cur_amp_server.FriendlyName}')
                    self._client.Whitelist_wait_list.pop(key)


async def setup(client: commands.Bot):
    await client.add_cog(Whitelist(client))
