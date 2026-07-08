'''
   Copyright (C) 2021-2022 Katelynn Cadwallader.

   This file is part of Gatekeeper, the AMP Minecraft Discord Bot.

   Gatekeeper is free software; you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation; either version 3, or (at your option)
   any later version.

   Gatekeeper is distributed in the hope that it will be useful, but WITHOUT
   ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
   or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public
   License for more details.

   You should have received a copy of the GNU General Public License
   along with Gatekeeper; see the file COPYING.  If not, write to the Free
   Software Foundation, 51 Franklin Street - Fifth Floor, Boston, MA
   02110-1301, USA.

'''
from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING, Optional

import discord
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import commands, tasks

import AMP_Handler
import DB
import utils
import utils_embeds
import utils_ui
from discordBot import Gatekeeper

if TYPE_CHECKING:
    from discordBot import Gatekeeper

# This is used to force cog order to prevent missing methods.
# MUST USE ENTIRE FILENAME!
Dependencies = ["AMP_server_cog.py"]


class WhitelistSync(commands.Cog):
    def __init__(self, client: Gatekeeper):
        self._client: Gatekeeper = client
        self.name = os.path.basename(__file__)
        self.logger = logging.getLogger()

        self.AMPHandler = AMP_Handler.getAMPHandler()

        self.DBHandler = DB.getDBHandler()
        self.DB = self.DBHandler.DB  # Main Database object
        self.DBConfig = self.DBHandler.DBConfig

        self.uBot = utils.botUtils(client)
        self.eBot = utils_embeds.botEmbeds(client)
        self.uiBot = utils_ui

        # Attach our Whitelist Role management commands to the existing `server settings` group.
        self.uBot.sub_group_command_handler('server settings', self.whitelist_role_add)
        self.uBot.sub_group_command_handler('server settings', self.whitelist_role_remove)
        self.uBot.sub_group_command_handler('server settings', self.whitelist_role_list)

        if self.DBConfig.GetSetting('Whitelist_Role_Sync'):
            interval = int(self.DBConfig.GetSetting('Whitelist_Role_Sync_Interval') or 15)
            self.whitelist_role_sync_reconciliation.change_interval(minutes=interval)
            self.whitelist_role_sync_reconciliation.start()

        self.logger.info(f'**SUCCESS** Initializing {self.name.title()}')

    # Internal Helpers ----------------------------------------------------------------------------------------------------------------------

    def _get_amp_instance_by_server_id(self, ServerID: int) -> Optional[AMP_Handler.AMP.AMPInstance]:
        """Finds the live AMPInstance tied to a Servers table row ID."""
        for amp_instance in self.AMPHandler.AMP_Instances.values():
            if amp_instance.DB_Server.ID == ServerID:
                return amp_instance
        return None

    def _get_or_create_db_user(self, member: discord.Member) -> DB.DBUser:
        db_user = self.DB.GetUser(member.id)
        if db_user is None:
            db_user = self.DB.AddUser(DiscordID=member.id, DiscordName=member.name)
        return db_user

    async def _sync_add(self, member: discord.Member, ServerID: int):
        """Ensures `member` is Whitelisted on the AMP Instance tied to `ServerID`, if we have a linked identity for them."""
        amp_server = self._get_amp_instance_by_server_id(ServerID)
        if amp_server is None or not amp_server.Running:
            return

        db_user = self._get_or_create_db_user(member)
        try:
            whitelisted = amp_server.check_Whitelist(db_user)
        except Exception:
            self.logger.error(f'Whitelist Role Sync: Failed to check Whitelist status for {member.name} on {amp_server.FriendlyName}', exc_info=True)
            return

        if whitelisted == False:
            try:
                await member.send(f'Hey! I would love to auto-Whitelist you on **{amp_server.FriendlyName if amp_server.FriendlyName != None else amp_server.InstanceName}**, but I do not have a linked game account for you yet. Please use `/link` first.')
            except discord.Forbidden:
                pass
            return

        if whitelisted == True:
            amp_server.addWhitelist(db_user=db_user)
            self.logger.command(f'Whitelist Role Sync: Whitelisted {member.name} on {amp_server.FriendlyName}')

    async def _sync_remove(self, member: discord.Member, ServerID: int):
        """Removes `member` from the Whitelist on the AMP Instance tied to `ServerID`, if they are currently on it."""
        amp_server = self._get_amp_instance_by_server_id(ServerID)
        if amp_server is None or not amp_server.Running:
            return

        db_user = self.DB.GetUser(member.id)
        if db_user is None:
            return

        try:
            whitelisted = amp_server.check_Whitelist(db_user)
        except Exception:
            self.logger.error(f'Whitelist Role Sync: Failed to check Whitelist status for {member.name} on {amp_server.FriendlyName}', exc_info=True)
            return

        if whitelisted == None:
            amp_server.removeWhitelist(db_user=db_user)
            self.logger.command(f'Whitelist Role Sync: Removed {member.name} from the Whitelist on {amp_server.FriendlyName}')

    async def _cleanup_minecraft_whitelist(self, context: commands.Context):
        """Removes `db_user` from any role-synced Minecraft Whitelist before their linked IGN/UUID is cleared via `/link remove`.\n
        Must be called *before* nulling `MC_IngameName`/`MC_UUID`, since removal still needs the old identity to know who to remove."""
        if not self.DBConfig.GetSetting('Whitelist_Role_Sync'):
            return

        if not isinstance(context.author, discord.Member):
            return

        server_ids = set()
        for role in context.author.roles:
            server_ids.update(self.DB.GetServersByWhitelistRole(role.id))

        for server_id in server_ids:
            amp_server = self._get_amp_instance_by_server_id(server_id)
            # Only Minecraft actually keys Whitelist membership off MC_IngameName/MC_UUID today; every other
            # module's check_Whitelist/removeWhitelist is a no-op regardless of identity, so there's nothing to clean up there.
            if amp_server != None and amp_server.Module == 'Minecraft':
                await self._sync_remove(context.author, server_id)

    # Discord Listener Events -----------------------------------------------------------------------------------------------------------------

    @commands.Cog.listener('on_member_update')
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        """Keeps AMP Whitelists in sync when a Member gains or loses a configured Whitelist Sync Role."""
        if not self.DBConfig.GetSetting('Whitelist_Role_Sync'):
            return

        before_roles = {role.id for role in before.roles}
        after_roles = {role.id for role in after.roles}

        gained_roles = after_roles - before_roles
        lost_roles = before_roles - after_roles

        for role_id in gained_roles:
            for server_id in self.DB.GetServersByWhitelistRole(role_id):
                await self._sync_add(after, server_id)

        for role_id in lost_roles:
            for server_id in self.DB.GetServersByWhitelistRole(role_id):
                await self._sync_remove(after, server_id)

    @commands.Cog.listener('on_member_remove')
    async def on_member_remove(self, member: discord.Member):
        """Removes a departing Member from any Whitelist their Discord Roles were gating access for."""
        if not self.DBConfig.GetSetting('Whitelist_Role_Sync'):
            return

        server_ids = set()
        for role in member.roles:
            server_ids.update(self.DB.GetServersByWhitelistRole(role.id))

        for server_id in server_ids:
            await self._sync_remove(member, server_id)

    # Reconciliation Task ---------------------------------------------------------------------------------------------------------------------

    @tasks.loop(minutes=15)
    async def whitelist_role_sync_reconciliation(self):
        """Periodic safety-net pass; catches Role/Whitelist drift missed while the bot was offline."""
        if not self.DBConfig.GetSetting('Whitelist_Role_Sync'):
            return

        guild_id = getattr(self._client, 'guild_id', None)
        if guild_id is None:
            return

        guild = self._client.get_guild(guild_id)
        if guild is None:
            return

        self.logger.dev('Whitelist Role Sync: Running reconciliation pass...')
        for amp_server in list(self.AMPHandler.AMP_Instances.values()):
            db_server = amp_server.DB_Server
            role_ids = db_server.GetWhitelistRoles()
            if not len(role_ids):
                continue

            members = set()
            for role_id in role_ids:
                role = guild.get_role(role_id)
                if role != None:
                    members.update(role.members)

            for member in members:
                await self._sync_add(member, db_server.ID)

        self.logger.dev('Whitelist Role Sync: Reconciliation pass complete.')

    @whitelist_role_sync_reconciliation.before_loop
    async def before_whitelist_role_sync_reconciliation(self):
        await self._client.wait_until_ready()

    # Account Linking Commands -----------------------------------------------------------------------------------------------------------------

    @commands.hybrid_group(name='link')
    async def link_group(self, context: commands.Context):
        if context.invoked_subcommand is None:
            await context.send('Please use a subcommand, e.g. `/link minecraft <ign>` or `/link steam <steamid64>`.', ephemeral=True, delete_after=self._client.Message_Timeout)

    @link_group.command(name='minecraft')
    async def link_minecraft(self, context: commands.Context, ign: str):
        """Links your Discord account to a Minecraft in-game name."""
        self.logger.command(f'{context.author.name} used Link Minecraft')

        profile = self.uBot.get_minecraft_profile(ign)
        if profile == None:
            return await context.send(f'I was unable to find a Minecraft account named **{ign}**, please double check the spelling.', ephemeral=True, delete_after=self._client.Message_Timeout)

        embed = discord.Embed(title='Is this your Minecraft Account?', description=f'**{profile["name"]}**\nUUID: `{profile["uuid"]}`', color=0x808000)
        embed.set_thumbnail(url=profile['avatar'])

        def apply_minecraft_link(db_user: DB.DBUser):
            db_user.MC_IngameName = profile['name']
            db_user.MC_UUID = profile['uuid']

        view = self.uiBot.LinkConfirmView(invoker_id=context.author.id, apply=apply_minecraft_link, confirm_message=f'Linked your Discord account to the Minecraft account **{profile["name"]}**!')
        view.message = await context.send(embed=embed, view=view, ephemeral=True)

    @link_group.command(name='steam')
    async def link_steam(self, context: commands.Context, steam: str):
        """Links your Discord account to a Steam Account. Accepts a vanity name, profile URL, or SteamID64."""
        self.logger.command(f'{context.author.name} used Link Steam')

        if not self.uBot.steam_api_key_configured():
            return await context.send('Sorry, Steam account linking has not been configured by Staff yet.', ephemeral=True, delete_after=self._client.Message_Timeout)

        profile = self.uBot.get_steam_profile(steam)
        if profile == None:
            return await context.send(f'I was unable to find a Steam account matching **{steam}**. Try pasting your full Steam profile URL instead.', ephemeral=True, delete_after=self._client.Message_Timeout)

        embed = discord.Embed(title='Is this your Steam Account?', description=f'[{profile["personaname"]}]({profile["profileurl"]})\nSteamID64: `{profile["steamid"]}`', color=0x808000)
        if profile['avatar'] != None:
            embed.set_thumbnail(url=profile['avatar'])

        def apply_steam_link(db_user: DB.DBUser):
            db_user.SteamID = profile['steamid']

        view = self.uiBot.LinkConfirmView(invoker_id=context.author.id, apply=apply_steam_link, confirm_message='Linked your Discord account to that Steam account!')
        view.message = await context.send(embed=embed, view=view, ephemeral=True)

    @link_group.command(name='show')
    async def link_show(self, context: commands.Context):
        """Shows your currently linked game accounts."""
        self.logger.command(f'{context.author.name} used Link Show')

        db_user = self.DB.GetUser(context.author.id)
        await context.send(embed=self.eBot.user_info_embed(db_user, context.author), ephemeral=True, delete_after=self._client.Message_Timeout)

    @link_group.command(name='remove')
    @app_commands.choices(identity=[Choice(name='Minecraft', value='minecraft'), Choice(name='Steam', value='steam')])
    async def link_remove(self, context: commands.Context, identity: Choice[str]):
        """Removes one of your linked game accounts."""
        self.logger.command(f'{context.author.name} used Link Remove')

        db_user = self.DB.GetUser(context.author.id)
        if db_user is None:
            return await context.send('You do not have any linked accounts yet.', ephemeral=True, delete_after=self._client.Message_Timeout)

        if identity.value == 'minecraft':
            if db_user.MC_IngameName == None and db_user.MC_UUID == None:
                return await context.send('You do not have a linked Minecraft account to remove.', ephemeral=True, delete_after=self._client.Message_Timeout)

            # Must run before nulling the fields below; removal still needs the old IGN/UUID to know who to remove.
            await self._cleanup_minecraft_whitelist(context)
            db_user.MC_IngameName = None
            db_user.MC_UUID = None
            await context.send('Removed your linked Minecraft account.', ephemeral=True, delete_after=self._client.Message_Timeout)
        elif identity.value == 'steam':
            if db_user.SteamID == None:
                return await context.send('You do not have a linked Steam account to remove.', ephemeral=True, delete_after=self._client.Message_Timeout)

            db_user.SteamID = None
            await context.send('Removed your linked Steam account.', ephemeral=True, delete_after=self._client.Message_Timeout)

    # Discord Auto Completes ---------------------------------------------------------------------------------------------------------------

    async def autocomplete_whitelist_roles(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        """Autocomplete for Discord Roles currently gating Whitelist access on the already-selected `server` option."""
        server = interaction.namespace.server
        if not server:
            return []

        amp_server = self.uBot.serverparse(server)
        if amp_server == None:
            return []

        db_server = self.DB.GetServer(amp_server.InstanceID)
        choices = []
        for role_id in db_server.GetWhitelistRoles():
            role = interaction.guild.get_role(role_id)
            name = role.name if role != None else f'Deleted Role ({role_id})'
            if current.lower() in name.lower():
                choices.append(app_commands.Choice(name=name, value=str(role_id)))

        return choices[:25]

    # Whitelist Role Management Commands (attached to `server settings`) ----------------------------------------------------------------------

    @commands.hybrid_command(name='whitelist_role_add')
    @utils.role_check()
    @app_commands.autocomplete(server=utils.autocomplete_servers)
    async def whitelist_role_add(self, context: commands.Context, server: str, role: discord.Role):
        """Adds a Discord Role that grants automatic Whitelist access to the provided Server."""
        self.logger.command(f'{context.author.name} used Whitelist Role Add')

        amp_server = await self.uBot._serverCheck(context, server, False)
        if amp_server:
            db_server = self.DB.GetServer(amp_server.InstanceID)
            server_name = amp_server.FriendlyName if amp_server.FriendlyName != None else amp_server.InstanceName

            if role.id in db_server.GetWhitelistRoles():
                return await context.send(f'**{role.name}** is already gating Whitelist access for **{server_name}**.', ephemeral=True, delete_after=self._client.Message_Timeout)

            db_server.AddWhitelistRole(role.id)
            await context.send(f'Members with **{role.name}** will now be automatically Whitelisted on **{server_name}**.', ephemeral=True, delete_after=self._client.Message_Timeout)

    @commands.hybrid_command(name='whitelist_role_remove')
    @utils.role_check()
    @app_commands.autocomplete(server=utils.autocomplete_servers, role=autocomplete_whitelist_roles)
    async def whitelist_role_remove(self, context: commands.Context, server: str, role: str):
        """Removes a Discord Role from a Server's Whitelist Sync gate list."""
        self.logger.command(f'{context.author.name} used Whitelist Role Remove')

        amp_server = await self.uBot._serverCheck(context, server, False)
        if amp_server:
            db_server = self.DB.GetServer(amp_server.InstanceID)
            server_name = amp_server.FriendlyName if amp_server.FriendlyName != None else amp_server.InstanceName

            if not role.isdigit():
                return await context.send(f'I could not recognize **{role}** as a Discord Role, please pick one from the autocomplete list.', ephemeral=True, delete_after=self._client.Message_Timeout)

            role_id = int(role)
            discord_role = context.guild.get_role(role_id)
            role_name = discord_role.name if discord_role != None else f'Deleted Role ({role_id})'

            if role_id not in db_server.GetWhitelistRoles():
                return await context.send(f'**{role_name}** is not currently gating Whitelist access for **{server_name}**.', ephemeral=True, delete_after=self._client.Message_Timeout)

            db_server.DelWhitelistRole(role_id)
            await context.send(f'Removed **{role_name}** from **{server_name}**\'s Whitelist Sync.', ephemeral=True, delete_after=self._client.Message_Timeout)

    @commands.hybrid_command(name='whitelist_role_list')
    @utils.role_check()
    @app_commands.autocomplete(server=utils.autocomplete_servers)
    async def whitelist_role_list(self, context: commands.Context, server: str):
        """Lists all Discord Roles gating Whitelist access for the provided Server."""
        self.logger.command(f'{context.author.name} used Whitelist Role List')

        amp_server = await self.uBot._serverCheck(context, server, False)
        if amp_server:
            db_server = self.DB.GetServer(amp_server.InstanceID)
            server_name = amp_server.FriendlyName if amp_server.FriendlyName != None else amp_server.InstanceName
            role_ids = db_server.GetWhitelistRoles()

            if not len(role_ids):
                return await context.send(f'**{server_name}** has no Whitelist Sync Roles configured.', ephemeral=True, delete_after=self._client.Message_Timeout)

            role_mentions = []
            for role_id in role_ids:
                role = context.guild.get_role(role_id)
                role_mentions.append(role.mention if role != None else f'`{role_id}` (deleted role)')

            await context.send(f'**{server_name}** Whitelist Sync Roles: {", ".join(role_mentions)}', ephemeral=True, delete_after=self._client.Message_Timeout)

    # Whitelist Sync Global Settings --------------------------------------------------------------------------------------------------------

    @commands.hybrid_group(name='whitelist_sync')
    @utils.role_check()
    async def whitelist_sync_settings(self, context: commands.Context):
        if context.invoked_subcommand is None:
            await context.send('Invalid command passed...', ephemeral=True, delete_after=self._client.Message_Timeout)

    @whitelist_sync_settings.command(name='enabled')
    @utils.role_check()
    @app_commands.choices(flag=[Choice(name='True', value=1), Choice(name='False', value=0)])
    async def whitelist_sync_enabled(self, context: commands.Context, flag: Choice[int]):
        """Turns Discord Role Whitelist Syncing ON or OFF."""
        self.logger.command(f'{context.author.name} used Whitelist Sync Enabled')

        self.DBConfig.SetSetting('Whitelist_Role_Sync', flag.value)
        if flag.value == 1:
            if not self.whitelist_role_sync_reconciliation.is_running():
                interval = int(self.DBConfig.GetSetting('Whitelist_Role_Sync_Interval') or 15)
                self.whitelist_role_sync_reconciliation.change_interval(minutes=interval)
                self.whitelist_role_sync_reconciliation.start()
            await context.send('Woohoo! I will now keep Whitelists in sync with Discord Roles.', ephemeral=True, delete_after=self._client.Message_Timeout)
        else:
            if self.whitelist_role_sync_reconciliation.is_running():
                self.whitelist_role_sync_reconciliation.stop()
            await context.send('Alright, I will no longer sync Whitelists with Discord Roles.', ephemeral=True, delete_after=self._client.Message_Timeout)

    @whitelist_sync_settings.command(name='interval')
    @utils.role_check()
    @app_commands.describe(minutes='How often (in minutes) to run the Whitelist Sync reconciliation pass.')
    async def whitelist_sync_interval(self, context: commands.Context, minutes: app_commands.Range[int, 1, 1440] = 15):
        """Sets how often the Whitelist Sync reconciliation pass runs, in minutes."""
        self.logger.command(f'{context.author.name} used Whitelist Sync Interval')

        self.DBConfig.SetSetting('Whitelist_Role_Sync_Interval', minutes)
        if self.whitelist_role_sync_reconciliation.is_running():
            self.whitelist_role_sync_reconciliation.change_interval(minutes=minutes)
        await context.send(f'Whitelist Sync reconciliation will now run every **{minutes} {"minutes" if minutes > 1 else "minute"}**.', ephemeral=True, delete_after=self._client.Message_Timeout)


async def setup(client: commands.Bot):
    await client.add_cog(WhitelistSync(client))
