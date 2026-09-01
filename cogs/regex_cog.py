# Copyright (C) 2021-2022 Katelynn Cadwallader
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations
import discord
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import commands
import os
import logging
import re
import traceback

from core import utils
from core import utils_permissions
from core import AMP_Handler
from core import DB as DB
from core import i18n

# This is used to force cog order to prevent missing methods.
Dependencies = ["bot_cog.py"]


class Regex(commands.Cog):
    def __init__(self, client: discord.Client):
        self._client = client
        self.name = os.path.basename(__file__)
        self.logger = logging.getLogger()  # Point all print/logging statments here!

        self.AMPHandler = AMP_Handler.getAMPHandler()
        self.AMP = self.AMPHandler.AMP  # Main AMP object
        self.AMPInstances = self.AMPHandler.AMP_Instances  # Main AMP Instance Dictionary

        # use DBHandler for all DB related needs.
        self.DBHandler = DB.getDBHandler()
        self.DB = self.DBHandler.DB  # Main Database object

        # utils.botUtils provide access to utility functions such as serverparse,role_parse,channel_parse,user_parse.
        self.uBot = utils.botUtils(client)

        # Leave this commented out unless you need to create a sub-command.
        self.uBot.sub_command_handler('bot', self.regex_pattern)  # This is used to add a sub command(self,parent_command,sub_command)

        self.logger.info(f'**SUCCESS** Loading Module **{self.name.title()}**')

    async def autocomplete_regex(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        """Autocomplete for Regex Pattern Names"""
        choice_list = []
        regex_patterns = self.DB.GetAllRegexPatterns()

        for regex in regex_patterns:
            choice_list.append(regex_patterns[regex]["Name"])
        return [app_commands.Choice(name=choice, value=choice) for choice in choice_list if current.lower() in choice.lower()][:25]

    @commands.hybrid_group(name='regex_pattern', description=i18n.t('commands.bot.regex_pattern.description'))
    @utils_permissions.role_check()
    async def regex_pattern(self, context: commands.Context):
        if context.invoked_subcommand is None:
            await context.send(i18n.t('common.try_again'), ephemeral=True, delete_after=self._client.Message_Timeout)

    @regex_pattern.command(name='add', description=i18n.t('commands.bot.regex_pattern.add.description'))
    @utils_permissions.role_check()
    @app_commands.describe(name=i18n.t('commands.bot.regex_pattern.add.params.name.description'))
    @app_commands.describe(filter_type=i18n.t('commands.bot.regex_pattern.add.params.filter_type.description'))
    @app_commands.describe(pattern=i18n.t('commands.bot.regex_pattern.add.params.pattern.description'))
    @app_commands.choices(filter_type=[
        Choice(name=i18n.t('commands.bot.regex_pattern.add.params.filter_type.choices.0'), value=0),
        Choice(name=i18n.t('commands.bot.regex_pattern.add.params.filter_type.choices.1'), value=1),
    ])
    async def regex_pattern_add(self, context: commands.Context, name: str, filter_type: Choice[int], pattern: str):
        self.logger.command(f'{context.author.name} used Regex Pattern Add')
        try:
            re.compile(pattern=pattern)
        except re.error as e:
            self.logger.error(e)
            return await context.send(content=i18n.t('messages.regex.invalid_pattern', pattern=pattern), ephemeral=True, delete_after=self._client.Message_Timeout)

        if self.DB.AddRegexPattern(Name=name, Pattern=pattern, Type=filter_type.value):
            await context.send(content=i18n.t('messages.regex.add.success', name=name, filter_name=filter_type.name, pattern=pattern), ephemeral=True, delete_after=self._client.Message_Timeout)
        else:
            await context.send(content=i18n.t('messages.regex.add.duplicate_name', name=name), ephemeral=True, delete_after=self._client.Message_Timeout)

    @regex_pattern.command(name='delete', description=i18n.t('commands.bot.regex_pattern.delete.description'))
    @utils_permissions.role_check()
    @app_commands.autocomplete(name=autocomplete_regex)
    @app_commands.describe(name=i18n.t('commands.bot.regex_pattern.delete.params.name.description'))
    async def regex_pattern_remove(self, context: commands.Context, name: str):
        self.logger.command(f'{context.author.name} used Regex Pattern Delete')
        if self.DB.DelRegexPattern(Name=name):
            await context.send(content=i18n.t('messages.regex.delete.success', name=name), ephemeral=True, delete_after=self._client.Message_Timeout)
        else:
            await context.send(content=i18n.t('messages.regex.delete.not_found', name=name), ephemeral=True, delete_after=self._client.Message_Timeout)

    @regex_pattern.command(name='update', description=i18n.t('commands.bot.regex_pattern.update.description'))
    @utils_permissions.role_check()
    @app_commands.autocomplete(name=autocomplete_regex)
    @app_commands.choices(filter_type=[
        Choice(name=i18n.t('commands.bot.regex_pattern.update.params.filter_type.choices.0'), value=0),
        Choice(name=i18n.t('commands.bot.regex_pattern.update.params.filter_type.choices.1'), value=1),
    ])
    @app_commands.describe(name=i18n.t('commands.bot.regex_pattern.update.params.name.description'))
    @app_commands.describe(new_name=i18n.t('commands.bot.regex_pattern.update.params.new_name.description'))
    @app_commands.describe(filter_type=i18n.t('commands.bot.regex_pattern.update.params.filter_type.description'))
    @app_commands.describe(pattern=i18n.t('commands.bot.regex_pattern.update.params.pattern.description'))
    async def regex_pattern_update(self, context: commands.Context, name: str, new_name: str | None = None, filter_type: Choice[int] = None, pattern: str | None = None):
        self.logger.command(f'{context.author.name} used Regex Pattern Update')

        if pattern != None:
            try:
                re.compile(pattern=pattern)
            except re.error:
                self.logger.error(f'Regex Error: {traceback.format_exc()}')
                return await context.send(content=i18n.t('messages.regex.invalid_pattern', pattern=pattern), ephemeral=True, delete_after=self._client.Message_Timeout)

        filter_value = None
        filter_name = None
        content_str = ''
        if filter_type != None:
            filter_value = filter_type.value
            filter_name = filter_type.name
            content_str = i18n.t('messages.regex.update.type_suffix', filter_name=filter_name)

        if self.DB.UpdateRegexPattern(Pattern=pattern, Type=filter_value, Pattern_Name=name, Name=new_name):
            if new_name != None:
                name = new_name

            await context.send(content=i18n.t('messages.regex.update.success', name=name, content_str=content_str, pattern=pattern), ephemeral=True, delete_after=self._client.Message_Timeout)
        else:
            await context.send(content=i18n.t('messages.regex.update.not_found', name=name), ephemeral=True, delete_after=self._client.Message_Timeout)

    @regex_pattern.command(name='list', description=i18n.t('commands.bot.regex_pattern.list.description'))
    @utils_permissions.role_check()
    async def regex_pattern_list(self, context: commands.Context):
        self.logger.command(f'{context.author.name} used Regex Pattern List')
        regex_patterns = self.DB.GetAllRegexPatterns()
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
    await client.add_cog(Regex(client))
