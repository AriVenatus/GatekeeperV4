# Copyright (C) 2021-2022 Katelynn Cadwallader
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations
import discord
from discord.ext import commands
import os
import logging

from core import utils
from core import AMP_Handler
from core import DB as DB


DisplayImageSources = ["internal:MinecraftJava"]


class Minecraft(commands.Cog):
    def __init__(self, client: commands.Bot):
        self._client = client
        self.name = os.path.basename(__file__)
        self.logger = logging.getLogger(__name__)  # Point all print/logging statments here!

        self.AMPHandler = AMP_Handler.getAMPHandler()
        self.AMP = self.AMPHandler.AMP  # Main AMP object
        self.AMPInstances = self.AMPHandler.AMP_Instances  # Main AMP Instance Dictionary

        self.DBHandler = DB.getDBHandler()
        self.DB = self.DBHandler.DB  # Main Database object
        self.DBConfig = self.DBHandler.DBConfig

        self.uBot = utils.botUtils(client)  # Utilities Class for Embed's and other functionality.

        # This will be used for Modded Minecraft - Not yet implemented.
        self.DBConfig.AddSetting('Minecraft_Multiverse_Core', False)

        self.logger.info(f'**SUCCESS** Initializing Module **{self.name.capitalize()}**')

    @commands.Cog.listener('on_user_update')
    async def on_user_update(self, user_before, user_after: discord.User):
        """Called when a User updates any part of their Discord Profile; this provides access to the `user_before` and `user_after` <discord.Member> objects."""
        self.logger.dev(f'User Update {self.name}: {user_before} into {user_after}')
        return user_before, user_after

    @commands.Cog.listener('on_member_remove')
    async def on_member_remove(self, member: discord.Member):
        """Called when a member is kicked or leaves the Server/Guild. Returns a <discord.Member> object."""
        self.logger.dev(f'Member Leave {self.name}: {member.name} {member}')

        db_user = self.DB.GetUser(str(member.id))
        if db_user != None and db_user.InGameName != None:
            for server in list(self.AMPInstances):
                if self.AMPInstances[server].Module == 'Minecraft':
                    if db_user.MC_IngameName != None:
                        self.AMPInstances[server].removeWhitelist(db_user.MC_IngameName)

        return member


async def setup(client):
    await client.add_cog(Minecraft(client))
