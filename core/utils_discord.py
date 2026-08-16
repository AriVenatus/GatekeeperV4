# Copyright (C) 2021-2022 Katelynn Cadwallader
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations
import logging
from typing import Union

import discord
from discord import app_commands
from discord.ext import commands

from core import AMP_Handler
from core import utils_permissions

# GLOBAL VARS# DO NOT EDIT THESE! ONLY READ THEM
__AMP_Handler = AMP_Handler.getAMPHandler()


async def autocomplete_servers(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    """Autocomplete for AMP Instance Names"""
    choice_list = __AMP_Handler.get_AMP_instance_names()
    if await utils_permissions.async_rolecheck(interaction, perm_node='staff') == True:
        return [app_commands.Choice(name=f"{value} | ID: {key}", value=key)for key, value in choice_list.items() if current.lower().lstrip() in value.lower()][:25]
    else:
        return [app_commands.Choice(name=f"{value}", value=key)for key, value in choice_list.items() if current.lower().lstrip() in value.lower()][:25]


async def autocomplete_servers_public(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    """Autocomplete for AMP Instance Names"""
    choice_list = __AMP_Handler.get_AMP_instance_names(public=True)
    return [app_commands.Choice(name=f"{value}", value=key)for key, value in choice_list.items() if current.lower().lstrip() in value.lower()][:25]


class DiscordPlumbingMixin:
    """Discord entity-parsing/command-tree helpers, mixed into `botUtils` (see `core/utils.py`).

    Relies on `self.logger`, `self._client` and `self.AMPHandler` being set by `botUtils.__init__`.
    """

    def role_parse(self, parameter: str, context: commands.Context, guild_id: int) -> Union[discord.Role, None]:
        """This is the bot utils Role Parse Function
        It handles finding the specificed Discord `<role>` in multiple different formats.
        They can contain single quotes, double quotes and underscores. (" ",' ',_)
        returns `<role>` object if True, else returns `None`
        **Note** Use context.guild.id"""
        self.logger.dev('Role Parse Called...')

        guild = self._client.get_guild(guild_id)
        role_list = guild.roles

        # Role ID catch
        if parameter.isnumeric():
            role = guild.get_role(int(parameter))
            self.logger.debug(f'Found the Discord Role {role}')
            return role
        else:
            # This allows a user to pass in a role in quotes double or single
            if parameter.find("'") != -1 or parameter.find('"'):
                parameter = parameter.replace('"', '')
                parameter = parameter.replace("'", '')

            # If a user provides a role name; this will check if it exists and return the ID
            for role in role_list:
                if role.name.lower() == parameter.lower():
                    self.logger.debug(f'Found the Discord Role {role}')
                    return role

                # This is to handle roles with spaces
                parameter.replace('_', ' ')
                if role.name.lower() == parameter.lower():
                    self.logger.debug(f'Found the Discord Role {role}')
                    return role

            # await context.reply(f'Unable to find the Discord Role: {parameter}')
            return None

    def channel_parse(self, parameter: Union[str, int], context: commands.Context = None, guild_id: int | None = None) -> Union[discord.TextChannel, None]:
        """This is the bot utils Channel Parse Function
        It handles finding the specificed Discord `<channel>` in multiple different formats, either numeric or alphanumeric.
        returns `<channel>` object if True, else returns `None`
        **Note** Use context.guild.id"""
        self.logger.dev('Channel Parse Called...')

        if guild_id == None:
            channel = self._client.get_channel(parameter)
            self.logger.debug(f'Found the Discord Channel {channel}')
            return channel

        guild = self._client.get_guild(guild_id)
        channel_list = guild.channels
        if type(parameter) == int:
            channel = guild.get_channel(parameter)
            self.logger.debug(f'Found the Discord Channel {channel}')
            return channel
        else:
            category_clear = parameter.find('->')
            if category_clear != -1:
                parameter = parameter[(category_clear + 2):].strip()

            for channel in channel_list:
                if channel.name == parameter:
                    self.logger.debug(f'Found the Discord Channel {channel}')
                    return channel
            else:
                self.logger.error('Unable to Find the Discord Channel')
                # await context.reply(f'Unable to find the Discord Channel: {parameter}')
                return None

    def user_parse(self, parameter: str, context: commands.Context = None, guild_id: int | None = None) -> Union[discord.Member, None]:
        """This is the bot utils User Parse Function
        It handles finding the specificed Discord `<user>` in multiple different formats, either numeric or alphanumeric.
        It also supports '@', '#0000' and partial display name searching for user indentification (eg. k8thekat#1357)
        returns `<user>` object if True, else returns `None`
        **Note** Use context.guild.id"""
        self.logger.dev('User Parse Called...')

        # Without a guild_ID its harder to parse members.
        if guild_id == None:
            cur_member = self._client.get_user(int(parameter))
            self.logger.dev(f'Found the Discord Member {cur_member.display_name}')
            return cur_member

        guild = self._client.get_guild(guild_id)
        # Discord ID catch
        if parameter.isnumeric():
            cur_member = guild.get_member(int(parameter))
            self.logger.dev(f'Found the Discord Member {cur_member.display_name}')
            return cur_member

        # Profile Name Catch
        if parameter.find('#') != -1:
            cur_member = guild.get_member_named(parameter)
            self.logger.dev(f'Found the Discord Member {cur_member.display_name}')
            return cur_member

        # Using @ at user and stripping
        if parameter.startswith('<@!') and parameter.endswith('>'):
            user_discordid = parameter[3:-1]
            cur_member = guild.get_member(int(user_discordid))
            self.logger.dev(f'Found the Discord Member {cur_member.display_name}')
            return cur_member

        # DiscordName/IGN Catch(DB Get user can look this up)
        cur_member = guild.get_member_named(parameter)
        if cur_member != None:
            self.logger.dev(f'Found the Discord Member {cur_member.display_name}')
            return cur_member

        # Display Name Lookup
        else:
            cur_member = None
            for member in guild.members:
                if member.display_name.lower().startswith(parameter.lower()) or (member.display_name.lower().find(parameter.lower()) != -1):
                    if cur_member != None:
                        self.logger.error(f'**ERROR** Found multiple Discord Members: {parameter}, Returning None')
                        return None

                    self.logger.dev(f'Found the Discord Member {member.display_name}')
                    cur_member = member
            return cur_member

    def serverparse(self, instanceID=str, context: commands.Context = None, guild_id: int | None = None) -> Union[AMP_Handler.AMP.AMPInstance, None]:
        """This is the botUtils Server Parse function.
        **Note** Use context.guild.id
        Returns `AMPInstance[server] <object>`"""
        self.logger.dev('Bot Utility Server Parse')
        cur_server = None
        for key, value in list(self.AMPHandler.AMP_Instances.items()):
            if key == instanceID:
                cur_server = value
                self.logger.dev(f'Selected Server is {value} - InstanceID: {key}')
                break

        return cur_server  # AMP instance object

    def sub_command_handler(self, command: str, sub_command):
        """This will get the `Parent` command and then add a `Sub` command to said `Parent` command."""
        parent_command = self._client.get_command(command)
        try:
            parent_command.add_command(sub_command)
            self.logger.dev(f'Added {command} Parent Command: {parent_command}')
        except discord.app_commands.errors.CommandAlreadyRegistered:
            return
        except Exception as e:
            self.logger.error(f'We encountered an error in `sub_command_handler` - {e}')

    def sub_group_command_handler(self, group: str, command):
        """Gets the `Command Group` and adds the `command` to said `Group`"""
        parent_group = self._client.get_command(group)
        if type(parent_group) == discord.ext.commands.hybrid.HybridGroup:
            try:
                parent_group.add_command(command)
                self.logger.dev(f'Added {group} to Parent Command Group: {parent_group}')
            except discord.app_commands.errors.CommandAlreadyRegistered:
                return
            except Exception as e:
                self.logger.error(f'We encountered an error in `sub_group_command_handler` - {e}')

    def _remove_commands(self, parent_group: str, command: str):
        """This will remove a command from a group"""
        # Should call some form of sync command after; but I do not want to auto sync. Regardless the command tree will be cleaned up.
        group = self._client.get_command(parent_group)
        # the Group command could not exists on first startup; as the client has not been sync'd.
        if group != None:
            self.logger.dev(f'Removed {command} from {parent_group}')
            group.remove_command(command)

    async def _serverCheck(self, context: commands.Context, server, online_only: bool = True) -> Union[AMP_Handler.AMP.AMPInstance, bool]:
        """Verifies if the AMP Server exists and if its Instance is running and its ADS is Running"""
        amp_server = self.serverparse(server, context, context.guild.id)

        if amp_server == None:
            if online_only == False:
                return amp_server

            await context.send('Well this is awkward, it appears that server could not be found.', ephemeral=True, delete_after=self._client.Message_Timeout)
            return False

        if online_only == False:
            return amp_server

        if amp_server.Running and amp_server._ADScheck():
            return amp_server

        await context.send(f'Well this is awkward, it appears the **{amp_server.FriendlyName if amp_server.FriendlyName != None else amp_server.InstanceName}** is `Offline`.', ephemeral=True, delete_after=self._client.Message_Timeout)
        return False
