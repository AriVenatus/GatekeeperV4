# Copyright (C) 2021-2022 Katelynn Cadwallader
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations
import sys
import logging
import traceback

import discord
from discord.ext import commands, tasks

# Custom scripts
from core import utils
from core import utils_permissions
from core import utils_embeds
from core import utils_ui
from core import AMP_Handler
from core import DB
from core import i18n

Version = 'beta-4.11.0'

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
        self.logger.warning(f'Waiting to Update Bot Version to {Version}...')
        await client.wait_until_ready()
        self.logger.warning(f'Currently Updating Bot Version to {Version}...')
        self.DBConfig.SetSetting('Bot_Version', Version)
        if self.guild_id != None:
            self.tree.copy_global_to(guild=self.get_guild(self.guild_id))
            await self.tree.sync(guild=self.get_guild(self.guild_id))
            self.logger.warning(f'Syncing Commands via update_loop to guild: {self.get_guild(self.guild_id).name} {await self.tree.sync(guild=self.get_guild(self.guild_id))}')
        else:
            self.logger.error(f'It appears I cannot Sync your commands for you, please run {self.prefix}bot utils sync or `/bot utils sync` to update your command tree. Please see the readme if you encounter issues.')
        self.update_loop.stop()

    async def permissions_update(self):
        """Loads the Custom Permission Cog and Validates the File."""
        try:
            await self.load_extension('cogs.permissions_cog')

        except discord.ext.commands.errors.ExtensionAlreadyLoaded:
            pass

        except Exception:
            self.logger.error(f'We ran into an Error Loading the Permissions_Cog. Error - {traceback.format_exc()}')
            return False

        self.bPerms = utils_permissions.get_botPerms()
        return True


client = Gatekeeper(Version=Version)


def client_run(tokens):
    client.logger.info('Gatekeeper v4 Intializing...')
    client.logger.info(f'Discord Version: {discord.__version__}  // Gatekeeper v4 Version: {client.Bot_Version} // Python Version {sys.version}')
    client.run(tokens.token, reconnect=True, log_handler=None)
