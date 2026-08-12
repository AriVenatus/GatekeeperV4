# Copyright (C) 2021-2022 Katelynn Cadwallader
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations
import sys
import logging
import traceback

import discord
from discord import app_commands
from discord.ext import commands, tasks
from discord.app_commands import Choice

# Custom scripts
from core import utils
from core import utils_embeds
from core import utils_ui
from core import AMP_Handler
from core import DB
from core import i18n
from typing import Union

Version = 'beta-4.7.5'

# Eager init: loads locales/en.json + locales/de.json and reads DBConfig.GetSetting('Language').
# Must happen before any i18n.t(...) call below in this file (e.g. the `bot_language` command's
# own decorators), and before setup_hook() triggers loader.Handler's cog imports further down --
# those cogs call i18n.t(...) at their own module-import time.
i18n.getI18nHandler()


class Gatekeeper(commands.Bot):
    def __init__(self, Version: str):
        self.logger = logging.getLogger()
        self.DBHandler = DB.getDBHandler()
        self.DB = DB.getDBHandler().DB
        self.DBConfig = self.DBHandler.DBConfig

        self.guild_id = None
        if self.DBConfig.GetSetting('Guild_ID') != None:
            self.guild_id = int(self.DBConfig.GetSetting('Guild_ID'))

        self.Bot_Version = self.DBConfig.GetSetting('Bot_Version')
        if self.Bot_Version == None:
            self.DBConfig.SetSetting('Bot_Version', Version)

        self.AMPHandler = AMP_Handler.getAMPHandler()
        self.AMP = AMP_Handler.getAMPHandler().AMP

        # Discord Specific
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        self.prefix = '$'
        super().__init__(intents=intents, command_prefix=self.prefix)
        self.Message_Timeout = self.DBConfig.Message_timeout
        self.uBot = utils.botUtils(client=self)
        self.uiBot = utils_ui
        self.eBot = utils_embeds.botEmbeds(client=self)

    async def setup_hook(self):
        if self.Bot_Version != Version:
            self.update_loop.start()

        from core import loader
        self.Handler = loader.Handler(self)
        await self.Handler.module_auto_loader()
        await self.Handler.cog_auto_loader()

        # This Creates the Bot_perms Object and validates the File. Also Adds the Command.
        if self.DBConfig.GetSetting('Permissions') == 'Custom':
            await self.permissions_update()

    def self_check(self, message: discord.Message) -> bool:
        return message.author == client.user

    async def on_command_error(self, context: commands.Context, exception: discord.errors) -> None:
        self.logger.error(f'We ran into an issue. {exception}')
        traceback.print_exception(exception)
        traceback.print_exc()

    async def on_ready(self):
        self.logger.info('Are you the Keymaster?...I am the Gatekeeper')

    @tasks.loop(seconds=30)
    async def update_loop(self):
        self.logger.warn(f'Waiting to Update Bot Version to {Version}...')
        await client.wait_until_ready()
        self.logger.warn(f'Currently Updating Bot Version to {Version}...')
        self.DBConfig.SetSetting('Bot_Version', Version)
        if self.guild_id != None:
            self.tree.copy_global_to(guild=self.get_guild(self.guild_id))
            await self.tree.sync(guild=self.get_guild(self.guild_id))
            self.logger.warn(f'Syncing Commands via update_loop to guild: {self.get_guild(self.guild_id).name} {await self.tree.sync(guild=self.get_guild(self.guild_id))}')
        else:
            self.logger.error(f'It appears I cannot Sync your commands for you, please run {self.prefix}bot utils sync or `/bot utils sync` to update your command tree. Please see the readme if you encounter issues.')
        self.update_loop.stop()

    async def permissions_update(self):
        """Loads the Custom Permission Cog and Validates the File."""
        try:
            await self.load_extension('cogs.permissions_cog')

        except discord.ext.commands.errors.ExtensionAlreadyLoaded:
            pass

        except Exception as e:
            self.logger.error(f'We ran into an Error Loading the Permissions_Cog. Error - {traceback.format_exc()}')
            return False

        self.bPerms = utils.get_botPerms()
        return True


