# Copyright (C) 2021-2022 Katelynn Cadwallader
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING, Optional

import discord
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import commands, tasks

from core import AMP_Handler
from core import DB
from core import utils
from core import utils_permissions
from core import utils_discord
from core import utils_embeds
from core import utils_ui
from core import i18n
from core.discordBot import Gatekeeper

if TYPE_CHECKING:
    from core.discordBot import Gatekeeper

# This is used to force cog order to prevent missing methods.
# MUST USE ENTIRE FILENAME!
Dependencies = ["amp_server_cog.py"]


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
        self.uBot.sub_group_command_handler('server settings', self.donator_role_add)
        self.uBot.sub_group_command_handler('server settings', self.donator_role_remove)
        self.uBot.sub_group_command_handler('server settings', self.donator_role_list)

        if self.DBConfig.GetSetting('Whitelist_Role_Sync'):
            interval = int(self.DBConfig.GetSetting('Whitelist_Role_Sync_Interval') or 15)
            self.whitelist_role_sync_reconciliation.change_interval(minutes=interval)
            self.whitelist_role_sync_reconciliation.start()

        self.logger.info(f'**SUCCESS** Initializing {self.name.title()}')

    # Internal Helpers ----------------------------------------------------------------------------------------------------------------------

    def _get_amp_instance_by_server_id(self, ServerID: int) -> Optional[AMP_Handler.AMP.AMPInstance]:
        """Finds the live AMPInstance tied to a Servers table row ID."""
        for amp_instance in list(self.AMPHandler.AMP_Instances.values()):
            if ServerID == amp_instance.DB_Server.ID:
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
            self.logger.exception(f'Whitelist Role Sync: Failed to check Whitelist status for {member.name} on {amp_server.FriendlyName}')
            return

        if whitelisted == False:
            server_name = amp_server.FriendlyName if amp_server.FriendlyName != None else amp_server.InstanceName
            try:
                await member.send(i18n.t('messages.whitelist_sync.dm_need_link', server_name=server_name))
            except discord.Forbidden:
                pass
            return

        if whitelisted == True:
            if amp_server.addWhitelist(db_user=db_user):
                self.logger.command(f'Whitelist Role Sync: Whitelisted {member.name} on {amp_server.FriendlyName}')
            else:
                self.logger.error(f'Whitelist Role Sync: Failed to Whitelist {member.name} on {amp_server.FriendlyName} -- the AMP Console command did not go through (check the Gatekeeper AMP Role\'s permissions).')

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
            self.logger.exception(f'Whitelist Role Sync: Failed to check Whitelist status for {member.name} on {amp_server.FriendlyName}')
            return

        if whitelisted == None:
            if amp_server.removeWhitelist(db_user=db_user):
                self.logger.command(f'Whitelist Role Sync: Removed {member.name} from the Whitelist on {amp_server.FriendlyName}')
            else:
                self.logger.error(f'Whitelist Role Sync: Failed to remove {member.name} from the Whitelist on {amp_server.FriendlyName} -- the AMP Console command did not go through (check the Gatekeeper AMP Role\'s permissions).')

    async def _sync_role_members_now(self, role: discord.Role, ServerID: int):
        """Immediately syncs every current holder of `role` against `ServerID`'s Whitelist.
        Called right after a Role is newly registered as a Whitelist-Sync or Donator gate --
        without this, someone who already held the Role before it became a gate would only
        get picked up by the next periodic `whitelist_role_sync_reconciliation` tick (up to
        `Whitelist_Role_Sync_Interval` minutes later), not immediately."""
        if not self.DBConfig.GetSetting('Whitelist_Role_Sync'):
            return

        for member in role.members:
            await self._sync_add(member, ServerID)

    def _member_still_qualifies(self, member: discord.Member, ServerID: int) -> bool:
        """Returns True if `member` currently holds ANY Role -- Whitelist-Sync OR Donator, either
        category counts -- that still gates Whitelist access for `ServerID`. Used to decide whether
        losing ONE qualifying Role should actually trigger a removal, or whether another still-held
        Role keeps them qualified."""
        try:
            db_server = self.DB.GetServer(ServerID=ServerID)
        except Exception:
            # ServerID no longer exists in Servers (eg. removed via `/dbserver cleanup`, which doesn't
            # clean up ServerWhitelistRoles/ServerDonatorRoles) -- nothing left to qualify them for.
            return False
        if db_server is None:
            return False
        qualifying_role_ids = set(db_server.GetWhitelistRoles()) | set(db_server.GetDonatorRoles())
        member_role_ids = {role.id for role in member.roles}
        return not qualifying_role_ids.isdisjoint(member_role_ids)

    async def _cleanup_minecraft_whitelist(self, context: commands.Context):
        """Removes `db_user` from any role-synced Minecraft Whitelist before their linked IGN/UUID is cleared via `/link remove`.
        Must be called *before* nulling `MC_IngameName`/`MC_UUID`, since removal still needs the old identity to know who to remove."""
        if not self.DBConfig.GetSetting('Whitelist_Role_Sync'):
            return

        if not isinstance(context.author, discord.Member):
            return

        server_ids = set()
        for role in context.author.roles:
            server_ids.update(self.DB.GetServersByWhitelistRole(role.id))
            server_ids.update(self.DB.GetServersByDonatorRole(role.id))

        for server_id in server_ids:
            amp_server = self._get_amp_instance_by_server_id(server_id)
            # Only Minecraft actually keys Whitelist membership off MC_IngameName/MC_UUID today; every other
            # module's check_Whitelist/removeWhitelist is a no-op regardless of identity, so there's nothing to clean up there.
            if amp_server != None and amp_server.Module == 'Minecraft':
                await self._sync_remove(context.author, server_id)

    async def _cleanup_steam_whitelist(self, context: commands.Context):
        """Removes `db_user` from any role-synced SteamID-keyed Whitelist before their linked SteamID is cleared via `/link remove`.
        Must be called *before* nulling `SteamID`, since removal still needs the old identity to know who to remove."""
        if not self.DBConfig.GetSetting('Whitelist_Role_Sync'):
            return

        if not isinstance(context.author, discord.Member):
            return

        server_ids = set()
        for role in context.author.roles:
            server_ids.update(self.DB.GetServersByWhitelistRole(role.id))
            server_ids.update(self.DB.GetServersByDonatorRole(role.id))

        for server_id in server_ids:
            amp_server = self._get_amp_instance_by_server_id(server_id)
            # Only modules that key Whitelist membership off SteamID (currently just ARK) need cleanup here;
            # every other module's check_Whitelist/removeWhitelist is a no-op regardless of identity.
            if amp_server != None and getattr(amp_server, 'APIModule', None) == 'Ark':
                await self._sync_remove(context.author, server_id)

    # Discord Listener Events -----------------------------------------------------------------------------------------------------------------

    @commands.Cog.listener('on_member_update')
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        """Keeps AMP Whitelists in sync when a Member gains or loses a configured Whitelist-Sync
        or Donator Role. Losing a Role only triggers a removal if the Member doesn't still hold
        some OTHER qualifying Role for that same Server (`_member_still_qualifies`)."""
        if not self.DBConfig.GetSetting('Whitelist_Role_Sync'):
            return

        before_roles = {role.id for role in before.roles}
        after_roles = {role.id for role in after.roles}

        gained_roles = after_roles - before_roles
        lost_roles = before_roles - after_roles

        gained_server_ids = set()
        for role_id in gained_roles:
            gained_server_ids.update(self.DB.GetServersByWhitelistRole(role_id))
            gained_server_ids.update(self.DB.GetServersByDonatorRole(role_id))

        lost_server_ids = set()
        for role_id in lost_roles:
            lost_server_ids.update(self.DB.GetServersByWhitelistRole(role_id))
            lost_server_ids.update(self.DB.GetServersByDonatorRole(role_id))

        for server_id in gained_server_ids:
            await self._sync_add(after, server_id)

        for server_id in lost_server_ids:
            if not self._member_still_qualifies(after, server_id):
                await self._sync_remove(after, server_id)

    @commands.Cog.listener('on_member_remove')
    async def on_member_remove(self, member: discord.Member):
        """Removes a departing Member from any Whitelist their Discord Roles were gating access for."""
        if not self.DBConfig.GetSetting('Whitelist_Role_Sync'):
            return

        server_ids = set()
        for role in member.roles:
            server_ids.update(self.DB.GetServersByWhitelistRole(role.id))
            server_ids.update(self.DB.GetServersByDonatorRole(role.id))

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
            role_ids = set(db_server.GetWhitelistRoles()) | set(db_server.GetDonatorRoles())
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

    @commands.hybrid_group(name='link', description=i18n.t('commands.link.description'))
    async def link_group(self, context: commands.Context):
        if context.invoked_subcommand is None:
            await context.send(i18n.t('messages.link.need_subcommand'), ephemeral=True, delete_after=self._client.Message_Timeout)

    @link_group.command(name='minecraft', description=i18n.t('commands.link.minecraft.description'))
    async def link_minecraft(self, context: commands.Context, ign: str):
        self.logger.command(f'{context.author.name} used Link Minecraft')

        profile = self.uBot.get_minecraft_profile(ign)
        if profile == None:
            return await context.send(i18n.t('messages.link.minecraft.not_found', ign=ign), ephemeral=True, delete_after=self._client.Message_Timeout)

        embed = discord.Embed(title=i18n.t('embeds.link.minecraft_title'), description=i18n.t('embeds.link.minecraft_description', name=discord.utils.escape_markdown(profile["name"]), uuid=profile["uuid"]), color=0x808000)
        embed.set_thumbnail(url=profile['avatar'])

        def apply_minecraft_link(db_user: DB.DBUser):
            db_user.MC_IngameName = profile['name']
            db_user.MC_UUID = profile['uuid']

        view = self.uiBot.LinkConfirmView(invoker_id=context.author.id, apply=apply_minecraft_link, confirm_message=i18n.t('messages.link.minecraft.confirm', name=discord.utils.escape_markdown(profile["name"])))
        view.message = await context.send(embed=embed, view=view, ephemeral=True)

    @link_group.command(name='steam', description=i18n.t('commands.link.steam.description'))
    async def link_steam(self, context: commands.Context, steam: str):
        self.logger.command(f'{context.author.name} used Link Steam')

        if not self.uBot.steam_api_key_configured():
            return await context.send(i18n.t('messages.link.steam.not_configured'), ephemeral=True, delete_after=self._client.Message_Timeout)

        profile = self.uBot.get_steam_profile(steam)
        if profile == None:
            return await context.send(i18n.t('messages.link.steam.not_found', steam=steam), ephemeral=True, delete_after=self._client.Message_Timeout)

        embed = discord.Embed(title=i18n.t('embeds.link.steam_title'), description=i18n.t('embeds.link.steam_description', personaname=discord.utils.escape_markdown(profile["personaname"]), profileurl=profile["profileurl"], steamid=profile["steamid"]), color=0x808000)
        if profile['avatar'] != None:
            embed.set_thumbnail(url=profile['avatar'])

        def apply_steam_link(db_user: DB.DBUser):
            db_user.SteamID = profile['steamid']

        view = self.uiBot.LinkConfirmView(invoker_id=context.author.id, apply=apply_steam_link, confirm_message=i18n.t('messages.link.steam.confirm'))
        view.message = await context.send(embed=embed, view=view, ephemeral=True)

    @link_group.command(name='show', description=i18n.t('commands.link.show.description'))
    async def link_show(self, context: commands.Context):
        self.logger.command(f'{context.author.name} used Link Show')

        db_user = self.DB.GetUser(context.author.id)
        await context.send(embed=self.eBot.user_info_embed(db_user, context.author), ephemeral=True, delete_after=self._client.Message_Timeout)

    @link_group.command(name='remove', description=i18n.t('commands.link.remove.description'))
    @app_commands.choices(identity=[
        Choice(name=i18n.t('commands.link.remove.params.identity.choices.minecraft'), value='minecraft'),
        Choice(name=i18n.t('commands.link.remove.params.identity.choices.steam'), value='steam'),
    ])
    async def link_remove(self, context: commands.Context, identity: Choice[str]):
        self.logger.command(f'{context.author.name} used Link Remove')

        db_user = self.DB.GetUser(context.author.id)
        if db_user is None:
            return await context.send(i18n.t('messages.link.remove.no_accounts'), ephemeral=True, delete_after=self._client.Message_Timeout)

        if identity.value == 'minecraft':
            if db_user.MC_IngameName == None and db_user.MC_UUID == None:
                return await context.send(i18n.t('messages.link.remove.no_minecraft'), ephemeral=True, delete_after=self._client.Message_Timeout)

            # Must run before nulling the fields below; removal still needs the old IGN/UUID to know who to remove.
            await self._cleanup_minecraft_whitelist(context)
            db_user.MC_IngameName = None
            db_user.MC_UUID = None
            await context.send(i18n.t('messages.link.remove.removed_minecraft'), ephemeral=True, delete_after=self._client.Message_Timeout)
        elif identity.value == 'steam':
            if db_user.SteamID == None:
                return await context.send(i18n.t('messages.link.remove.no_steam'), ephemeral=True, delete_after=self._client.Message_Timeout)

            # Must run before nulling the field below; removal still needs the old SteamID to know who to remove.
            await self._cleanup_steam_whitelist(context)
            db_user.SteamID = None
            await context.send(i18n.t('messages.link.remove.removed_steam'), ephemeral=True, delete_after=self._client.Message_Timeout)

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
            name = role.name if role != None else i18n.t('messages.whitelist_role.deleted_role_placeholder', role_id=role_id)
            if current.lower() in name.lower():
                choices.append(app_commands.Choice(name=name, value=str(role_id)))

        return choices[:25]

    async def autocomplete_donator_roles(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        """Autocomplete for Discord Roles currently gating Donator access on the already-selected `server` option."""
        server = interaction.namespace.server
        if not server:
            return []

        amp_server = self.uBot.serverparse(server)
        if amp_server == None:
            return []

        db_server = self.DB.GetServer(amp_server.InstanceID)
        choices = []
        for role_id in db_server.GetDonatorRoles():
            role = interaction.guild.get_role(role_id)
            name = role.name if role != None else i18n.t('messages.donator_role.deleted_role_placeholder', role_id=role_id)
            if current.lower() in name.lower():
                choices.append(app_commands.Choice(name=name, value=str(role_id)))

        return choices[:25]

    # Whitelist Role Management Commands (attached to `server settings`) ----------------------------------------------------------------------

    @commands.hybrid_command(name='whitelist_role_add', description=i18n.t('commands.server.settings.whitelist_role_add.description'))
    @utils_permissions.role_check()
    @app_commands.autocomplete(server=utils_discord.autocomplete_servers)
    async def whitelist_role_add(self, context: commands.Context, server: str, role: discord.Role):
        self.logger.command(f'{context.author.name} used Whitelist Role Add')

        amp_server = await self.uBot._serverCheck(context, server, False)
        if amp_server:
            db_server = self.DB.GetServer(amp_server.InstanceID)
            server_name = amp_server.FriendlyName if amp_server.FriendlyName != None else amp_server.InstanceName

            if role.id in db_server.GetWhitelistRoles():
                return await context.send(i18n.t('messages.whitelist_role.add.already_gating', role_name=role.name, server_name=server_name), ephemeral=True, delete_after=self._client.Message_Timeout)

            db_server.AddWhitelistRole(role.id)
            await self._sync_role_members_now(role, db_server.ID)
            await context.send(i18n.t('messages.whitelist_role.add.success', role_name=role.name, server_name=server_name), ephemeral=True, delete_after=self._client.Message_Timeout)

    @commands.hybrid_command(name='whitelist_role_remove', description=i18n.t('commands.server.settings.whitelist_role_remove.description'))
    @utils_permissions.role_check()
    @app_commands.autocomplete(server=utils_discord.autocomplete_servers, role=autocomplete_whitelist_roles)
    async def whitelist_role_remove(self, context: commands.Context, server: str, role: str):
        self.logger.command(f'{context.author.name} used Whitelist Role Remove')

        amp_server = await self.uBot._serverCheck(context, server, False)
        if amp_server:
            db_server = self.DB.GetServer(amp_server.InstanceID)
            server_name = amp_server.FriendlyName if amp_server.FriendlyName != None else amp_server.InstanceName

            if not role.isdigit():
                return await context.send(i18n.t('messages.whitelist_role.remove.not_a_role', role=role), ephemeral=True, delete_after=self._client.Message_Timeout)

            role_id = int(role)
            discord_role = context.guild.get_role(role_id)
            role_name = discord_role.name if discord_role != None else i18n.t('messages.whitelist_role.deleted_role_placeholder', role_id=role_id)

            if role_id not in db_server.GetWhitelistRoles():
                return await context.send(i18n.t('messages.whitelist_role.remove.not_gating', role_name=role_name, server_name=server_name), ephemeral=True, delete_after=self._client.Message_Timeout)

            db_server.DelWhitelistRole(role_id)
            await context.send(i18n.t('messages.whitelist_role.remove.success', role_name=role_name, server_name=server_name), ephemeral=True, delete_after=self._client.Message_Timeout)

    @commands.hybrid_command(name='whitelist_role_list', description=i18n.t('commands.server.settings.whitelist_role_list.description'))
    @utils_permissions.role_check()
    @app_commands.autocomplete(server=utils_discord.autocomplete_servers)
    async def whitelist_role_list(self, context: commands.Context, server: str):
        self.logger.command(f'{context.author.name} used Whitelist Role List')

        amp_server = await self.uBot._serverCheck(context, server, False)
        if amp_server:
            db_server = self.DB.GetServer(amp_server.InstanceID)
            server_name = amp_server.FriendlyName if amp_server.FriendlyName != None else amp_server.InstanceName
            role_ids = db_server.GetWhitelistRoles()

            if not len(role_ids):
                return await context.send(i18n.t('messages.whitelist_role.list.none_configured', server_name=server_name), ephemeral=True, delete_after=self._client.Message_Timeout)

            role_mentions = []
            for role_id in role_ids:
                role = context.guild.get_role(role_id)
                role_mentions.append(role.mention if role != None else i18n.t('messages.whitelist_role.deleted_role_mention', role_id=role_id))

            await context.send(i18n.t('messages.whitelist_role.list.result', server_name=server_name, role_mentions=", ".join(role_mentions)), ephemeral=True, delete_after=self._client.Message_Timeout)

    # Donator Role Management Commands (attached to `server settings`) -- any one of these Roles automatically
    # grants Whitelist access via the same Whitelist-Sync mechanism as `whitelist_role_add` above -----------------

    @commands.hybrid_command(name='donator_role_add', description=i18n.t('commands.server.settings.donator_role_add.description'))
    @utils_permissions.role_check()
    @app_commands.autocomplete(server=utils_discord.autocomplete_servers)
    async def donator_role_add(self, context: commands.Context, server: str, role: discord.Role):
        self.logger.command(f'{context.author.name} used Donator Role Add')

        amp_server = await self.uBot._serverCheck(context, server, False)
        if amp_server:
            db_server = self.DB.GetServer(amp_server.InstanceID)
            server_name = amp_server.FriendlyName if amp_server.FriendlyName != None else amp_server.InstanceName

            if role.id in db_server.GetDonatorRoles():
                return await context.send(i18n.t('messages.donator_role.add.already_gating', role_name=role.name, server_name=server_name), ephemeral=True, delete_after=self._client.Message_Timeout)

            db_server.AddDonatorRole(role.id)
            await self._sync_role_members_now(role, db_server.ID)
            await context.send(i18n.t('messages.donator_role.add.success', role_name=role.name, server_name=server_name), ephemeral=True, delete_after=self._client.Message_Timeout)

    @commands.hybrid_command(name='donator_role_remove', description=i18n.t('commands.server.settings.donator_role_remove.description'))
    @utils_permissions.role_check()
    @app_commands.autocomplete(server=utils_discord.autocomplete_servers, role=autocomplete_donator_roles)
    async def donator_role_remove(self, context: commands.Context, server: str, role: str):
        self.logger.command(f'{context.author.name} used Donator Role Remove')

        amp_server = await self.uBot._serverCheck(context, server, False)
        if amp_server:
            db_server = self.DB.GetServer(amp_server.InstanceID)
            server_name = amp_server.FriendlyName if amp_server.FriendlyName != None else amp_server.InstanceName

            if not role.isdigit():
                return await context.send(i18n.t('messages.donator_role.remove.not_a_role', role=role), ephemeral=True, delete_after=self._client.Message_Timeout)

            role_id = int(role)
            discord_role = context.guild.get_role(role_id)
            role_name = discord_role.name if discord_role != None else i18n.t('messages.donator_role.deleted_role_placeholder', role_id=role_id)

            if role_id not in db_server.GetDonatorRoles():
                return await context.send(i18n.t('messages.donator_role.remove.not_gating', role_name=role_name, server_name=server_name), ephemeral=True, delete_after=self._client.Message_Timeout)

            db_server.DelDonatorRole(role_id)
            await context.send(i18n.t('messages.donator_role.remove.success', role_name=role_name, server_name=server_name), ephemeral=True, delete_after=self._client.Message_Timeout)

    @commands.hybrid_command(name='donator_role_list', description=i18n.t('commands.server.settings.donator_role_list.description'))
    @utils_permissions.role_check()
    @app_commands.autocomplete(server=utils_discord.autocomplete_servers)
    async def donator_role_list(self, context: commands.Context, server: str):
        self.logger.command(f'{context.author.name} used Donator Role List')

        amp_server = await self.uBot._serverCheck(context, server, False)
        if amp_server:
            db_server = self.DB.GetServer(amp_server.InstanceID)
            server_name = amp_server.FriendlyName if amp_server.FriendlyName != None else amp_server.InstanceName
            role_ids = db_server.GetDonatorRoles()

            if not len(role_ids):
                return await context.send(i18n.t('messages.donator_role.list.none_configured', server_name=server_name), ephemeral=True, delete_after=self._client.Message_Timeout)

            role_mentions = []
            for role_id in role_ids:
                role = context.guild.get_role(role_id)
                role_mentions.append(role.mention if role != None else i18n.t('messages.donator_role.deleted_role_mention', role_id=role_id))

            await context.send(i18n.t('messages.donator_role.list.result', server_name=server_name, role_mentions=", ".join(role_mentions)), ephemeral=True, delete_after=self._client.Message_Timeout)

    # Whitelist Sync Global Settings --------------------------------------------------------------------------------------------------------

    @commands.hybrid_group(name='whitelist_sync', description=i18n.t('commands.whitelist_sync.description'))
    @utils_permissions.role_check()
    async def whitelist_sync_settings(self, context: commands.Context):
        if context.invoked_subcommand is None:
            await context.send(i18n.t('common.invalid_command'), ephemeral=True, delete_after=self._client.Message_Timeout)

    @whitelist_sync_settings.command(name='enabled', description=i18n.t('commands.whitelist_sync.enabled.description'))
    @utils_permissions.role_check()
    @app_commands.choices(flag=[Choice(name=i18n.t('common.bool.true'), value=1), Choice(name=i18n.t('common.bool.false'), value=0)])
    async def whitelist_sync_enabled(self, context: commands.Context, flag: Choice[int]):
        self.logger.command(f'{context.author.name} used Whitelist Sync Enabled')

        self.DBConfig.SetSetting('Whitelist_Role_Sync', flag.value)
        if flag.value == 1:
            if not self.whitelist_role_sync_reconciliation.is_running():
                interval = int(self.DBConfig.GetSetting('Whitelist_Role_Sync_Interval') or 15)
                self.whitelist_role_sync_reconciliation.change_interval(minutes=interval)
                self.whitelist_role_sync_reconciliation.start()
            await context.send(i18n.t('messages.whitelist_sync.enabled.on'), ephemeral=True, delete_after=self._client.Message_Timeout)
        else:
            if self.whitelist_role_sync_reconciliation.is_running():
                self.whitelist_role_sync_reconciliation.stop()
            await context.send(i18n.t('messages.whitelist_sync.enabled.off'), ephemeral=True, delete_after=self._client.Message_Timeout)

    @whitelist_sync_settings.command(name='interval', description=i18n.t('commands.whitelist_sync.interval.description'))
    @utils_permissions.role_check()
    @app_commands.describe(minutes=i18n.t('commands.whitelist_sync.interval.params.minutes.description'))
    async def whitelist_sync_interval(self, context: commands.Context, minutes: app_commands.Range[int, 1, 1440] = 15):
        self.logger.command(f'{context.author.name} used Whitelist Sync Interval')

        self.DBConfig.SetSetting('Whitelist_Role_Sync_Interval', minutes)
        if self.whitelist_role_sync_reconciliation.is_running():
            self.whitelist_role_sync_reconciliation.change_interval(minutes=minutes)
        interval_str = i18n.t_plural('common.minutes', count=minutes)
        await context.send(i18n.t('messages.whitelist_sync.interval.result', interval=interval_str), ephemeral=True, delete_after=self._client.Message_Timeout)


async def setup(client: commands.Bot):
    await client.add_cog(WhitelistSync(client))
