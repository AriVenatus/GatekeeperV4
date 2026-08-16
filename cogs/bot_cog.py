# Copyright (C) 2021-2022 Katelynn Cadwallader
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations
import os
import sys
import logging
import traceback
from typing import Union

import discord
from discord import app_commands
from discord.ext import commands
from discord.app_commands import Choice

from core import utils
from core import utils_permissions
from core import utils_embeds
from core import AMP_Handler
from core import DB
from core import i18n
from core.discordBot import Version

# This is used to force cog order to prevent missing methods.
Dependencies = None


class Bot(commands.Cog):
    def __init__(self, client: discord.Client):
        self._client = client
        self.name = os.path.basename(__file__)

        self.logger = logging.getLogger()

        self.AMPHandler = AMP_Handler.getAMPHandler()
        self.DBHandler = DB.getDBHandler()
        self.DBConfig = self.DBHandler.DBConfig

        self.uBot = utils.botUtils(client)
        self.eBot = utils_embeds.botEmbeds(client)

        self.logger.info(f'**SUCCESS** Initializing {self.name.title().replace("Bot_Cog","Bot")}')

    async def autocomplete_loadedcogs(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        """Cog Autocomplete template."""
        choice_list = []
        for key in self._client.cogs:
            if key not in choice_list:
                choice_list.append(key)
        return [app_commands.Choice(name=choice, value=choice) for choice in choice_list if current.lower() in choice.lower()]

    @commands.hybrid_group(name='bot', description=i18n.t('commands.bot.description'))
    @utils_permissions.role_check()
    async def main_bot(self, context: commands.Context):
        if context.invoked_subcommand is None:
            await context.send(i18n.t('common.invalid_command'), ephemeral=True, delete_after=self._client.Message_Timeout)

    @main_bot.command(name='moderator', description=i18n.t('commands.bot.moderator.description'))
    @commands.has_guild_permissions(administrator=True)
    async def moderator(self, context: commands.Context, role: discord.Role):
        self.logger.command(f'{context.author.name} used Bot Moderator...')

        self.DBConfig.SetSetting('Moderator_role_id', role.id)
        await context.send(i18n.t('messages.bot.moderator.success', role_name=role.name), ephemeral=True)

    @main_bot.command(name='permissions', description=i18n.t('commands.bot.permissions.description'))
    @commands.has_guild_permissions(administrator=True)
    @app_commands.choices(permission=[
        Choice(name=i18n.t('commands.bot.permissions.params.permission.choices.0'), value=0),
        Choice(name=i18n.t('commands.bot.permissions.params.permission.choices.1'), value=1),
    ])
    async def permissions(self, context: commands.Context, permission: Choice[int]):
        self.logger.command(f'{context.author.name} used Bot Permissions...')

        # If we set to 0; we are using `Default` Permissions and need to unload the cog and commands related to custom permissions.
        if permission.value == 0:
            await context.send(i18n.t('messages.bot.permissions.selected_default'), ephemeral=True, delete_after=self._client.Message_Timeout)
            parent_command = self._client.get_command('user')
            parent_command.remove_command('role')
            if 'cogs.permissions_cog' in self._client.extensions:
                await self._client.unload_extension('cogs.permissions_cog')

        # If we set to 1; we are using `Custom` Permissions.
        elif permission.value == 1:
            await context.send(i18n.t('messages.bot.permissions.selected_custom'), ephemeral=True, delete_after=self._client.Message_Timeout)
            await context.send(i18n.t('messages.bot.permissions.visit_docs'), ephemeral=True, delete_after=self._client.Message_Timeout)
            # This validates the `bot_perms.json` file.
            if not await self._client.permissions_update():
                return await context.send(i18n.t('messages.bot.permissions.load_error'), ephemeral=True, delete_after=self._client.Message_Timeout)

        # Depending on which permissions; this will sync the updated commands available.
        self._client.tree.copy_global_to(guild=self._client.get_guild(context.guild.id))
        await self._client.tree.sync(guild=self._client.get_guild(context.guild.id))
        self.DBConfig.Permissions = permission.name
        await context.send(i18n.t('messages.bot.permissions.finished', permission_name=permission.name), ephemeral=True, delete_after=self._client.Message_Timeout)

    @main_bot.command(name='language', description=i18n.t('commands.bot.language.description'))
    @commands.has_guild_permissions(administrator=True)
    @app_commands.describe(language=i18n.t('commands.bot.language.params.language.description'))
    @app_commands.choices(language=[Choice(name='English', value='en'), Choice(name='Deutsch', value='de')])
    async def language(self, context: commands.Context, language: Choice[str]):
        self.logger.command(f'{context.author.name} used Bot Language...')
        # Walking every command in the tree plus a tree.sync() round trip can exceed Discord's 3s
        # interaction-ack window; mirrors the existing defer() precedent in utils_clear/utils_sync.
        await context.defer(ephemeral=True)

        i18n.set_language(language.value)
        updated, skipped = i18n.retranslate_command_tree(self._client)
        self.logger.info(f'i18n: retranslated {updated} fields to "{language.value}" ({skipped} fell back/skipped).')

        self._client.tree.copy_global_to(guild=self._client.get_guild(context.guild.id))
        await self._client.tree.sync(guild=self._client.get_guild(context.guild.id))

        await context.send(i18n.t('commands.bot.language.confirmation', language=language.name), ephemeral=True, delete_after=self._client.Message_Timeout)

    @main_bot.command(name='settings', description=i18n.t('commands.bot.settings.description'))
    @utils_permissions.role_check()
    async def settings(self, context: commands.Context):
        self.logger.command(f'{context.author.name} used Bot Settings...')
        await context.send(embed=self.eBot.bot_settings_embed(context), ephemeral=True, delete_after=(self._client.Message_Timeout * 3))  # Tripled the delay to help sort times.

    @main_bot.group(name='utils', description=i18n.t('commands.bot.utils.description'))
    @utils_permissions.role_check()
    async def utils_group(self, context: commands.Context):
        if context.invoked_subcommand is None:
            await context.send(i18n.t('common.invalid_command'), ephemeral=True, delete_after=self._client.Message_Timeout)

    @utils_group.command(name='clear', description=i18n.t('commands.bot.utils.clear.description'))
    @app_commands.choices(all=[Choice(name=i18n.t('common.bool.true'), value=1), Choice(name=i18n.t('common.bool.false'), value=0)])
    @app_commands.describe(all=i18n.t('commands.bot.utils.clear.params.all.description'))
    @app_commands.describe(channel=i18n.t('commands.bot.utils.clear.params.channel.description'))
    @utils_permissions.role_check()
    async def utils_clear(self, context: commands.Context, channel: discord.abc.GuildChannel = None, amount: app_commands.Range[int, 0, 100] = 50, all: Choice[int] = 0):
        self.logger.info(f'{context.author.name} used {context.command.name}...')
        self._client.context = context
        await context.defer()

        # Setting channel to the channel the command was run in as default.
        if channel == None:
            channel = context.channel

        if type(all) == Choice:
            all = all.value

        if all == 1:
            messages = await channel.purge(limit=amount, bulk=False)
        else:
            messages = await channel.purge(limit=amount, check=self._client.self_check, bulk=False)

        word = i18n.t_plural('common.messages_word', count=len(messages))
        return await channel.send(i18n.t('messages.bot.utils.clear.success', count=len(messages), word=word), delete_after=self._client.Message_Timeout)

    @utils_group.command(name='roleid', description=i18n.t('commands.bot.utils.roleid.description'))
    @utils_permissions.role_check()
    async def utils_roleid(self, context: commands.Context, role: discord.Role):
        self.logger.command(f'{context.author.name} used Bot Utils Role ID...')

        await context.send(i18n.t('messages.bot.utils.roleid.result', role_name=role.name, role_id=role.id), ephemeral=True, delete_after=self._client.Message_Timeout)

    @utils_group.command(name='channelid', description=i18n.t('commands.bot.utils.channelid.description'))
    @utils_permissions.role_check()
    async def utils_channelid(self, context: commands.Context, channel: discord.abc.GuildChannel):
        self.logger.command(f'{context.author.name} used Bot Utils Channel ID...')

        await context.send(i18n.t('messages.bot.utils.channelid.result', channel_name=channel.name, channel_id=channel.id), ephemeral=True, delete_after=self._client.Message_Timeout)

    @utils_group.command(name='userid', description=i18n.t('commands.bot.utils.userid.description'))
    @utils_permissions.role_check()
    async def utils_userid(self, context: commands.Context, user: Union[discord.User, discord.Member]):
        self.logger.command(f'{context.author.name} used Bot Utils User ID...')

        await context.send(i18n.t('messages.bot.utils.userid.result', user_name=user.name, display_name=user.display_name, user_id=user.id), ephemeral=True, delete_after=self._client.Message_Timeout)

    @utils_group.command(name='uuid', description=i18n.t('commands.bot.utils.uuid.description'))
    @utils_permissions.role_check()
    async def utils_uuid(self, context: commands.Context, mc_ign: str):
        self.logger.command(f'{context.author.name} used Bot Utils UUID...')

        await context.send(i18n.t('messages.bot.utils.uuid.result', mc_ign=mc_ign, uuid=self.uBot.name_to_uuid_MC(mc_ign)), ephemeral=True, delete_after=self._client.Message_Timeout)

    @utils_group.command(name='ping', description=i18n.t('commands.bot.utils.ping.description'))
    @utils_permissions.role_check()
    async def utils_ping(self, context: commands.Context):
        self.logger.command(f'{context.author.name} used Bot Ping...')

        await context.send(i18n.t('messages.bot.utils.ping.result', latency=round(self._client.latency * 1000)), ephemeral=True, delete_after=self._client.Message_Timeout)

    @utils_group.command(name='disconnect', description=i18n.t('commands.bot.utils.disconnect.description'))
    @utils_permissions.role_check()
    async def utils_disconnect(self, context: commands.Context):
        self.logger.command(f'{context.author.name} used Bot Stop Function...')

        await context.send(i18n.t('messages.bot.utils.disconnect.message'), ephemeral=True, delete_after=self._client.Message_Timeout)
        return await self._client.close()

    @utils_group.command(name='restart', description=i18n.t('commands.bot.utils.restart.description'))
    @utils_permissions.role_check()
    async def utils_restart(self, context: commands.Context):
        self.logger.command(f'{context.author.name} used Bot Restart Function...')

        import os
        import sys
        await context.send(i18n.t('messages.bot.utils.restart.message'), ephemeral=True, delete_after=self._client.Message_Timeout)
        sys.stdout.flush()
        os.execv(sys.executable, ['python3'] + sys.argv)

    @utils_group.command(name='status', description=i18n.t('commands.bot.utils.status.description'))
    @utils_permissions.role_check()
    async def utils_status(self, context: commands.Context):
        self.logger.command(f'{context.author.name} used Bot Status Function...')

        await context.send(i18n.t('messages.bot.utils.status.versions', discord_version=discord.__version__, python_version=sys.version), ephemeral=True, delete_after=self._client.Message_Timeout)
        await context.send(i18n.t('messages.bot.utils.status.bot_db_version', bot_version=Version, db_version=self.DBHandler.DB_Version), ephemeral=True, delete_after=self._client.Message_Timeout)
        await context.send(i18n.t('messages.bot.utils.status.connections', amp_connected=self.AMPHandler.SuccessfulConnection, db_connected=self.DBHandler.SuccessfulDatabase), ephemeral=True, delete_after=self._client.Message_Timeout)

    @utils_group.command(name='message_timeout', description=i18n.t('commands.bot.utils.message_timeout.description'))
    @utils_permissions.role_check()
    @app_commands.describe(time=i18n.t('commands.bot.utils.message_timeout.params.time.description'))
    async def utils_message_timeout(self, context: commands.Context, time: Union[None, int] = 60):
        self.logger.command(f'{context.author.name} used Bot Utils Message Timeout Function...')

        self.DBConfig.SetSetting('Message_Timeout', f'{time}')
        self._client.Message_Timeout = time

        content_str = i18n.t('messages.bot.utils.message_timeout.will_delete', time=time)
        if time == None:
            content_str = i18n.t('messages.bot.utils.message_timeout.will_not_delete')

        await context.send(content=i18n.t('messages.bot.utils.message_timeout.result', content_str=content_str), ephemeral=True, delete_after=self._client.Message_Timeout)

    @utils_group.command(name='sync', description=i18n.t('commands.bot.utils.sync.description'))
    @utils_permissions.role_check()
    @app_commands.choices(local=[Choice(name=i18n.t('common.bool.true'), value=1), Choice(name=i18n.t('common.bool.false'), value=0)])
    @app_commands.choices(reset=[Choice(name=i18n.t('common.bool.true'), value=1), Choice(name=i18n.t('common.bool.false'), value=0)])
    async def utils_sync(self, context: commands.Context, local: Choice[int] = True, reset: Choice[int] = False):
        self.logger.command(f'{context.author.name} used Bot Sync Function...')
        await context.defer()
        # This keeps our DB Guild_ID Current.
        if self._client.guild_id == None or context.guild.id != int(self._client.guild_id):
            self.DBConfig.SetSetting('Guild_ID', context.guild.id)

        if ((type(reset)) == bool and (reset == True)) or ((type(reset) == Choice) and (reset.value == 1)):
            if ((type(local) == bool) and (local == True)) or ((type(local)) == Choice and (local.value == 1)):
                # Local command tree reset
                self._client.tree.clear_commands(guild=context.guild)
                self.logger.command(f'Bot Commands Reset Locally and Sync\'d: {await self._client.tree.sync(guild=context.guild)}')
                return await context.send(i18n.t('messages.bot.utils.sync.reset_local'), ephemeral=True, delete_after=self._client.Message_Timeout)

            elif context.author.id == 144462063920611328:
                # Global command tree reset, limited by k8thekat discord ID
                self._client.tree.clear_commands(guild=None)
                self.logger.command(f'Bot Commands Reset Global and Sync\'d: {await self._client.tree.sync(guild=None)}')
                return await context.send(i18n.t('messages.bot.utils.sync.reset_global'), ephemeral=True, delete_after=self._client.Message_Timeout)
            else:
                return await context.send(i18n.t('messages.bot.utils.sync.no_permission'), ephemeral=True, delete_after=self._client.Message_Timeout)

        if ((type(local) == bool) and (local == True)) or ((type(local) == Choice) and (local.value == 1)):
            # Local command tree sync
            self._client.tree.copy_global_to(guild=context.guild)
            self.logger.command(f'Bot Commands Sync\'d Locally: {await self._client.tree.sync(guild=context.guild)}')
            return await context.send(i18n.t('messages.bot.utils.sync.local_success', guild_name=context.guild.name), ephemeral=True, delete_after=self._client.Message_Timeout)

        elif context.author.id == 144462063920611328:
            # Global command tree sync, limited by k8thekat discord ID
            self.logger.command(f'Bot Commands Sync\'d Globally: {await self._client.tree.sync(guild=None)}')
            await context.send(i18n.t('messages.bot.utils.sync.global_success'), ephemeral=True, delete_after=self._client.Message_Timeout)

    # Cog Specific Bot Commands --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    @main_bot.group(name='cog', description=i18n.t('commands.bot.cog.description'))
    @utils_permissions.role_check()
    async def cogs_group(self, context: commands.Context):
        if context.invoked_subcommand is None:
            await context.send(i18n.t('common.invalid_command'), ephemeral=True, delete_after=self._client.Message_Timeout)

    @cogs_group.command(name='load', description=i18n.t('commands.bot.cog.load.description'))
    @utils_permissions.role_check()
    async def cogs_load(self, context: commands.Context, cog: str):
        self.logger.command(f'{context.author.name} used Bot Cog Load Function...')

        try:
            await self._client.load_extension(name=cog)
        except Exception as e:
            await context.send(i18n.t('messages.bot.cog.load.error', cog=cog, traceback=traceback.format_exc()), ephemeral=True, delete_after=self._client.Message_Timeout)
        else:
            await context.send(i18n.t('messages.bot.cog.load.success', cog=cog), ephemeral=True, delete_after=self._client.Message_Timeout)

    @cogs_group.command(name='unload', description=i18n.t('commands.bot.cog.unload.description'))
    @utils_permissions.role_check()
    @app_commands.autocomplete(cog=autocomplete_loadedcogs)
    async def cogs_unload(self, context: commands.Context, cog: str):
        self.logger.command(f'{context.author.name} used Bot Cog Unload Function...')

        # Guard: this cog contains the `/bot` command group itself (incl. `bot cog load`, the only
        # way to bring it back without a process restart). Unloading it here would leave the bot
        # uncontrollable from Discord until someone restarts the process. Refuse and explain instead.
        if cog == self.qualified_name:
            await context.send(i18n.t('messages.bot.cog.unload.self_protected', cog=cog), ephemeral=True, delete_after=self._client.Message_Timeout)
            return

        try:
            my_cog = self._client.cogs[cog]
            await my_cog.cog_unload()
            # await client.unload_extension(name=cog)
        except Exception as e:
            await context.send(i18n.t('messages.bot.cog.unload.error', cog=cog, traceback=traceback.format_exc()), ephemeral=True, delete_after=self._client.Message_Timeout)
        else:
            await context.send(i18n.t('messages.bot.cog.unload.success', cog=cog), ephemeral=True, delete_after=self._client.Message_Timeout)

    @cogs_group.command(name='reload', description=i18n.t('commands.bot.cog.reload.description'))
    @utils_permissions.role_check()
    async def cogs_reload(self, context: commands.Context):
        self.logger.command(f'{context.author.name} used Bot Cog Reload Function...')

        # Guard: skip reloading this cog (it contains the live `/bot` group, including this very
        # command) as part of a bulk reload -- see the matching guard/comment in cogs_unload.
        # `core/loader.py`'s cog_auto_loader() excludes it the same way it already excludes
        # permissions_cog.py, just conditioned on `reload=True` since it must still be auto-loaded
        # normally at startup.
        await self._client.Handler.cog_auto_loader(reload=True)
        # One send, not two -- a hybrid command's second `context.send` becomes a separate
        # follow-up message, which reads as two disjoint replies to a single invocation.
        await context.send(
            f"{i18n.t('messages.bot.cog.reload.success')}\n{i18n.t('messages.bot.cog.reload.self_protected', cog=self.name)}",
            ephemeral=True, delete_after=self._client.Message_Timeout)


async def setup(client):
    await client.add_cog(Bot(client))