async def autocomplete_loadedcogs(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    """Cog Autocomplete template."""
    choice_list = []
    for key in client.cogs:
        if key not in choice_list:
            choice_list.append(key)
    return [app_commands.Choice(name=choice, value=choice) for choice in choice_list if current.lower() in choice.lower()]

client = Gatekeeper(Version=Version)


@client.hybrid_group(name='bot', description=i18n.t('commands.bot.description'))
@utils.role_check()
async def main_bot(context: commands.Context):
    if context.invoked_subcommand is None:
        await context.send(i18n.t('common.invalid_command'), ephemeral=True, delete_after=client.Message_Timeout)


@main_bot.command(name='donator', description=i18n.t('commands.bot.donator.description'))
@utils.role_check()
async def bot_donator(context: commands.Context, role: discord.Role):
    client.logger.command(f'{context.author.name} used Bot Donator Role...')

    client.DBConfig.SetSetting('Donator_role_id', role.id)
    await context.send(i18n.t('messages.bot.donator.success', role_mention=role.mention), ephemeral=True, delete_after=client.Message_Timeout)


@main_bot.command(name='moderator', description=i18n.t('commands.bot.moderator.description'))
@commands.has_guild_permissions(administrator=True)
async def bot_moderator(context: commands.Context, role: discord.Role):
    client.logger.command(f'{context.author.name} used Bot Moderator...')

    client.DBConfig.SetSetting('Moderator_role_id', role.id)
    await context.send(i18n.t('messages.bot.moderator.success', role_name=role.name), ephemeral=True)


@main_bot.command(name='permissions', description=i18n.t('commands.bot.permissions.description'))
@commands.has_guild_permissions(administrator=True)
@app_commands.choices(permission=[
    Choice(name=i18n.t('commands.bot.permissions.params.permission.choices.0'), value=0),
    Choice(name=i18n.t('commands.bot.permissions.params.permission.choices.1'), value=1),
])
async def bot_permissions(context: commands.Context, permission: Choice[int]):
    client.logger.command(f'{context.author.name} used Bot Permissions...')

    # If we set to 0; we are using `Default` Permissions and need to unload the cog and commands related to custom permissions.
    if permission.value == 0:
        await context.send(i18n.t('messages.bot.permissions.selected_default'), ephemeral=True, delete_after=client.Message_Timeout)
        parent_command = client.get_command('user')
        parent_command.remove_command('role')
        if 'cogs.permissions_cog' in client.extensions:
            await client.unload_extension('cogs.permissions_cog')

    # If we set to 1; we are using `Custom` Permissions.
    elif permission.value == 1:
        await context.send(i18n.t('messages.bot.permissions.selected_custom'), ephemeral=True, delete_after=client.Message_Timeout)
        await context.send(i18n.t('messages.bot.permissions.visit_docs'), ephemeral=True, delete_after=client.Message_Timeout)
        # This validates the `bot_perms.json` file.
        if not await client.permissions_update():
            return await context.send(i18n.t('messages.bot.permissions.load_error'), ephemeral=True, delete_after=client.Message_Timeout)

    # Depending on which permissions; this will sync the updated commands available.
    client.tree.copy_global_to(guild=client.get_guild(context.guild.id))
    await client.tree.sync(guild=client.get_guild(context.guild.id))
    client.DBConfig.Permissions = permission.name
    await context.send(i18n.t('messages.bot.permissions.finished', permission_name=permission.name), ephemeral=True, delete_after=client.Message_Timeout)


@main_bot.command(name='language', description=i18n.t('commands.bot.language.description'))
@commands.has_guild_permissions(administrator=True)
@app_commands.describe(language=i18n.t('commands.bot.language.params.language.description'))
@app_commands.choices(language=[Choice(name='English', value='en'), Choice(name='Deutsch', value='de')])
async def bot_language(context: commands.Context, language: Choice[str]):
    client.logger.command(f'{context.author.name} used Bot Language...')
    # Walking every command in the tree plus a tree.sync() round trip can exceed Discord's 3s
    # interaction-ack window; mirrors the existing defer() precedent in bot_utils_clear/bot_utils_sync.
    await context.defer(ephemeral=True)

    i18n.set_language(language.value)
    updated, skipped = i18n.retranslate_command_tree(client)
    client.logger.info(f'i18n: retranslated {updated} fields to "{language.value}" ({skipped} fell back/skipped).')

    client.tree.copy_global_to(guild=client.get_guild(context.guild.id))
    await client.tree.sync(guild=client.get_guild(context.guild.id))

    await context.send(i18n.t('commands.bot.language.confirmation', language=language.name), ephemeral=True, delete_after=client.Message_Timeout)


@main_bot.command(name='settings', description=i18n.t('commands.bot.settings.description'))
@utils.role_check()
async def bot_settings(context: commands.Context):
    client.logger.command(f'{context.author.name} used Bot Settings...')
    await context.send(embed=client.eBot.bot_settings_embed(context), ephemeral=True, delete_after=(client.Message_Timeout * 3))  # Tripled the delay to help sort times.


@main_bot.group(name='utils', description=i18n.t('commands.bot.utils.description'))
@utils.role_check()
async def bot_utils(context: commands.Context):
    if context.invoked_subcommand is None:
        await context.send(i18n.t('common.invalid_command'), ephemeral=True, delete_after=client.Message_Timeout)


@bot_utils.command(name='clear', description=i18n.t('commands.bot.utils.clear.description'))
@app_commands.choices(all=[Choice(name=i18n.t('common.bool.true'), value=1), Choice(name=i18n.t('common.bool.false'), value=0)])
@app_commands.describe(all=i18n.t('commands.bot.utils.clear.params.all.description'))
@app_commands.describe(channel=i18n.t('commands.bot.utils.clear.params.channel.description'))
@utils.role_check()
async def bot_utils_clear(context: commands.Context, channel: discord.abc.GuildChannel = None, amount: app_commands.Range[int, 0, 100] = 50, all: Choice[int] = 0):
    client.logger.info(f'{context.author.name} used {context.command.name}...')
    client.context = context
    await context.defer()

    # Setting channel to the channel the command was run in as default.
    if channel == None:
        channel = context.channel

    if type(all) == Choice:
        all = all.value

    if all == 1:
        messages = await channel.purge(limit=amount, bulk=False)
    else:
        messages = await channel.purge(limit=amount, check=client.self_check, bulk=False)

    word = i18n.t_plural('common.messages_word', count=len(messages))
    return await channel.send(i18n.t('messages.bot.utils.clear.success', count=len(messages), word=word), delete_after=client.Message_Timeout)


@bot_utils.command(name='roleid', description=i18n.t('commands.bot.utils.roleid.description'))
@utils.role_check()
async def bot_utils_roleid(context: commands.Context, role: discord.Role):
    client.logger.command(f'{context.author.name} used Bot Utils Role ID...')

    await context.send(i18n.t('messages.bot.utils.roleid.result', role_name=role.name, role_id=role.id), ephemeral=True, delete_after=client.Message_Timeout)


@bot_utils.command(name='channelid', description=i18n.t('commands.bot.utils.channelid.description'))
@utils.role_check()
async def bot_utils_channelid(context: commands.Context, channel: discord.abc.GuildChannel):
    client.logger.command(f'{context.author.name} used Bot Utils Channel ID...')

    await context.send(i18n.t('messages.bot.utils.channelid.result', channel_name=channel.name, channel_id=channel.id), ephemeral=True, delete_after=client.Message_Timeout)


@bot_utils.command(name='userid', description=i18n.t('commands.bot.utils.userid.description'))
@utils.role_check()
async def bot_utils_userid(context: commands.Context, user: Union[discord.User, discord.Member]):
    client.logger.command(f'{context.author.name} used Bot Utils User ID...')

    await context.send(i18n.t('messages.bot.utils.userid.result', user_name=user.name, display_name=user.display_name, user_id=user.id), ephemeral=True, delete_after=client.Message_Timeout)


@bot_utils.command(name='uuid', description=i18n.t('commands.bot.utils.uuid.description'))
@utils.role_check()
async def bot_utils_uuid(context: commands.Context, mc_ign: str):
    client.logger.command(f'{context.author.name} used Bot Utils UUID...')

    await context.send(i18n.t('messages.bot.utils.uuid.result', mc_ign=mc_ign, uuid=client.uBot.name_to_uuid_MC(mc_ign)), ephemeral=True, delete_after=client.Message_Timeout)


@bot_utils.command(name='ping', description=i18n.t('commands.bot.utils.ping.description'))
@utils.role_check()
async def bot_utils_ping(context: commands.Context):
    client.logger.command(f'{context.author.name} used Bot Ping...')

    await context.send(i18n.t('messages.bot.utils.ping.result', latency=round(client.latency * 1000)), ephemeral=True, delete_after=client.Message_Timeout)


@bot_utils.command(name='disconnect', description=i18n.t('commands.bot.utils.disconnect.description'))
@utils.role_check()
async def bot_utils_stop(context: commands.Context):
    client.logger.command(f'{context.author.name} used Bot Stop Function...')

    await context.send(i18n.t('messages.bot.utils.disconnect.message'), ephemeral=True, delete_after=client.Message_Timeout)
    return await client.close()


@bot_utils.command(name='restart', description=i18n.t('commands.bot.utils.restart.description'))
@utils.role_check()
async def bot_utils_restart(context: commands.Context):
    client.logger.command(f'{context.author.name} used Bot Restart Function...')

    import os
    import sys
    await context.send(i18n.t('messages.bot.utils.restart.message'), ephemeral=True, delete_after=client.Message_Timeout)
    sys.stdout.flush()
    os.execv(sys.executable, ['python3'] + sys.argv)


@bot_utils.command(name='status', description=i18n.t('commands.bot.utils.status.description'))
@utils.role_check()
async def bot_utils_status(context: commands.Context):
    client.logger.command(f'{context.author.name} used Bot Status Function...')

    await context.send(i18n.t('messages.bot.utils.status.versions', discord_version=discord.__version__, python_version=sys.version), ephemeral=True, delete_after=client.Message_Timeout)
    await context.send(i18n.t('messages.bot.utils.status.bot_db_version', bot_version=Version, db_version=client.DBHandler.DB_Version), ephemeral=True, delete_after=client.Message_Timeout)
    await context.send(i18n.t('messages.bot.utils.status.connections', amp_connected=client.AMPHandler.SuccessfulConnection, db_connected=client.DBHandler.SuccessfulDatabase), ephemeral=True, delete_after=client.Message_Timeout)


@bot_utils.command(name='message_timeout', description=i18n.t('commands.bot.utils.message_timeout.description'))
@utils.role_check()
@app_commands.describe(time=i18n.t('commands.bot.utils.message_timeout.params.time.description'))
async def bot_utils_message_timeout(context: commands.Context, time: Union[None, int] = 60):
    client.logger.command(f'{context.author.name} used Bot Utils Message Timeout Function...')

    client.DBConfig.SetSetting('Message_Timeout', f'{time}')
    client.Message_Timeout = time

    content_str = i18n.t('messages.bot.utils.message_timeout.will_delete', time=time)
    if time == None:
        content_str = i18n.t('messages.bot.utils.message_timeout.will_not_delete')

    await context.send(content=i18n.t('messages.bot.utils.message_timeout.result', content_str=content_str), ephemeral=True, delete_after=client.Message_Timeout)


@bot_utils.command(name='sync', description=i18n.t('commands.bot.utils.sync.description'))
@utils.role_check()
@app_commands.choices(local=[Choice(name=i18n.t('common.bool.true'), value=1), Choice(name=i18n.t('common.bool.false'), value=0)])
@app_commands.choices(reset=[Choice(name=i18n.t('common.bool.true'), value=1), Choice(name=i18n.t('common.bool.false'), value=0)])
async def bot_utils_sync(context: commands.Context, local: Choice[int] = True, reset: Choice[int] = False):
    client.logger.command(f'{context.author.name} used Bot Sync Function...')
    await context.defer()
    # This keeps our DB Guild_ID Current.
    if client.guild_id == None or context.guild.id != int(client.guild_id):
        client.DBConfig.SetSetting('Guild_ID', context.guild.id)

    if ((type(reset)) == bool and (reset == True)) or ((type(reset) == Choice) and (reset.value == 1)):
        if ((type(local) == bool) and (local == True)) or ((type(local)) == Choice and (local.value == 1)):
            # Local command tree reset
            client.tree.clear_commands(guild=context.guild)
            client.logger.command(f'Bot Commands Reset Locally and Sync\'d: {await client.tree.sync(guild=context.guild)}')
            return await context.send(i18n.t('messages.bot.utils.sync.reset_local'), ephemeral=True, delete_after=client.Message_Timeout)

        elif context.author.id == 144462063920611328:
            # Global command tree reset, limited by k8thekat discord ID
            client.tree.clear_commands(guild=None)
            client.logger.command(f'Bot Commands Reset Global and Sync\'d: {await client.tree.sync(guild=None)}')
            return await context.send(i18n.t('messages.bot.utils.sync.reset_global'), ephemeral=True, delete_after=client.Message_Timeout)
        else:
            return await context.send(i18n.t('messages.bot.utils.sync.no_permission'), ephemeral=True, delete_after=client.Message_Timeout)

    if ((type(local) == bool) and (local == True)) or ((type(local) == Choice) and (local.value == 1)):
        # Local command tree sync
        client.tree.copy_global_to(guild=context.guild)
        client.logger.command(f'Bot Commands Sync\'d Locally: {await client.tree.sync(guild=context.guild)}')
        return await context.send(i18n.t('messages.bot.utils.sync.local_success', guild_name=context.guild.name), ephemeral=True, delete_after=client.Message_Timeout)

    elif context.author.id == 144462063920611328:
        # Global command tree sync, limited by k8thekat discord ID
        client.logger.command(f'Bot Commands Sync\'d Globally: {await client.tree.sync(guild=None)}')
        await context.send(i18n.t('messages.bot.utils.sync.global_success'), ephemeral=True, delete_after=client.Message_Timeout)


# Cog Specific Bot Commands --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
@main_bot.group(name='cog', description=i18n.t('commands.bot.cog.description'))
@utils.role_check()
async def bot_cog(context: commands.Context):
    if context.invoked_subcommand is None:
        await context.send(i18n.t('common.invalid_command'), ephemeral=True, delete_after=client.Message_Timeout)


@bot_cog.command(name='load', description=i18n.t('commands.bot.cog.load.description'))
@utils.role_check()
async def bot_cog_loader(context: commands.Context, cog: str):
    client.logger.command(f'{context.author.name} used Bot Cog Load Function...')

    try:
        await client.load_extension(name=cog)
    except Exception as e:
        await context.send(i18n.t('messages.bot.cog.load.error', cog=cog, traceback=traceback.format_exc()), ephemeral=True, delete_after=client.Message_Timeout)
    else:
        await context.send(i18n.t('messages.bot.cog.load.success', cog=cog), ephemeral=True, delete_after=client.Message_Timeout)


@bot_cog.command(name='unload', description=i18n.t('commands.bot.cog.unload.description'))
@utils.role_check()
@app_commands.autocomplete(cog=autocomplete_loadedcogs)
async def bot_cog_unloader(context: commands.Context, cog: str):
    client.logger.command(f'{context.author.name} used Bot Cog Unload Function...')

    try:
        my_cog = client.cogs[cog]
        await my_cog.cog_unload()
        # await client.unload_extension(name=cog)
    except Exception as e:
        await context.send(i18n.t('messages.bot.cog.unload.error', cog=cog, traceback=traceback.format_exc()), ephemeral=True, delete_after=client.Message_Timeout)
    else:
        await context.send(i18n.t('messages.bot.cog.unload.success', cog=cog), ephemeral=True, delete_after=client.Message_Timeout)


@bot_cog.command(name='reload', description=i18n.t('commands.bot.cog.reload.description'))
@utils.role_check()
async def bot_cog_reload(context: commands.Context):
    client.logger.command(f'{context.author.name} used Bot Cog Reload Function...')

    await client.Handler.cog_auto_loader(reload=True)
    await context.send(i18n.t('messages.bot.cog.reload.success'), ephemeral=True, delete_after=client.Message_Timeout)


def client_run(tokens):
    client.logger.info('Gatekeeper v4 Intializing...')
    client.logger.info(f'Discord Version: {discord.__version__}  // Gatekeeper v4 Version: {client.Bot_Version} // Python Version {sys.version}')
    client.run(tokens.token, reconnect=True, log_handler=None)
