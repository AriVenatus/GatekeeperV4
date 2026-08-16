# Copyright (C) 2021-2022 Katelynn Cadwallader
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations
import logging
import aiohttp
import asyncio
from typing import Union

import discord
from discord.ext import commands

from core import DB
from core import AMP_Handler
from core import utils_api
from core import utils_discord


class botUtils(utils_api.GameAPIMixin, utils_discord.DiscordPlumbingMixin):
    """Gatekeeper Utility Class"""

    def __init__(self, client: discord.Client = None):
        self._client = client
        self.logger = logging.getLogger(__name__)
        self.logger.debug('Utils Bot Loaded')

        self.DBHandler = DB.getDBHandler()
        self.DB = self.DBHandler.DB  # Main Database object
        self.DBConfig = self.DBHandler.DBConfig

        self.AMPHandler = AMP_Handler.getAMPHandler()
        self.AMPInstances = self.AMPHandler.AMP_Instances
        self.AMPServer_Avatar_urls = []

    def str_to_bool(self, parameter: str):
        """Bool Converter"""
        return parameter.lower() == 'true'

    def message_formatter(self, message: str):
        """Formats the message for Discord
        `Bold = \\x01, \\x02`
        `Italic = \\x03, \\x04`
        `Underline = \\x05, \\x06` \n"""
        message = message.replace('\x01', '**')
        message = message.replace('\x02', '**')
        message = message.replace('\x03', '*')
        message = message.replace('\x04', '*')
        message = message.replace('\x05', '__')
        message = message.replace('\x06', '__')
        return message

    def whitelist_reply_handler(self, message: str, context: commands.Context, server: AMP_Handler.AMP.AMPInstance = None) -> str:
        """Fills whitelist reply placeholders: `<user>`, `<server>`, `<guild>`."""

        if message.find('<user>') != -1:
            message = message.replace('<user>', context.author.name)
        if message.find('<guild>') != -1:
            message = message.replace('<guild>', context.guild.name)
        if message.find('<server>') != -1 and server is not None:
            server_name = server.FriendlyName
            if server.DisplayName != None:
                server_name = server.DisplayName
            message = message.replace('<server>', server_name)
        return message

    async def validate_avatar(self, db_server: AMP_Handler.AMP.AMPInstance) -> Union[str, None]:
        """This checks the DB Server objects Avatar_url and returns the proper object type.
        Must be either `webp`, `jpeg`, `jpg`, `png`, or `gif` if it's animated."""
        if db_server.Avatar_url == None:
            return None
        # This handles web URL avatar icon urls.
        if db_server.Avatar_url.startswith("https://") or db_server.Avatar_url.startswith("http://"):
            if db_server.Avatar_url not in self.AMPServer_Avatar_urls:
                await asyncio.sleep(.5)
                # Validating if the URL actually works/exists via response.status codes.
                async with aiohttp.ClientSession() as session:
                    async with session.get(db_server.Avatar_url) as response:
                        if response.status == 200:
                            self.AMPServer_Avatar_urls.append(db_server.Avatar_url)
                            return db_server.Avatar_url
                        else:
                            self.logger.error(f'We are getting Error Code {response.status}, not sure whats going on...')
                            return None
            else:
                return db_server.Avatar_url
        else:
            return None
