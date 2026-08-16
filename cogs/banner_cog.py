# Copyright (C) 2021-2022 Katelynn Cadwallader
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

import asyncio
import logging
import math
import os
import pathlib
import sqlite3
from datetime import datetime
from importlib.resources import is_resource
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError, available_timezones

import discord
from discord import MessageType, app_commands
from discord.app_commands import Choice
from discord.ext import commands, tasks
from PIL import Image

from core import AMP_Handler
from core import DB as DB
import modules.banner_creator as BC
from core import utils
from core import utils_permissions
from core import utils_discord
from core import utils_embeds
from core import utils_ui
from utils_dev.banner_editor.ui.view import Banner_Editor_View
from core import i18n

# This is used to force cog order to prevent missing methods.
Dependencies = ["amp_server_cog.py", "bot_cog.py"]


class Banner(commands.Cog):
    def __init__(self, client: commands.Bot):
        self._client = client
        self.name = os.path.basename(__file__)
        self.logger = logging.getLogger()  # Point all print/logging statements here!

        self.AMPHandler = AMP_Handler.getAMPHandler()
        self.AMP = self.AMPHandler.AMP  # Main AMP object
        self.AMPInstances = self.AMPHandler.AMP_Instances  # Main AMP Instance Dictionary

        self.DBHandler = DB.getDBHandler()
        self.DB = self.DBHandler.DB  # Main Database object
        self.DBConfig = self.DB.DBConfig

        self.uBot = utils.botUtils(client)
        self.eBot = utils_embeds.botEmbeds(client)
        self.uiBot = utils_ui
        self.BC = BC

        self.uBot.sub_command_handler('server', self.amp_banner)  # This adds server specific amp_banner commands to the `/server` parent command.
        self.uBot.sub_command_handler('bot', self.banner_settings)
        self.uBot.sub_command_handler('bot', self.banner_group_group)

        if not self.DBConfig.GetSetting('Banner_Timezone'):
            self.DBConfig.SetSetting('Banner_Timezone', "UTC")
        if self.DBConfig.GetSetting('Banner_Use_12Hour') is None:
            self.DBConfig.SetSetting('Banner_Use_12Hour', True)

        if self.DBConfig.GetSetting('Banner_Auto_Update') == True:
            self.server_display_update.start()
            self.banner_loop_time_control.start()
            self.logger.dev(f'**{self.name.title()}** Server Display Banners Task Loop is Running: {self.server_display_update.is_running()}')

        self.logger.info(f'**SUCCESS** Loading Module **{self.name.title()}**')

    @property
    def _Message_Timeout(self):
        return self.DBConfig.Message_timeout

    def _get_current_timezone_time(self) -> datetime:
        """Return the current time using the configured `Banner_Timezone` setting.

        Falls back to UTC if the stored timezone is missing or invalid.
        """
        tz_name = self.DBConfig.GetSetting('Banner_Timezone')
        if not tz_name:
            tz_name = "UTC"
            self.DBConfig.SetSetting('Banner_Timezone', tz_name)
        try:
            return datetime.now(ZoneInfo(tz_name))
        except ZoneInfoNotFoundError:
            self.logger.error(f"Invalid timezone '{tz_name}' in Banner_Timezone setting. Falling back to UTC.")
            return datetime.now(ZoneInfo("UTC"))

    def _get_time_format(self) -> str:
        """Return the strftime format string based on the `Banner_Use_12Hour` setting."""
        use_12h = self.DBConfig.GetSetting('Banner_Use_12Hour')
        if use_12h is None or use_12h == True:
            return '%Y-%m-%d | %I:%M %p %Z'
        return '%Y-%m-%d | %H:%M %Z'

    async def autocomplete_timezones(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        """Autocomplete for IANA timezone names, filtered by what the user has typed so far."""
        all_zones = sorted(available_timezones())
        matches = [tz for tz in all_zones if current.lower() in tz.lower()]
        return [app_commands.Choice(name=tz, value=tz) for tz in matches[:25]]

    @commands.Cog.listener('on_message_delete')
    async def on_message_delete(self, message: discord.Message):
        """This should handle if someone deletes the Display Messages."""

        # This should allow on_message_delete to ignore ephemeral message timed delete events.
        if hasattr(message, "type") and message.type == MessageType.chat_input_command:
            return

        self.logger.dev(f'{self.name.title()} `on_message_delete` event fired.. attempting to remove the message from the DB.')
        self.DB.Remove_Message_from_BannerGroup(messageid=message.id)

    @commands.Cog.listener('on_guild_channel_delete')
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        self.DB.Remove_Channel_from_BannerGroup(channelid=channel.id, guildid=channel.guild.id)

    async def autocomplete_banners(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        """This is for a file listing of the `resources/banners` path."""
        banners = []
        _cwd = pathlib.Path.cwd().joinpath('resources/banners')
        banner_file_list = _cwd.iterdir()
        for entry in banner_file_list:
            banners.append(entry.name)
        return [app_commands.Choice(name=banner, value=banner) for banner in banners if current.lower() in banner.lower()][:25]

    async def autocomplete_bannergroups(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        """This provides a Choice List of Banner Group Names"""
        banner_groups = self.DB.Get_All_BannerGroups()
        # If we don't have any entries. Send no results.
        if banner_groups == None or not len(banner_groups):
            return []
        return [app_commands.Choice(name=value, value=value)for key, value in banner_groups.items() if current.lower() in value.lower()][:25]

    async def autocomplete_bannergroups_channels(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        bg_channels = self.DB.Get_Channels_for_BannerGroup(interaction.namespace.group_name)
        try:
            # This could possibly fail if the "channel" gets deleted..and only if the `event` fails to fire.
            discord_channels = [interaction.guild.get_channel(value) for value in bg_channels]
            return [app_commands.Choice(name=channel.name, value=str(channel.id)) for channel in discord_channels if current.lower() in channel.name.lower()][:25]

        except:
            self.logger.error('We failed a `get_channel` inside of autocomplete_bannergroups_channels and defaulted to displaying the IDs')
            return [app_commands.Choice(name=str(value), value=str(value))for value in bg_channels if current.lower() in str(value).lower()][:25]

    async def banner_editor(self, context: commands.Context, amp_server: AMP_Handler.AMP.AMPInstance, db_server_banner=None):
        """Handles sending the banner."""
        db_server = self.DB.GetServer(amp_server.InstanceID)

        db_server_banner = db_server.getBanner()
        # Send a message so we can have a message.id to eidt later.
        sent_msg = await context.send(i18n.t('messages.banner.editor.creating'), ephemeral=True, delete_after=60)

        # Create my View first
        editor_view = Banner_Editor_View(amp_handler=self.AMPHandler, db_banner=db_server_banner, amp_server=amp_server, banner_message=sent_msg)
        banner_file = self.uiBot.banner_file_handler(self.BC.Banner_Generator(amp_server, db_server.getBanner())._image_())
        await sent_msg.edit(content=i18n.t('messages.banner.editor.title'), attachments=[banner_file], view=editor_view)

    async def _embed_generator(self, banner_name: str, server_list: list[str], message_list: list[discord.Message], discord_guild: discord.Guild, discord_channel: discord.TextChannel):
        embed_list = await self.eBot.server_display_embed(server_list=server_list, guild=discord_guild, banner_name=banner_name)
        if len(embed_list) == 0:
            self.logger.warning('We failed to find any Banners for your Instances.')
            return
        ratio = math.ceil((len(embed_list) / 10))
        # compare ratio to len(message_list)
        # If our message list is way larger than our embeds; lets remove the extras. (1 msg to 10 embeds)
        if len(message_list) > ratio:
            for message in message_list[ratio:]:
                self.DB.Remove_Message_from_BannerGroup(messageid=message.id)
                try:
                    await message.delete()
                except:
                    self.logger.error('Failed to find discord.Message object; removing Message from bannergroup.')

        # We have no Message IDs in the Database; so lets send new messages and store the IDs.
        # We have too many Embeds for the amount of Messages; we need to create some new ones.
        elif not len(message_list) or len(message_list) < ratio:
            # If we have messages; but we clearly didn't have enough. Lets remove all of them and send new ones.
            if len(message_list):
                for message in message_list:
                    self.DB.Remove_Message_from_BannerGroup(messageid=message.id)
                    try:
                        await message.delete()
                    except:
                        self.logger.error('Failed to find discord.Message object; removing Message from bannergroup.')

            for curpos in range(0, len(embed_list), 10):
                cur_message = await discord_channel.send(embeds=embed_list[curpos:(curpos + 9)])
                self.DB.Add_Message_to_BannerGroup(banner_groupname=banner_name, channelid=discord_channel.id, messageid=cur_message.id)

        elif len(message_list) == ratio:
            for curpos in range(0, len(message_list)):
                try:
                    # 0*10 = 0 : (0+1)*10 = 10 / 1*10 = 10 : (1+1)*10 = 20 / 2 *10 = 20 : (2+1)*10 = 30
                    now = self._get_current_timezone_time()
                    time_str = now.strftime(self._get_time_format())
                    await message_list[curpos].edit(content=i18n.t('messages.banner.display.edited_at', time_str=time_str), embeds=embed_list[curpos * 10:(curpos + 1) * 10], attachments=[])

                except discord.errors.Forbidden:
                    self.logger.error(f'{self._client.user.name} lacks permissions to edit messages in {discord_channel.name}, removing the Channel from {banner_name}.')
                    # self.DB.DelServerDisplayBanner(discord_guild.id, discord_channel.id)
                    self.DB.Remove_Channel_from_BannerGroup(channelid=discord_channel, guildid=discord_guild)

                except discord.errors.NotFound:
                    self.logger.error(f'{self._client.user.name} is unable to find the messages for {banner_name}, removing its messages.')
                    self.DB.Remove_Message_from_BannerGroup(messageid=message_list[curpos].id)

                await asyncio.sleep(2)

    async def _banner_generator(self, banner_name: str, server_list: list[str], message_list: list[discord.Message], discord_guild: discord.Guild, discord_channel: discord.TextChannel):
        banner_image_list = []

        for db_server in server_list:

            if db_server is None:
                continue

            if db_server.Hidden == 1:
                continue

            # We need the AMP object for the Banner Generator.
            try:
                amp_server = self.AMPHandler.AMP_Instances[db_server.InstanceID]
            except Exception:
                if self.DBConfig.GetSetting("Auto_BG_Remove") == True:
                    self.DB.Remove_Server_from_BannerGroup(banner_groupname=banner_name, instanceID=db_server.InstanceID)
                continue

            try:
                banner_file = self.uiBot.banner_file_handler(self.BC.Banner_Generator(amp_server, db_server.getBanner())._image_())
            except Exception:
                self.logger.exception(f'Failed to generate banner for InstanceID {db_server.InstanceID} in BannerGroup {banner_name}.')
                continue

            # Store all the images as a `discord.File` for ease of iterations.
            banner_image_list.append(banner_file)

        if not len(banner_image_list):
            self.logger.warning('We failed to find any Banners for your Instances.')
            return

        # If we have too many messages; well we need to remove the remaining messages.
        # We also remove the discord Messages too.
        if len(message_list) > len(banner_image_list):
            # Since Banner Images are 1 image per 1 message; we can use the len of our banner_image_list as our index
            old_messages = message_list[len(banner_image_list):]
            for message in old_messages:
                self.DB.Remove_Message_from_BannerGroup(messageid=message.id)
                try:
                    await message.delete()
                except:
                    self.logger.error('Failed to find discord.Message object; removing Message from bannergroup.')
                message_list.remove(message)

        # If our message_list is empty, we assume we haven't sent messages yet.
        # Or if the number of messages we have is less than the banner images, lets send new messages.
        elif not len(message_list) or (len(message_list) < len(banner_image_list)):
            # If we have messages; but we clearly didn't have enough. Lets remove all of them and send new ones.
            if len(message_list):
                for message in message_list:
                    try:
                        await message.delete()  # Remove any extra messages or existing messages.
                    except:
                        self.logger.error('Failed to find discord.Message object; removing Message from bannergroup.')
                    self.DB.Remove_Message_from_BannerGroup(messageid=message.id)

            for curpos in range(0, len(banner_image_list)):
                cur_message = await discord_channel.send(file=banner_image_list[curpos])
                self.DB.Add_Message_to_BannerGroup(banner_groupname=banner_name, channelid=discord_channel.id, messageid=cur_message.id)

        elif len(message_list) == len(banner_image_list):
            first_msg = True
            for curpos in range(0, len(message_list)):
                try:
                    if first_msg:
                        now = self._get_current_timezone_time()
                        time_str = now.strftime(self._get_time_format())
                        await message_list[curpos].edit(content=i18n.t('messages.banner.display.edited_at', time_str=time_str), attachments=[banner_image_list[curpos]], embed=None)
                        first_msg = False
                    else:
                        await message_list[curpos].edit(attachments=[banner_image_list[curpos]], embed=None)

                except discord.errors.Forbidden:
                    self.logger.error(f'{self._client.user.name} lacks permissions to edit messages in {discord_channel.name}, removing the Channel from {banner_name}.')
                    self.DB.Remove_Channel_from_BannerGroup(channelid=discord_channel.id, guildid=discord_channel.guild.id)

                except discord.errors.NotFound:
                    self.logger.error(f'{self._client.user.name} is unable to find the messages for {banner_name}, removing its messages.')
                    self.DB.Remove_Message_from_BannerGroup(messageid=message_list[curpos].id)

                await asyncio.sleep(2)

    @tasks.loop(minutes=1)
    async def banner_loop_time_control(self):
        """Dynamically adjusts the `server_display_update` loop time."""
        base_time = 60  # seconds
        # for each message we have in the DB; lets add to our base_time so we can *hopefully* avoid API ratelimit from discord.
        num_messages = self.DB.get_all_bannergroup_messages()
        base_time += (num_messages * 10)

        if self.server_display_update.seconds == base_time:
            return
        else:
            self.logger.info(f'We adjusted our Banner Update time from {self.server_display_update.seconds} seconds to {base_time} seconds.')
            self.server_display_update.change_interval(seconds=base_time)

    @tasks.loop(seconds=60)
    async def server_display_update(self):
        """This will handle the constant updating of Server Display Messages"""
        if not self._client.is_ready():
            return

        if not self.DBConfig.GetSetting('Banner_Auto_Update'):
            return

        self.logger.info('**Updating Banner Displays**')

        Banners = self.DB.Get_All_BannerGroup_Info()
        # Banners structure = {916195413839712277: {'name': 'TestBannerGroup', 'guild_id': 602285328320954378, 'servers': [1], 'messages': [1079236992145051668]}}
        for key, value in Banners.items():
            self.logger.dev(f'Getting the Banner Group: {value["name"]} from the DB')
            discord_guild = self._client.get_guild(value['guild_id'])
            if discord_guild is None:
                self.logger.error(f'Unable to find guild {value["guild_id"]} for BannerGroup {value["name"]}, skipping.')
                continue

            discord_channel = discord_guild.get_channel(key)
            if discord_channel is None:
                self.logger.error(f'Unable to find channel {key} in guild {discord_guild.id} for BannerGroup {value["name"]}, removing channel mapping.')
                self.DB.Remove_Channel_from_BannerGroup(channelid=key, guildid=discord_guild.id)
                continue

            # This should create a list of DBServer Objects.
            servers = []
            if len(value['servers']):
                for entry in value["servers"]:
                    db_server = self.DB.GetServer(ServerID=entry)
                    if db_server not in [None, "None"]:
                        servers.append(db_server)

            messages = []
            value['messages'] = [entry for entry in value['messages'] if entry not in ['None', None]]

            if len(value['messages']):
                # This should give us a list of partial message objects.
                messages = [discord_channel.get_partial_message(entry) for entry in value["messages"]]

            try:
                if self.DBConfig.GetSetting('Banner_Type') == 1:
                    await self._banner_generator(banner_name=value['name'], server_list=servers, message_list=messages, discord_channel=discord_channel, discord_guild=discord_guild)

                else:
                    await self._embed_generator(banner_name=value['name'], server_list=servers, message_list=messages, discord_channel=discord_channel, discord_guild=discord_guild)
            except Exception:
                self.logger.exception(f'Banner auto-update failed for BannerGroup {value["name"]}, continuing with next group.')

    @commands.hybrid_group(name='bannergroup', description=i18n.t('commands.bot.bannergroup.description'))
    async def banner_group_group(self, context: commands.Context):
        if context.invoked_subcommand is None:
            await context.send(i18n.t('common.invalid_command'), ephemeral=True, delete_after=30)

    @banner_group_group.command(name='create_group', description=i18n.t('commands.bot.bannergroup.create_group.description'))
    @utils_permissions.role_check()
    async def banner_group_create(self, context: commands.Context, group_name: str):
        try:
            self.DB.Add_BannerGroup(name=group_name)
            return await context.send(content=i18n.t('messages.banner.group.create.success', group_name=group_name), ephemeral=True, delete_after=self._client.Message_Timeout)
        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed" in e.args[0]:
                return await context.send(content=i18n.t('messages.banner.group.create.duplicate', group_name=group_name), ephemeral=True, delete_after=self._client.Message_Timeout)

    @banner_group_group.command(name='info', description=i18n.t('commands.bot.bannergroup.info.description'))
    @app_commands.autocomplete(group_name=autocomplete_bannergroups)
    async def banner_group_info(self, context: commands.Context, group_name: str):
        banner_info = self.DB.Get_one_BannerGroup_info(name=group_name)

        disc_chan_list = []
        servers = []
        if banner_info != None and len(banner_info):
            for key, value in banner_info.items():

                for entry in value['InstanceName']:
                    if entry not in servers and entry != None:
                        servers.append(entry)

                for entry in value['Discord_Channel']:
                    if entry not in disc_chan_list and entry != None:
                        disc_chan_list.append(context.guild.get_channel(entry).mention if context.guild.get_channel(entry) != None else entry)

        # If our lists are empty; add a 'None' placeholder to prevent display issues.
        if not len(servers):
            servers.append(i18n.t('messages.banner.group.info.none_placeholder'))

        if not len(disc_chan_list):
            disc_chan_list.append(i18n.t('messages.banner.group.info.none_placeholder'))

        embed = discord.Embed(title=group_name, color=0x71368a, description=i18n.t('embeds.banner_group_info.description'))
        embed.add_field(name=i18n.t('embeds.banner_group_info.servers_field'), value="\n".join(servers), inline=False)
        embed.add_field(name=i18n.t('embeds.banner_group_info.channels_field'), value="\n".join(disc_chan_list), inline=False)
        return await context.send(embed=embed, ephemeral=True, delete_after=(self._client.Message_Timeout * 2))

    @banner_group_group.command(name='rename', description=i18n.t('commands.bot.bannergroup.rename.description'))
    @app_commands.autocomplete(group_name=autocomplete_bannergroups)
    async def banner_group_rename(self, context: commands.Context, group_name: str, new_groupname: str):
        try:
            self.DB.Update_BannerGroup(new_name=new_groupname, name=group_name)
            return await context.send(content=i18n.t('messages.banner.group.rename.success', group_name=group_name, new_groupname=new_groupname), ephemeral=True, delete_after=self._client.Message_Timeout)

        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed" in e.args[0]:
                return await context.send(content=i18n.t('messages.banner.group.rename.duplicate', new_groupname=new_groupname), ephemeral=True, delete_after=self._client.Message_Timeout)

    @banner_group_group.command(name='add', description=i18n.t('commands.bot.bannergroup.add.description'))
    @app_commands.autocomplete(server=utils_discord.autocomplete_servers)
    @app_commands.autocomplete(group_name=autocomplete_bannergroups)
    async def banner_group_add(self, context: commands.Context, group_name: str, server: str | None = None, channel: discord.abc.GuildChannel | None = None):
        c_status = True
        s_status = True

        if self.DB.Get_BannerGroup(name=group_name) == None:
            return await context.send(content=i18n.t('messages.banner.group.add.not_exist', group_name=group_name), ephemeral=True, delete_after=self._client.Message_Timeout)

        if server == None and channel == None:
            return await context.send(content=i18n.t('messages.banner.group.add.need_selection'), ephemeral=True, delete_after=self._client.Message_Timeout)

        if server != None:
            db_server = self.DB.GetServer(InstanceID=server)
            s_status = self.DB.Add_Server_to_BannerGroup(banner_groupname=group_name, instanceID=server)

        if channel != None:
            c_status = self.DB.Add_Channel_to_BannerGroup(banner_groupname=group_name, channelid=channel.id, guildid=context.guild.id)

        if not c_status or not s_status:
            server_part = f' `{db_server.InstanceName}`' if server != None else ''
            and_part = i18n.t('common.and_joiner') if server != None and channel != None else ''
            channel_part = channel.mention if channel != None else ''
            return await context.send(content=i18n.t('messages.banner.group.add.already_exists', server_part=server_part, and_part=and_part, channel_part=channel_part, group_name=group_name), ephemeral=True, delete_after=self._client.Message_Timeout)

        server_part = f'` {db_server.InstanceName}`' if server != None else ''
        and_part = i18n.t('common.and_joiner') if server != None and channel != None else ''
        channel_part = channel.mention if channel != None else ''
        c_str = i18n.t('messages.banner.group.add.success', group_name=group_name, server_part=server_part, and_part=and_part, channel_part=channel_part)
        return await context.send(content=c_str, ephemeral=True, delete_after=self._client.Message_Timeout)

    @banner_group_group.command(name='remove', description=i18n.t('commands.bot.bannergroup.remove.description'))
    @app_commands.autocomplete(server=utils_discord.autocomplete_servers)
    @app_commands.autocomplete(channel=autocomplete_bannergroups_channels)
    @app_commands.autocomplete(group_name=autocomplete_bannergroups)
    async def banner_group_remove(self, context: commands.Context, group_name, server: str | None = None, channel: str | None = None):
        if server == None and channel == None:
            return await context.send(content=i18n.t('messages.banner.group.remove.need_selection'), ephemeral=True, delete_after=self._client.Message_Timeout)

        if server != None:
            db_server = self.DB.GetServer(InstanceID=server)
            self.DB.Remove_Server_from_BannerGroup(banner_groupname=group_name, instanceID=server)

        if channel != None:
            if type(channel) != str:
                # If we got a discord.abc.GuildChannel (or similar object) We should be able to call `.id` on said object.
                channel = channel.id
            banner_info = self.DB.Get_Messages_for_BannerGroup(banner_groupname=group_name)
            if banner_info == None:
                return await context.send(content=i18n.t('messages.banner.group.remove.no_entries', group_name=group_name), ephemeral=True, delete_after=self._Message_Timeout)
            for key, value in banner_info.items():
                cur_channel = self._client.get_channel(key)
                # We are going to find the old messages and delete them if possible.
                for entry in value['messages']:
                    try:
                        await cur_channel.get_partial_message(entry).delete()
                        self.logger.dev(f'Found message in channel and deleted message. id: {entry}')
                    except Exception:
                        self.logger.error(f'Was unable to delete a message id: {entry}, removing from DB')

            # We still need to `int` the channel object because on the off chance the channel has been deleted and the autocomplete fails to find said channel;
            # it will provide us with a str version of the `channel.id` that was stored in the DB. (Autocompletes want a `str` for value=)
            self.DB.Remove_Channel_from_BannerGroup(channelid=int(channel), guildid=context.guild.id)

        server_part = f'` {db_server.InstanceName}`' if server != None else ''
        and_part = i18n.t('common.and_joiner') if server != None and channel != None else ''
        channel_part = f'`{self._client.get_channel(int(channel)).mention}`' if channel != None else ''
        c_str = i18n.t('messages.banner.group.remove.success', group_name=group_name, server_part=server_part, and_part=and_part, channel_part=channel_part)
        return await context.send(content=c_str, ephemeral=True, delete_after=self._client.Message_Timeout)

    @banner_group_group.command(name='delete_group', description=i18n.t('commands.bot.bannergroup.delete_group.description'))
    @app_commands.autocomplete(group_name=autocomplete_bannergroups)
    async def banner_group_delete(self, context: commands.Context, group_name: str):
        banner_info = self.DB.Get_Messages_for_BannerGroup(banner_groupname=group_name)
        for key, value in banner_info.items():
            cur_channel = self._client.get_channel(key)
            # We are going to find the old messages and delete them if possible.
            for entry in value['messages']:
                try:
                    await cur_channel.get_partial_message(entry).delete()
                    self.logger.dev(f'Found message in channel and deleted message. id: {entry}')
                except Exception:
                    self.logger.error(f'Was unable to delete a message id: {entry}, removing from DB')

        self.DB.Delete_BannerGroup(name=group_name)
        await context.send(content=i18n.t('messages.banner.group.delete.success', group_name=group_name), ephemeral=True, delete_after=self._client.Message_Timeout)

    @commands.hybrid_group(name='banner', description=i18n.t('commands.server.banner.description'))
    @utils_permissions.role_check()
    async def amp_banner(self, context: commands.Context):
        if context.invoked_subcommand is None:
            await context.send(i18n.t('common.invalid_command'), ephemeral=True, delete_after=30)

    @amp_banner.command(name='background', description=i18n.t('commands.server.banner.background.description'))
    @app_commands.autocomplete(server=utils_discord.autocomplete_servers)
    @app_commands.autocomplete(image=autocomplete_banners)
    @utils_permissions.role_check()
    async def amp_banner_background(self, context: commands.Context, server, image):
        amp_server = self.uBot.serverparse(server, context, context.guild.id)
        if amp_server == None:
            return await context.send(i18n.t('common.server_not_found', server=server), ephemeral=True, delete_after=self._client.Message_Timeout)

        db_server = self.DB.GetServer(amp_server.InstanceID)
        banner = db_server.getBanner()
        image_path = pathlib.Path.cwd().joinpath('resources/banners').as_posix() + '/' + image
        banner.background_path = image_path
        amp_server._setDBattr()
        my_image = Image.open(image_path)
        await context.send(content=i18n.t('messages.banner.background.success', server_name=amp_server.FriendlyName), file=self.uiBot.banner_file_handler(my_image), ephemeral=True, delete_after=self._client.Message_Timeout)

    @amp_banner.command(name='settings', description=i18n.t('commands.server.banner.settings.description'))
    @utils_permissions.role_check()
    @app_commands.autocomplete(server=utils_discord.autocomplete_servers)
    async def amp_banner_settings(self, context: commands.Context, server):
        self.logger.command(f'{context.author.name} used Server Banner Settings Editor...')
        amp_server = self.uBot.serverparse(server, context, context.guild.id)
        if amp_server == None:
            return await context.send(i18n.t('common.server_not_found', server=server), ephemeral=True, delete_after=self._client.Message_Timeout)

        await self.banner_editor(context, amp_server)

    @commands.hybrid_group(name='banner_settings', description=i18n.t('commands.bot.banner_settings.description'))
    async def banner_settings(self, context: commands.Context):
        if context.invoked_subcommand is None:
            await context.send(i18n.t('common.invalid_command'), ephemeral=True, delete_after=self._client.Message_Timeout)

    @banner_settings.command(name='auto_update', description=i18n.t('commands.bot.banner_settings.auto_update.description'))
    @utils_permissions.role_check()
    @app_commands.choices(flag=[Choice(name=i18n.t('common.bool.true'), value=1), Choice(name=i18n.t('common.bool.false'), value=0)])
    async def banner_autoupdate(self, context: commands.Context, flag: Choice[int] = 1):
        self.logger.command(f'{context.author.name} used Bot Display Banners Auto Update...')

        if flag.value == 1:
            self.DBConfig.SetSetting('Banner_Auto_Update', True)

            if not self.server_display_update.is_running():
                self.server_display_update.start()
            if not self.banner_loop_time_control.is_running():
                self.banner_loop_time_control.start()

            return await context.send(i18n.t('messages.banner.settings.auto_update.enabled'), ephemeral=True, delete_after=self._client.Message_Timeout)
        if flag.value == 0:
            self.DBConfig.SetSetting('Banner_Auto_Update', False)

        if self.server_display_update.is_running():
            self.banner_loop_time_control.stop()
        if self.banner_loop_time_control.is_running():
            self.server_display_update.stop()

            return await context.send(i18n.t('messages.banner.settings.auto_update.disabled'), ephemeral=True, delete_after=self._client.Message_Timeout)
        else:
            return await context.send(i18n.t('messages.banner.settings.auto_update.invalid_choice'), ephemeral=True, delete_after=self._client.Message_Timeout)

    @banner_settings.command(name='type', description=i18n.t('commands.bot.banner_settings.type.description'))
    @utils_permissions.role_check()
    @app_commands.choices(type=[Choice(name=i18n.t('embeds.bot_settings.banner_type_images'), value=1), Choice(name=i18n.t('embeds.bot_settings.banner_type_embeds'), value=0)])
    async def banner_type(self, context: commands.Context, type: Choice[int] = 0):
        self.logger.command(f'{context.author.name} used Bot Banners Type...')

        if type.value == 0:
            self.DBConfig.SetSetting('Banner_Type', 0)
            return await context.send(i18n.t('messages.banner.settings.type.embeds'), ephemeral=True, delete_after=self._client.Message_Timeout)

        if type.value == 1:
            self.DBConfig.SetSetting('Banner_Type', 1)
            return await context.send(i18n.t('messages.banner.settings.type.images'), ephemeral=True, delete_after=self._client.Message_Timeout)

    @banner_settings.command(name='auto_remove', description=i18n.t('commands.bot.banner_settings.auto_remove.description'))
    @utils_permissions.role_check()
    @app_commands.choices(flag=[Choice(name=i18n.t('common.bool.true'), value=1), Choice(name=i18n.t('common.bool.false'), value=0)])
    async def banner_auto_remove(self, context: commands.Context, flag: Choice[int] = 1):
        self.logger.command(f'{context.author.name} used Bot Banners Auto Remove...')

        if flag.value == 0:
            self.DBConfig.SetSetting('Auto_BG_Remove', 0)
            return await context.send(i18n.t('messages.banner.settings.auto_remove.disabled'), ephemeral=True, delete_after=self._client.Message_Timeout)

        if flag.value == 1:
            self.DBConfig.SetSetting('Auto_BG_Remove', 1)
            return await context.send(i18n.t('messages.banner.settings.auto_remove.enabled'), ephemeral=True, delete_after=self._client.Message_Timeout)

    @banner_settings.command(name='timeformat', description=i18n.t('commands.bot.banner_settings.timeformat.description'))
    @utils_permissions.role_check()
    @app_commands.choices(format=[Choice(name=i18n.t('commands.bot.banner_settings.timeformat.params.format.choices.1'), value=1), Choice(name=i18n.t('commands.bot.banner_settings.timeformat.params.format.choices.0'), value=0)])
    async def banner_timeformat(self, context: commands.Context, format: Choice[int]):
        self.logger.command(f'{context.author.name} changed banner time format to {"12h" if format.value == 1 else "24h"}')

        self.DBConfig.SetSetting('Banner_Use_12Hour', bool(format.value))

        mode = i18n.t('messages.banner.settings.timeformat.mode_12h') if format.value == 1 else i18n.t('messages.banner.settings.timeformat.mode_24h')
        now = self._get_current_timezone_time()
        time_str = now.strftime(self._get_time_format())

        await context.send(
            content=i18n.t('messages.banner.settings.timeformat.result', mode=mode, time_str=time_str),
            ephemeral=True,
            delete_after=self._client.Message_Timeout
        )

    @banner_settings.command(name='timezone', description=i18n.t('commands.bot.banner_settings.timezone.description'))
    @utils_permissions.role_check()
    @app_commands.autocomplete(timezone=autocomplete_timezones)
    async def banner_timezone(self, context: commands.Context, timezone: str):
        self.logger.command(f'{context.author.name} changed banner timezone to {timezone}')

        try:
            ZoneInfo(timezone)
        except ZoneInfoNotFoundError:
            return await context.send(
                content=i18n.t('messages.banner.settings.timezone.invalid', timezone=timezone),
                ephemeral=True,
                delete_after=self._client.Message_Timeout * 2
            )

        self.DBConfig.SetSetting('Banner_Timezone', timezone)
        now = self._get_current_timezone_time()
        time_str = now.strftime(self._get_time_format())
        await context.send(
            content=i18n.t('messages.banner.settings.timezone.result', timezone=timezone, time_str=time_str),
            ephemeral=True,
            delete_after=self._client.Message_Timeout
        )


async def setup(client):
    await client.add_cog(Banner(client))
