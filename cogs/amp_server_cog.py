# Copyright (C) 2021-2022 Katelynn Cadwallader
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations
import os
import logging
from datetime import datetime, UTC
import asyncio

import discord
from discord.ext import commands, tasks
from discord import app_commands
from discord.app_commands import Choice
from numpy import isin

from core import AMP_Handler
from core import DB
from core import utils
from core import utils_permissions
from core import utils_discord
from core import utils_ui
from core import utils_embeds
import modules.banner_creator as BC
from core import i18n

# This is used to force cog order to prevent missing methods.
Dependencies = None


class AMP_Server(commands.Cog):
    def __init__(self, client: discord.Client):
        self._client = client
        self.name = os.path.basename(__file__)
        self.logger = logging.getLogger()

        self.AMPHandler = AMP_Handler.getAMPHandler()
        self.AMPInstances = self.AMPHandler.AMP_Instances
        self.AMPThreads = self.AMPHandler.AMP_Console_Threads

        self.DBHandler = DB.getDBHandler()
        self.DB = self.DBHandler.DB
        self.DBConfig = self.DBHandler.DBConfig

        self.uBot = utils.botUtils(client)
        self.uiBot = utils_ui
        self.eBot = utils_embeds.botEmbeds(client)
        self.BC = BC

        self.logger.info(f'**SUCCESS** Initializing {self.name.title().replace("Amp", "AMP")}')

    async def autocomplete_regex(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        """Autocomplete for Regex Pattern Names"""
        choice_list = []
        regex_patterns = self.DB.GetAllRegexPatterns()

        for regex in regex_patterns:
            choice_list.append(regex_patterns[regex]["Name"])
        return [app_commands.Choice(name=choice, value=choice) for choice in choice_list if current.lower() in choice.lower()][:25]

    async def autocomplete_server_regex(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        """Autocomplete for Regex Pattern Names"""
        choice_list = []

        if interaction.namespace.server != None:
            db_server = self.DB.GetServer(InstanceID=interaction.namespace.server)
            regex_patterns = db_server.GetServerRegexPatterns()

            if len(regex_patterns):
                for regex in regex_patterns:
                    choice_list.append(regex_patterns[regex]["Name"])
            else:
                choice_list.append('None')

        return [app_commands.Choice(name=choice, value=choice) for choice in choice_list if current.lower() in choice.lower()][:25]

    @commands.hybrid_group(name='server', description=i18n.t('commands.server.description'))
    @utils_permissions.role_check()
    async def server(self, context: commands.Context):
        if context.invoked_subcommand is None:
            await context.send(i18n.t('common.try_again'), ephemeral=True, delete_after=self._client.Message_Timeout)

    @server.command(name='update', description=i18n.t('commands.server.update.description'))
    @utils_permissions.role_check()
    async def amp_server_update(self, context: commands.Context):
        self.logger.command(f'{context.author.name} used AMP Server Update')
        new_server = self.AMPHandler._instanceValidation(main_amp=self.AMPHandler.AMP)
        if new_server:
            await context.send(i18n.t('messages.amp_server.update.found', new_server=new_server), ephemeral=True, delete_after=self._client.Message_Timeout)
        else:
            await context.send(i18n.t('messages.amp_server.update.none_found'), ephemeral=True, delete_after=self._client.Message_Timeout)

    @server.command(name='broadcast', description=i18n.t('commands.server.broadcast.description'))
    @utils_permissions.role_check()
    @app_commands.choices(prefix=[Choice(name=i18n.t(f'commands.server.broadcast.params.prefix.choices.{x}'), value=x) for x in ['Announcement', 'Broadcast', 'Maintenance', 'Info', 'Warning']])
    async def amp_server_broadcast(self, context: commands.Context, prefix: Choice[str], message: str):
        self.logger.command(f'{context.author.name} used AMP Server Broadcast')
        discord_message = await context.send(i18n.t('messages.amp_server.broadcast.sending'), ephemeral=True)
        for amp_server in list(self.AMPInstances):
            if self.AMPInstances[amp_server].Running:
                if self.AMPInstances[amp_server]._ADScheck():
                    self.AMPInstances[amp_server].Broadcast_Message(message, prefix=prefix.value)

        await discord_message.edit(content=i18n.t('messages.amp_server.broadcast.sent', prefix=prefix.value))
        await discord_message.delete(delay=self._client.Message_Timeout)


# This section is AMP Server Commands ----------------------------------------------------------------------------------------------------------------------------------------------------------------


    @server.command(name='start', description=i18n.t('commands.server.start.description'))
    @utils_permissions.role_check()
    @app_commands.autocomplete(server=utils_discord.autocomplete_servers)
    async def amp_server_start(self, context: commands.Context, server):
        self.logger.command(f'{context.author.name} used AMP Server Started...')
        await context.defer(ephemeral=True)

        amp_server = self.uBot.serverparse(server, context, context.guild.id)

        if not amp_server._ADScheck():
            amp_server.StartInstance()
            amp_server.ADS_Running = True
            await context.send(i18n.t('messages.amp_server.start.starting', server_name=amp_server.InstanceName), ephemeral=True, delete_after=self._client.Message_Timeout)
        else:
            return await context.send(i18n.t('messages.amp_server.start.already_running'), ephemeral=True, delete_after=self._client.Message_Timeout)

    @server.command(name='stop', description=i18n.t('commands.server.stop.description'))
    @utils_permissions.role_check()
    @app_commands.autocomplete(server=utils_discord.autocomplete_servers)
    async def amp_server_stop(self, context: commands.Context, server):
        self.logger.command(f'{context.author.name} used AMP Server Stopped...')
        await context.defer(ephemeral=True)

        amp_server = await self.uBot._serverCheck(context, server)
        if amp_server:
            amp_server.StopInstance()
            amp_server.ADS_Running = False
            await context.send(i18n.t('messages.amp_server.stop.stopping', server_name=amp_server.InstanceName), ephemeral=True, delete_after=self._client.Message_Timeout)

    @server.command(name='restart', description=i18n.t('commands.server.restart.description'))
    @utils_permissions.role_check()
    @app_commands.autocomplete(server=utils_discord.autocomplete_servers)
    async def amp_server_restart(self, context: commands.Context, server):
        self.logger.command(f'{context.author.name} used AMP Server Restart...')
        await context.defer(ephemeral=True)

        amp_server = await self.uBot._serverCheck(context, server)
        if amp_server:
            amp_server.RestartInstance()
            amp_server.ADS_Running = True
            await context.send(i18n.t('messages.amp_server.restart.restarting', server_name=amp_server.InstanceName), ephemeral=True, delete_after=self._client.Message_Timeout)

    @server.command(name='kill', description=i18n.t('commands.server.kill.description'))
    @utils_permissions.role_check()
    @app_commands.autocomplete(server=utils_discord.autocomplete_servers)
    async def amp_server_kill(self, context: commands.Context, server):
        self.logger.command(f'{context.author.name} used AMP Server Kill...')
        await context.defer(ephemeral=True)

        amp_server = await self.uBot._serverCheck(context, server)
        if amp_server:
            amp_server.KillInstance()
            amp_server.ADS_Running = False
            await context.send(i18n.t('messages.amp_server.kill.killing', server_name=amp_server.InstanceName), ephemeral=True, delete_after=self._client.Message_Timeout)

    @server.command(name='msg', description=i18n.t('commands.server.msg.description'))
    @utils_permissions.role_check()
    @app_commands.autocomplete(server=utils_discord.autocomplete_servers)
    async def amp_server_message(self, context: commands.Context, server, message: str):
        self.logger.command(f'{context.author.name} used AMP Server Message...')

        amp_server = await self.uBot._serverCheck(context, server)
        if amp_server:
            amp_server.ConsoleMessage(message)
        await context.send(i18n.t('messages.amp_server.msg.sent', message=message, server_name=amp_server.InstanceName), ephemeral=True, delete_after=self._client.Message_Timeout)

    @server.command(name='backup', description=i18n.t('commands.server.backup.description'))
    @utils_permissions.role_check()
    @app_commands.autocomplete(server=utils_discord.autocomplete_servers)
    async def amp_server_backup(self, context: commands.Context, server):
        self.logger.command(f'{context.author.name} used AMP Server Backup...')

        amp_server = await self.uBot._serverCheck(context, server)
        if amp_server:
            title = f"Backup by {context.author.display_name}"
            time = str(datetime.now(tz=UTC))
            description = f"Created at {time} by {context.author.display_name}"
            display_description = i18n.t('messages.amp_server.backup.description', time_str=str(datetime.now(tz=UTC).strftime("%Y-%m-%d %H:%M")), author=context.author.display_name)
            await context.send(i18n.t('messages.amp_server.backup.creating', server_name=server.InstanceName, description=display_description), ephemeral=True, delete_after=self._client.Message_Timeout)
            amp_server.takeBackup(title, description)

    @server.command(name='status', description=i18n.t('commands.server.status.description'))
    @utils_permissions.role_check()
    @app_commands.autocomplete(server=utils_discord.autocomplete_servers)
    async def amp_server_status(self, context: commands.Context, server):
        self.logger.command(f'{context.author.name} used AMP Server Status...')
        await context.defer(ephemeral=True)

        amp_server = self.uBot.serverparse(server, context, context.guild.id)
        if amp_server == None:
            return await context.send(i18n.t('common.server_not_found', server=server), ephemeral=True, delete_after=self._client.Message_Timeout)

        if amp_server.Running == False:
            await context.send(i18n.t('messages.amp_server.status.offline', server_name=amp_server.InstanceName), ephemeral=True, delete_after=self._client.Message_Timeout)

        if amp_server._ADScheck():
            tps, Users, cpu, Memory, Uptime = amp_server.getMetrics()
            Users_online = ', '.join(amp_server.getUserList())
            if len(Users_online) == 0:
                Users_online = 'None'
            server_embed = await self.eBot.server_status_embed(context, amp_server, tps, Users, cpu, Memory, Uptime, Users_online)
            view = self.uiBot.StatusView(context=context, amp_server=amp_server)
            self.uiBot.StartButton(amp_server, view, amp_server.StartInstance)
            self.uiBot.StopButton(amp_server, view, amp_server.StopInstance)
            self.uiBot.RestartButton(server, view, amp_server.RestartInstance)
            self.uiBot.KillButton(server, view, amp_server.KillInstance)
            await context.send(embed=server_embed, view=view, ephemeral=True)

        else:
            server_embed = await self.eBot.server_status_embed(context, amp_server)
            view = self.uiBot.StatusView()
            self.uiBot.StartButton(amp_server, view, amp_server.StartInstance)
            self.uiBot.StopButton(amp_server, view, amp_server.StopInstance).disabled = True
            self.uiBot.RestartButton(amp_server, view, amp_server.RestartInstance).disabled = True
            self.uiBot.KillButton(amp_server, view, amp_server.KillInstance).disabled = True
            await context.send(embed=server_embed, view=view, ephemeral=True)

    @server.command(name='users', description=i18n.t('commands.server.users.description'))
    @utils_permissions.role_check()
    @app_commands.autocomplete(server=utils_discord.autocomplete_servers)
    async def amp_server_users_list(self, context: commands.Context, server):
        self.logger.command(f'{context.author.name} used AMP Server Connected Users...')

        amp_server = await self.uBot._serverCheck(context, server)
        if amp_server:
            cur_users = (', ').join(amp_server.getUserList())
            if len(cur_users) != 0:
                await context.send(i18n.t('messages.amp_server.users.list', users=cur_users), ephemeral=True, delete_after=self._client.Message_Timeout)
            else:
                await context.send(i18n.t('messages.amp_server.users.none_online'), ephemeral=True, delete_after=self._client.Message_Timeout)

# This Section is AMP/DB Server Settings -----------------------------------------------------------------------------------------------------
    @server.group(name='settings', description=i18n.t('commands.server.settings.description'))
    @utils_permissions.role_check()
    async def amp_server_settings(self, context: commands.Context):
        if context.invoked_subcommand is None:
            await context.send(i18n.t('common.try_again'), ephemeral=True, delete_after=self._client.Message_Timeout)

    @amp_server_settings.command(name='info', description=i18n.t('commands.server.settings.info.description'))
    @utils_permissions.role_check()
    @app_commands.autocomplete(server=utils_discord.autocomplete_servers)
    async def amp_server_settings_info(self, context: commands.Context, server):
        self.logger.command(f'{context.author.name} used AMP Server Info')
        await context.defer(ephemeral=True)

        amp_server = await self.uBot._serverCheck(context, server, False)
        if amp_server:
            embed = await self.eBot.server_info_embed(amp_server, context)
            await context.send(embed=embed, ephemeral=True, delete_after=self._client.Message_Timeout)

    @amp_server_settings.command(name='avatar', description=i18n.t('commands.server.settings.avatar.description'))
    @utils_permissions.role_check()
    @app_commands.autocomplete(server=utils_discord.autocomplete_servers)
    async def amp_server_avatar(self, context: commands.Context, server, url: str):
        self.logger.command(f'{context.author.name} used Database Server Avatar Set')
        await context.defer()

        if not url.startswith('http://') and not url.startswith('https://'):
            return await context.send(i18n.t('messages.amp_server.avatar.invalid_url'), ephemeral=True, delete_after=self._client.Message_Timeout)

        amp_server = await self.uBot._serverCheck(context, server, False)
        if amp_server:
            db_server = self.DB.GetServer(InstanceID=amp_server.InstanceID)
            db_server.Avatar_url = url
            if url == 'None':
                await context.send(i18n.t('messages.amp_server.avatar.removed', server_name=amp_server.InstanceName), ephemeral=True, delete_after=self._client.Message_Timeout)
                amp_server._setDBattr()
                return
            if await self.uBot.validate_avatar(db_server) != None:
                amp_server._setDBattr()  # This will update the AMPInstance Attributes
                await context.send(i18n.t('messages.amp_server.avatar.success', server_name=amp_server.InstanceName, url=url), ephemeral=True, delete_after=self._client.Message_Timeout)
            else:
                await context.send(i18n.t('messages.amp_server.avatar.error', url=url), ephemeral=True, delete_after=self._client.Message_Timeout)

    @amp_server_settings.command(name='displayname', description=i18n.t('commands.server.settings.displayname.description'))
    @utils_permissions.role_check()
    @app_commands.autocomplete(server=utils_discord.autocomplete_servers)
    async def amp_server_displayname(self, context: commands.Context, server, name: str):
        self.logger.command(f'{context.author.name} used Database Server Display Name')

        amp_server = await self.uBot._serverCheck(context, server, False)
        if amp_server:
            db_server = self.DB.GetServer(InstanceID=amp_server.InstanceID)
            if db_server.setDisplayName(name) != False:
                amp_server._setDBattr()  # This will update the AMPInstance Attributes
                await context.send(i18n.t('messages.amp_server.displayname.success', server_name=amp_server.InstanceName, name=name), ephemeral=True, delete_after=self._client.Message_Timeout)
            else:
                await context.send(i18n.t('messages.amp_server.displayname.not_unique'), ephemeral=True, delete_after=self._client.Message_Timeout)

    @amp_server_settings.command(name='host', description=i18n.t('commands.server.settings.host.description'))
    @utils_permissions.role_check()
    @app_commands.autocomplete(server=utils_discord.autocomplete_servers)
    async def amp_server_host(self, context: commands.Context, server, hostname: str):
        self.logger.command(f'{context.author.name} used Database Server Host')

        amp_server = await self.uBot._serverCheck(context, server, False)
        if amp_server:
            db_server = self.DB.GetServer(InstanceID=amp_server.InstanceID)
            db_server.Host = hostname
            amp_server._setDBattr()  # This will update the AMPInstance Attributes
            await context.send(i18n.t('messages.amp_server.host.success', server_name=amp_server.InstanceName, hostname=hostname), ephemeral=True, delete_after=self._client.Message_Timeout)

    @amp_server_settings.command(name='donator', description=i18n.t('commands.server.settings.donator.description'))
    @utils_permissions.role_check()
    @app_commands.autocomplete(server=utils_discord.autocomplete_servers)
    @app_commands.choices(flag=[Choice(name=i18n.t('common.bool.true'), value=1), Choice(name=i18n.t('common.bool.false'), value=0)])
    async def amp_server_donator(self, context: commands.Context, server, flag: Choice[int] = 0):
        self.logger.command(f'{context.author.name} used Database Donator Flag')

        amp_server = await self.uBot._serverCheck(context, server, False)
        if amp_server:
            self.DB.GetServer(InstanceID=amp_server.InstanceID).Donator = flag.value
            amp_server._setDBattr()  # This will update the AMPConsole Attributes
            return await context.send(i18n.t('messages.amp_server.donator.success', server_name=amp_server.InstanceName, flag=flag.name if type(flag) == Choice else bool(flag)), ephemeral=True, delete_after=self._client.Message_Timeout)

    @amp_server_settings.command(name='role', description=i18n.t('commands.server.settings.role.description'))
    @utils_permissions.role_check()
    @app_commands.autocomplete(server=utils_discord.autocomplete_servers)
    async def amp_server_discord_role_set(self, context: commands.Context, server, role: discord.Role):
        self.logger.command(f'{context.author.name} used Database Server Discord Role')

        amp_server = await self.uBot._serverCheck(context, server, False)
        if amp_server:
            self.DB.GetServer(amp_server.InstanceID).Discord_Role = role.id
            amp_server._setDBattr()  # This will update the AMPInstance Attributes
            await context.send(i18n.t('messages.amp_server.role.success', server_name=amp_server.InstanceName, role_name=role.name), ephemeral=True, delete_after=self._client.Message_Timeout)

    @amp_server_settings.command(name='prefix', description=i18n.t('commands.server.settings.prefix.description'))
    @utils_permissions.role_check()
    @app_commands.autocomplete(server=utils_discord.autocomplete_servers)
    async def amp_server_discord_prefix_set(self, context: commands.Context, server, server_prefix: str):
        self.logger.command(f'{context.author.name} used Database Server Discord Chat Prefix')

        amp_server = await self.uBot._serverCheck(context, server, False)
        if amp_server:
            self.DB.GetServer(amp_server.InstanceID).Discord_Chat_prefix = server_prefix
            amp_server._setDBattr()  # This will update the AMPInstance Attributes
            await context.send(i18n.t('messages.amp_server.prefix.success', server_name=amp_server.InstanceName, server_prefix=server_prefix), ephemeral=True, delete_after=self._client.Message_Timeout)

    @amp_server_settings.command(name='hidden', description=i18n.t('commands.server.settings.hidden.description'))
    @utils_permissions.role_check()
    @app_commands.autocomplete(server=utils_discord.autocomplete_servers)
    @app_commands.choices(flag=[Choice(name=i18n.t('common.bool.true'), value=1), Choice(name=i18n.t('common.bool.false'), value=0)])
    async def amp_server_hidden(self, context: commands.Context, server, flag: Choice[int]):
        self.logger.command(f'{context.author.name} used Database Server Hidden')

        amp_server = await self.uBot._serverCheck(context, server, False)
        if amp_server:
            self.DB.GetServer(InstanceID=amp_server.InstanceID).Hidden = flag.value
            amp_server._setDBattr()  # This will update the AMPConsole Attributes
            shown_state = i18n.t('messages.amp_server.hidden.hidden_state') if flag.value == 1 else i18n.t('messages.amp_server.hidden.shown_state')
            return await context.send(i18n.t('messages.amp_server.hidden.success', server_name=amp_server.InstanceName, state=shown_state), ephemeral=True, delete_after=self._client.Message_Timeout)

# This section is AMP Server Console Specific Settings -------------------------------------------------------------------------------------------------------------------------------------------------
    @server.group(name='console', description=i18n.t('commands.server.console.description'))
    @utils_permissions.role_check()
    async def amp_server_console_settings(self, context: commands.Context):
        if context.invoked_subcommand is None:
            await context.send(i18n.t('common.invalid_command'), ephemeral=True, delete_after=self._client.Message_Timeout)

    @amp_server_console_settings.command(name='channel', description=i18n.t('commands.server.console.channel.description'))
    @utils_permissions.role_check()
    @app_commands.autocomplete(server=utils_discord.autocomplete_servers)
    async def amp_server_console_channel(self, context: commands.Context, server, channel: discord.abc.GuildChannel | None):
        self.logger.command(f'{context.author.name} used Database Server Console Channel')

        amp_server = await self.uBot._serverCheck(context, server, False)
        if amp_server:
            if isinstance(channel, discord.abc.GuildChannel):
                self.DB.GetServer(InstanceID=amp_server.InstanceID).Discord_Console_Channel = channel.id
            else:
                self.DB.GetServer(InstanceID=amp_server.InstanceID).Discord_Console_Channel = channel

            amp_server._setDBattr()  # This will update the AMPConsole Attribute
            channel_mention = channel.mention if channel is not None else i18n.t('common.embed.not_set')
            await context.send(i18n.t('messages.amp_server.console.channel_set', server_name=amp_server.InstanceName, channel_mention=channel_mention), ephemeral=True, delete_after=self._client.Message_Timeout)

    @amp_server_console_settings.command(name='filter', description=i18n.t('commands.server.console.filter.description'))
    @utils_permissions.role_check()
    @app_commands.autocomplete(server=utils_discord.autocomplete_servers)
    @app_commands.choices(flag=[Choice(name=i18n.t('common.bool.true'), value=1), Choice(name=i18n.t('common.bool.false'), value=0)])
    @app_commands.choices(filter_type=[
        Choice(name=i18n.t('commands.server.console.filter.params.filter_type.choices.0'), value=0),
        Choice(name=i18n.t('commands.server.console.filter.params.filter_type.choices.1'), value=1),
    ])
    async def amp_server_console_filter(self, context: commands.Context, server, flag: Choice[int], filter_type: Choice[int]):
        self.logger.command(f'{context.author.name} used Database Server Console Filtered True...')

        amp_server = await self.uBot._serverCheck(context, server, False)
        if amp_server:
            db_server = self.DB.GetServer(InstanceID=amp_server.InstanceID)
            db_server.Console_Filtered = flag.value
            db_server.Console_Filtered_Type = filter_type.value
            amp_server._setDBattr()  # This will update the AMPConsole Attributes
            return await context.send(i18n.t('messages.amp_server.console.filter_set', server_name=amp_server.InstanceName, flag_name=flag.name, filter_type_name=filter_type.name), ephemeral=True, delete_after=self._client.Message_Timeout)

# This section is AMP Server Chat Specific Settings -------------------------------------------------------------------------------------------------------------------------------------------------
    @server.group(name='chat', description=i18n.t('commands.server.chat.description'))
    @utils_permissions.role_check()
    async def amp_server_chat_settings(self, context: commands.Context):
        if context.invoked_subcommand is None:
            await context.send(i18n.t('common.invalid_command'), ephemeral=True, delete_after=self._client.Message_Timeout)

    @amp_server_chat_settings.command(name='channel', description=i18n.t('commands.server.chat.channel.description'))
    @utils_permissions.role_check()
    @app_commands.autocomplete(server=utils_discord.autocomplete_servers)
    async def amp_server_chat_channel(self, context: commands.Context, server, channel: discord.abc.GuildChannel):
        self.logger.command(f'{context.author.name} used Database Server Chat Channel')

        amp_server = await self.uBot._serverCheck(context, server, False)
        if amp_server:
            if isinstance(channel, discord.abc.GuildChannel):
                self.DB.GetServer(amp_server.InstanceID).Discord_Chat_Channel = channel.id
            else:
                self.DB.GetServer(amp_server.InstanceID).Discord_Chat_Channel = channel

            amp_server._setDBattr()  # This will update the AMPInstance Attributes
            channel_mention = channel.mention if channel is not None else i18n.t('common.embed.not_set')
            await context.send(i18n.t('messages.amp_server.chat.channel_set', server_name=amp_server.InstanceName, channel_mention=channel_mention), ephemeral=True, delete_after=self._client.Message_Timeout)

# This section is AMP Server Event Specific Settings -------------------------------------------------------------------------------------------------------------------------------------------------
    @server.group(name='event', description=i18n.t('commands.server.event.description'))
    @utils_permissions.role_check()
    async def amp_server_event_settings(self, context: commands.Context):
        if context.invoked_subcommand is None:
            await context.send(i18n.t('common.invalid_command'), ephemeral=True, delete_after=self._client.Message_Timeout)

    @amp_server_event_settings.command(name='channel', description=i18n.t('commands.server.event.channel.description'))
    @utils_permissions.role_check()
    @app_commands.autocomplete(server=utils_discord.autocomplete_servers)
    async def amp_server_event_channel_set(self, context: commands.Context, server, channel: discord.abc.GuildChannel):
        self.logger.command(f'{context.author.name} used Database Server Event Channel')

        amp_server = await self.uBot._serverCheck(context, server, False)
        if amp_server:
            if isinstance(channel, discord.abc.GuildChannel):
                self.DB.GetServer(amp_server.InstanceID).Discord_Event_Channel = channel.id
            else:
                self.DB.GetServer(amp_server.InstanceID).Discord_Event_Channel = channel

            amp_server._setDBattr()  # This will update the AMPInstance Attributes
            channel_mention = channel.mention if channel is not None else i18n.t('common.embed.not_set')
            await context.send(i18n.t('messages.amp_server.event.channel_set', server_name=amp_server.InstanceName, channel_mention=channel_mention), ephemeral=True, delete_after=self._client.Message_Timeout)

# This section is AMP Server Regex Specific Settings ------------------------------------------------------------------------------------------------------------------------------
    @server.group(name='regex', description=i18n.t('commands.server.regex.description'))
    @utils_permissions.role_check()
    async def server_regex_settings(self, context: commands.Context):
        if context.invoked_subcommand is None:
            await context.send(i18n.t('common.invalid_command'), ephemeral=True, delete_after=self._client.Message_Timeout)

    @server_regex_settings.command(name='add', description=i18n.t('commands.server.regex.add.description'))
    @utils_permissions.role_check()
    @app_commands.autocomplete(server=utils_discord.autocomplete_servers)
    @app_commands.autocomplete(name=autocomplete_regex)
    async def server_regex_add(self, context: commands.Context, server, name: str):
        self.logger.command(f'{context.author.name} used Server Regex Pattern Add')

        amp_server = self.uBot.serverparse(server, context, context.guild.id)
        db_server = self.DB.GetServer(InstanceID=server)
        if db_server != None:
            if db_server.AddServerRegexPattern(Name=name):
                regex = self.DB.GetRegexPattern(Name=name)
                if regex:
                    if regex['Type'] == 0:
                        pattern_type = i18n.t('messages.regex.pattern_type_console')
                    if regex['Type'] == 1:
                        pattern_type = i18n.t('messages.regex.pattern_type_events')

                    await context.send(i18n.t('messages.amp_server.regex.add.success', name=name, server_name=amp_server.InstanceName, pattern_name=regex["Name"], pattern_type=pattern_type, pattern=regex["Pattern"]), ephemeral=True, delete_after=self._client.Message_Timeout)
            else:
                await context.send(i18n.t('messages.amp_server.regex.add.duplicate', name=name, server_name=amp_server.InstanceName), ephemeral=True, delete_after=self._client.Message_Timeout)

    @server_regex_settings.command(name='delete', description=i18n.t('commands.server.regex.delete.description'))
    @utils_permissions.role_check()
    @app_commands.autocomplete(server=utils_discord.autocomplete_servers)
    @app_commands.autocomplete(name=autocomplete_server_regex)
    async def server_regex_delete(self, context: commands.Context, server: str, name: str):
        self.logger.command(f'{context.author.name} used Server Regex Pattern Delete.')

        amp_server = self.uBot.serverparse(server, context, context.guild.id)
        db_server = self.DB.GetServer(InstanceID=server)
        if db_server != None:
            if name != 'None':
                if db_server.DelServerRegexPattern(Name=name):
                    regex = self.DB.GetRegexPattern(Name=name)
                    if regex['Type'] == 0:
                        pattern_type = i18n.t('messages.regex.pattern_type_console')
                    if regex['Type'] == 1:
                        pattern_type = i18n.t('messages.regex.pattern_type_events')
                    await context.send(i18n.t('messages.amp_server.regex.delete.success', name=name, server_name=amp_server.InstanceName, pattern_name=regex["Name"], pattern_type=pattern_type, pattern=regex["Pattern"]), ephemeral=True, delete_after=self._client.Message_Timeout)
            else:
                await context.send(i18n.t('messages.amp_server.regex.delete.duplicate', name=name, server_name=amp_server.InstanceName), ephemeral=True, delete_after=self._client.Message_Timeout)

    @server_regex_settings.command(name='list', description=i18n.t('commands.server.regex.list.description'))
    @utils_permissions.role_check()
    @app_commands.autocomplete(server=utils_discord.autocomplete_servers)
    async def server_regex_list(self, context: commands.Context, server: str):
        self.logger.command(f'{context.author.name} used Server Regex List')

        db_server = self.DB.GetServer(InstanceID=server)
        if db_server != None:
            regex_patterns = db_server.GetServerRegexPatterns()
        if not regex_patterns:
            return await context.send(content=i18n.t('messages.regex.list.empty'), ephemeral=True, delete_after=self._client.Message_Timeout)

        embed_field = 0
        embed_list = []
        embed = discord.Embed(title=i18n.t('embeds.regex.title'))
        for pattern in regex_patterns:
            embed_field += 1
            if regex_patterns[pattern]['Type'] == 0:
                pattern_type = i18n.t('messages.regex.pattern_type_console')
            if regex_patterns[pattern]['Type'] == 1:
                pattern_type = i18n.t('messages.regex.pattern_type_events')

            embed.add_field(name=i18n.t('embeds.regex.field_name', name=regex_patterns[pattern]['Name'], pattern_type=pattern_type), value=regex_patterns[pattern]['Pattern'], inline=False)

            if embed_field >= 25:
                embed_list.append(embed)
                embed = discord.Embed(title=i18n.t('embeds.regex.title'))
                embed_field = 1
                continue

            if embed_field >= len(regex_patterns):
                embed_list.append(embed)
                break

        await context.send(embeds=embed_list, ephemeral=True, delete_after=self._client.Message_Timeout)


async def setup(client):
    await client.add_cog(AMP_Server(client))
