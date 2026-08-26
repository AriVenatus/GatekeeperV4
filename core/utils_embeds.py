# Copyright (C) 2021-2022 Katelynn Cadwallader
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations
import logging
import discord
from discord.ext import commands

from core import DB
from core import AMP_Handler
from core import utils
from core import i18n


class botEmbeds:
    """Gatekeeper Embeds/Banners"""

    def __init__(self, client: commands.Bot = None):
        self._client = client
        self.logger = logging.getLogger(__name__)
        self.logger.debug('Utils Bot Loaded')

        self.DBHandler = DB.getDBHandler()
        self.DB = self.DBHandler.DB  # Main Database object
        self.DBConfig = self.DBHandler.DBConfig
        self.uBot = utils.botUtils(client)

        self.AMPHandler = AMP_Handler.getAMPHandler()
        self.AMPInstances = self.AMPHandler.AMP_Instances
        self.AMPServer_Avatar_urls = []

    def _bool_str(self, value) -> str:
        """Renders the literal word True/False -- this reflects raw internal state, not UI
        copy, so it must stay fixed and not change with the active language."""
        return f'`{bool(value)}`'

    def _yes_no_str(self, value) -> str:
        """Localized Yes/No rendering for a raw internal boolean. Deliberately scoped to
        `server_display_embed`'s Info field ONLY -- not shared via `_bool_str()`, and uses
        dedicated `common.bool.yes`/`common.bool.no` keys, not `common.bool.true`/
        `common.bool.false` (those stay fixed literals reserved for Choice-dropdown-label
        reuse elsewhere). See CLAUDE.md's i18n notes for why this is intentionally scoped
        rather than applied to every `_bool_str()` call site."""
        key = 'common.bool.yes' if bool(value) else 'common.bool.no'
        return f'`{i18n.t(key)}`'

    def _filter_type_str(self, value) -> str:
        """Console_Filtered_Type: 0 = Blacklist, 1 = Whitelist."""
        key = 'embeds.common.filter_type.whitelist' if bool(value) else 'embeds.common.filter_type.blacklist'
        return f'`{i18n.t(key)}`'

    def _player_load(self, online: str | None, maximum: str | None, length: int = 10) -> tuple[str, float | None]:
        """Renders `(online, maximum)` (both strings, straight from AMP) as a Unicode block bar
        plus its ratio in [0, 1]. Returns `('', None)` if either value isn't a usable positive int."""
        if online is None or maximum is None:
            return '', None
        try:
            online_i = int(online)
            max_i = int(maximum)
        except ValueError:
            return '', None
        if max_i <= 0:
            return '', None
        ratio = max(0.0, min(1.0, online_i / max_i))
        filled = round(ratio * length)
        return ('▰' * filled) + ('▱' * (length - filled)), ratio

    def default_embedmsg(self, title, context: commands.Context, description=None, field=None, field_value=None) -> discord.Embed:
        """This Embed has only one Field Entry."""
        embed = discord.Embed(title=title, description=description, color=0x808000)  # color is RED
        embed.set_author(name=context.author.display_name, icon_url=context.author.avatar)
        embed.add_field(name=field, value=field_value, inline=False)
        return embed

    async def server_info_embed(self, server: AMP_Handler.AMP.AMPInstance, context: commands.Context) -> discord.Embed:
        """For Individual Server info embed replies"""
        db_server = self.DB.GetServer(InstanceID=server.InstanceID)
        server_name = db_server.InstanceName
        if db_server.DisplayName != None:
            server_name = db_server.DisplayName

        embed = discord.Embed(title=f'__**{server_name}**__ - {[server.TargetName]}', color=0x00ff00, description=server.Description)

        discord_role = db_server.Discord_Role
        if discord_role != None:
            discord_role = context.guild.get_role(int(db_server.Discord_Role)).name

        avatar = await self.uBot.validate_avatar(db_server)
        if avatar != None:
            embed.set_thumbnail(url=avatar)

        embed.add_field(name=i18n.t('embeds.server_info.host'), value=f'`{db_server.Host}`', inline=False)
        embed.add_field(name=i18n.t('common.embed.donator_only'), value=self._bool_str(db_server.Donator), inline=True)
        embed.add_field(name=i18n.t('common.embed.whitelist_open'), value=self._bool_str(db_server.Whitelist), inline=True)
        embed.add_field(name=i18n.t('embeds.server_info.role'), value=f'`{discord_role}`', inline=False)
        embed.add_field(name=i18n.t('embeds.server_info.hidden'), value=self._bool_str(db_server.Hidden), inline=True)
        embed.add_field(name=i18n.t('embeds.server_info.whitelist_hidden'), value=self._bool_str(db_server.Whitelist_disabled), inline=True)

        embed.add_field(name=i18n.t('embeds.server_info.filtered_console'), value=self._bool_str(db_server.Console_Filtered), inline=False)
        embed.add_field(name=i18n.t('embeds.server_info.console_filter_type'), value=self._filter_type_str(db_server.Console_Filtered_Type), inline=True)
        if db_server.Discord_Console_Channel != None:
            discord_channel = context.guild.get_channel(db_server.Discord_Console_Channel)
            embed.add_field(name=i18n.t('embeds.server_info.console_channel'), value=f'`{discord_channel.name}`', inline=False)
        else:
            embed.add_field(name=i18n.t('embeds.server_info.console_channel'), value=f'`{db_server.Discord_Console_Channel}`', inline=False)

        embed.add_field(name=i18n.t('embeds.server_info.chat_prefix'), value=f'`{db_server.Discord_Chat_Prefix}`', inline=False)
        if db_server.Discord_Chat_Channel != None:
            discord_channel = context.guild.get_channel(db_server.Discord_Chat_Channel)
            embed.add_field(name=i18n.t('embeds.server_info.chat_channel'), value=f'`{discord_channel.name}`', inline=True)
        else:
            embed.add_field(name=i18n.t('embeds.server_info.chat_channel'), value=f'`{db_server.Discord_Chat_Channel}`', inline=True)

        if db_server.Discord_Event_Channel != None:
            discord_channel = context.guild.get_channel(db_server.Discord_Event_Channel)
            embed.add_field(name=i18n.t('embeds.server_info.event_channel'), value=f'`{discord_channel.name}`', inline=True)
        else:
            embed.add_field(name=i18n.t('embeds.server_info.event_channel'), value=f'`{db_server.Discord_Event_Channel}`', inline=True)
        embed.set_footer(text=f'InstanceID: {server.InstanceID}')
        return embed

    async def server_display_embed(self, server_list: list[DB.DBServer], banner_name: str, guild: discord.Guild = None, ) -> list[discord.Embed]:
        """Used for Banner Groups and Display"""
        embed_list = []
        for db_server in server_list:
            if db_server == None:
                self.DB.Remove_Server_from_BannerGroup(banner_groupname=banner_name, instanceID=db_server.InstanceID)

            try:
                server = self.AMPInstances[db_server.InstanceID]
            except:
                self.DB.Remove_Server_from_BannerGroup(banner_groupname=banner_name, instanceID=db_server.InstanceID)

            # If no DB Server or the Server is Hidden; skip.
            if db_server == None or db_server.Hidden == 1:
                continue

            instance_status = i18n.t('embeds.server_display.status_offline_icon')
            dedicated_status = i18n.t('embeds.server_display.status_offline_icon')
            Users = None
            User_list = None
            # This is for the Instance
            if server.Running:
                instance_status = i18n.t('embeds.server_display.status_online_icon')
                # ADS AKA Application status
                if server._ADScheck() and server.ADS_Running:
                    dedicated_status = i18n.t('embeds.server_display.status_online_icon')
                    Users = server.getUsersOnline()
                    if len(server.getUserList()) >= 1:
                        User_list = (', ').join(server.getUserList())

            bar, ratio = self._player_load(*Users) if Users != None else ('', None)

            # Discord Role color takes priority; otherwise a green/yellow/red status color.
            embed_color = None
            if guild != None and db_server.Discord_Role != None:
                db_server_role = guild.get_role(int(db_server.Discord_Role))
                if db_server_role != None:
                    embed_color = db_server_role.color

            if embed_color == None:
                if Users == None:
                    embed_color = 0xE74C3C  # Offline
                elif ratio != None and ratio >= 0.9:
                    embed_color = 0xF1C40F  # Online, nearly full
                else:
                    embed_color = 0x2ECC71  # Online, healthy

            server_name = server.FriendlyName
            if server.DisplayName != None:
                server_name = db_server.DisplayName

            embed = discord.Embed(title=f'**=======  {server_name}  =======**', description=server.Description, color=embed_color)
            # This is for future custom avatar support.
            avatar = await self.uBot.validate_avatar(db_server)
            if avatar != None:
                embed.set_thumbnail(url=avatar)

            status_value = f"{i18n.t('embeds.server_display.instance_status_label')} {instance_status}\n{i18n.t('common.embed.dedicated_server_status')} {dedicated_status}"
            embed.add_field(name=i18n.t('embeds.server_display.status_label'), value=status_value, inline=False)

            info_value = f"{i18n.t('common.embed.host_bold')} `{db_server.Host}`\n{i18n.t('embeds.server_display.donator')} {self._yes_no_str(db_server.Donator)}\n{i18n.t('embeds.server_display.whitelist_open')} {self._yes_no_str(db_server.Whitelist)}"
            if getattr(server, 'APIModule', None) == 'Ark':
                ark_map = server.getMap()
                if ark_map != None:
                    info_value += f"\n{i18n.t('embeds.server_display.map')} `{ark_map}`"
            embed.add_field(name=i18n.t('embeds.server_display.info_label'), value=info_value, inline=True)

            if Users != None:
                embed.add_field(name=i18n.t('embeds.server_display.players'), value=f'{bar} `{Users[0]}/{Users[1]}`', inline=True)
            else:
                embed.add_field(name=i18n.t('embeds.server_display.player_limit'), value=f'`{Users}`', inline=True)
            embed.add_field(name=i18n.t('embeds.server_display.players_online'), value=f'`{User_list}`', inline=False)

            # Discord renders this client-side, live, in each viewer's own timezone -- no
            # Banner_Timezone/Banner_Use_12Hour dependency and nothing to keep in sync.
            embed.add_field(name=i18n.t('embeds.server_display.last_updated_label'), value=discord.utils.format_dt(discord.utils.utcnow(), style='R'), inline=False)

            embed_list.append(embed)

        return embed_list

    async def server_status_embed(self, context: commands.Context, server: AMP_Handler.AMP.AMPInstance, TPS=None, Users=None, CPU=None, Memory=None, Uptime=None, Users_Online=None) -> discord.Embed:
        """This is the Server Status Embed Message"""
        db_server = self.DB.GetServer(InstanceID=server.InstanceID)

        if server.Running:
            instance_status = i18n.t('common.status.online')
        else:
            instance_status = i18n.t('common.status.offline')

        if server.ADS_Running:
            server_status = i18n.t('common.status.online')
        else:
            server_status = i18n.t('common.status.offline')

        embed_color = 0x71368a
        if db_server.Discord_Role != None:
            db_server_role = context.guild.get_role(int(db_server.Discord_Role))
            if db_server_role != None:
                embed_color = db_server_role.color

        server_name = server.FriendlyName
        if server.DisplayName != None:
            server_name = db_server.DisplayName

        embed = discord.Embed(title=f"{server_name} - [{server.TargetName}]", description=i18n.t('embeds.server_status.description', instance_status=instance_status), color=embed_color)

        avatar = await self.uBot.validate_avatar(db_server)
        if avatar != None:
            embed.set_thumbnail(url=avatar)

        embed.add_field(name=i18n.t('common.embed.dedicated_server_status'), value=f'`{server_status}`', inline=True)

        if db_server.Host != None:
            embed.add_field(name=i18n.t('embeds.server_status.host'), value=f'`{db_server.Host}`', inline=True)

        if getattr(server, 'APIModule', None) == 'Ark':
            ark_map = server.getMap()
            if ark_map != None:
                embed.add_field(name=i18n.t('embeds.server_status.map'), value=f'`{ark_map}`', inline=True)

        # embed.add_field(name='\u1CBC\u1CBC',value='\u1CBC\u1CBC',inline=False)
        embed.add_field(name=i18n.t('common.embed.donator_only'), value=self._bool_str(db_server.Donator), inline=True)
        embed.add_field(name=i18n.t('common.embed.whitelist_open'), value=self._bool_str(db_server.Whitelist), inline=True)
        # embed.add_field(name='\u1CBC\u1CBC',value='\u1CBC\u1CBC',inline=False) #This Generates a BLANK Field entirely.

        if server.ADS_Running:
            embed.add_field(name=i18n.t('embeds.server_status.tps'), value=f'`{TPS}`', inline=True)
            embed.add_field(name=i18n.t('embeds.server_status.player_count'), value=f'`{Users[0]}/{Users[1]}`', inline=True)
            embed.add_field(name=i18n.t('embeds.server_status.memory_usage'), value=f'`{Memory[0]}/{Memory[1]}`', inline=True)
            embed.add_field(name=i18n.t('embeds.server_status.cpu_usage'), value=f'`{CPU}/100%`', inline=True)
            #!UPTIME is disabled until AMP Impliments the feature.
            #embed.add_field(name='Uptime', value=Uptime, inline=True)
            embed.add_field(name=i18n.t('embeds.server_status.players_online'), value=f'`{Users_Online}`', inline=True)
        embed.set_footer(text=f'InstanceID: {server.InstanceID}')
        return embed

    def bot_settings_embed(self, context: commands.Context) -> discord.Embed:
        """Default Embed Reply for command /bot settings, please pass in a List of Dictionaries eg {'setting_name': 'value'}"""
        embed = discord.Embed(title=i18n.t('embeds.bot_settings.title'), color=0x71368a)
        embed.set_thumbnail(url=context.guild.icon)
        embed.add_field(name='\u1CBC\u1CBC', value='\u1CBC\u1CBC', inline=False)

        # This allows me to control which settings display first.
        layout = ["bot_version",
                  "db_version",
                  "guild_id",
                  "moderator_role_id",
                  "permissions",
                  "message_timeout",
                  "banner_type",
                  "banner_auto_update",
                  "whitelist_request_channel",
                  "whitelist_role_sync_interval",
                  "whitelist_sync_notify_channel"]

        # Take our list and store it in a seperate list and lowercase the strings.
        db_config_settingslist = [x.lower() for x in self.DBConfig.GetSettingList()]
        for key in layout:
            # If the key is not in the DB; skip.
            if key not in db_config_settingslist:
                continue

            db_config_settingslist.remove(key)
            value = self.DBConfig.GetSetting(key)
            key = key.lower()
            if key == 'whitelist_request_channel':
                if value != 'None':
                    value = context.guild.get_channel(value)

                embed.add_field(name=i18n.t('embeds.bot_settings.whitelist_request_channel'), value=f'`{value.name.title() if value != None else i18n.t("common.embed.not_set")}`', inline=False)

            elif key == 'whitelist_sync_notify_channel':
                # A Channel ID, not a boolean -- same reasoning as whitelist_role_sync_interval
                # above, needs its own branch instead of falling into the generic int fallback.
                if value != 'None':
                    value = context.guild.get_channel(value)

                embed.add_field(name=i18n.t('embeds.bot_settings.whitelist_sync_notify_channel'), value=f'`{value.name.title() if value != None else i18n.t("common.embed.not_set")}`', inline=False)

            elif key == 'message_timeout':
                embed.add_field(name=i18n.t('embeds.bot_settings.message_timeout'), value=f'`{i18n.t("embeds.bot_settings.seconds", value=value)}`', inline=False)

            elif key == 'permissions':
                if value == 0:
                    value = i18n.t('embeds.bot_settings.permissions_default')
                elif value == 1:
                    value = i18n.t('embeds.bot_settings.permissions_custom')
                embed.add_field(name=i18n.t('embeds.bot_settings.permissions'), value=f'`{value}`', inline=True)

            elif key == 'banner_type':
                if value == 0:
                    value = i18n.t('embeds.bot_settings.banner_type_embeds')
                elif value == 1:
                    value = i18n.t('embeds.bot_settings.banner_type_images')
                embed.add_field(name=i18n.t('embeds.bot_settings.banner_type'), value=f'`{value}`', inline=False)

            elif key == 'banner_auto_update':
                embed.add_field(name=i18n.t('embeds.bot_settings.banner_auto_update'), value=self._bool_str(value == 1), inline=True)

            elif key == 'whitelist_role_sync_interval':
                # A real minute count, not a boolean -- the generic int-as-bool fallback below
                # would otherwise render any nonzero value as `True`.
                embed.add_field(name=i18n.t('embeds.bot_settings.whitelist_role_sync_interval'), value=f'`{i18n.t_plural("common.minutes", count=int(value))}`', inline=True)

            elif key == 'db_version':
                embed.add_field(name=i18n.t('embeds.bot_settings.db_version'), value=f'`{value}`', inline=True)

            elif key == 'bot_version':
                embed.add_field(name=i18n.t('embeds.bot_settings.bot_version'), value=f'`{value}`', inline=True)

            elif key == 'guild_id':
                if self._client != None and value != 'None':
                    value = self._client.get_guild(value)

                    embed.add_field(name=i18n.t('embeds.bot_settings.guild_id'), value=f'`{value.name.title() if value != None else i18n.t("common.embed.not_set")}`', inline=False)

            elif key == 'moderator_role_id':
                if value != 'None':
                    value = context.guild.get_role(value)

                embed.add_field(name=i18n.t('embeds.bot_settings.moderator_role'), value=f'`{value.name.title() if value != None else i18n.t("common.embed.not_set")}`', inline=True)

        # This iterates through the remaining keys of the Settings List and adds them to the Embed.
        # NOTE: these field NAMES stay English-only by design -- they're auto-titled from
        # whatever DBConfig key a future maintainer adds (DBConfig.SetSetting accepts arbitrary
        # keys at any time), so there's no finite, translatable key set for them. Only the
        # boolean VALUE (not the auto-generated name) goes through i18n.
        for key in db_config_settingslist:
            value = self.DBConfig.GetSetting(key)
            key = key.replace("_", " ").title()  # Turns `auto_whitelist`` into `Auto Whitelist`

            # For our possible bool entries (0, 1) to True and False respectively.
            if type(value) == int:
                embed.add_field(name=key, value=self._bool_str(value != 0), inline=False)
            else:
                embed.add_field(name=key, value=f'`{value}`', inline=False)

        return embed

    def user_info_embed(self, db_user: DB.DBUser, discord_user: discord.User = None) -> discord.Embed:
        if discord_user != None:
            embed = discord.Embed(title=f'{discord_user.name}', color=discord_user.color)
            embed.add_field(name=i18n.t('embeds.user_info.discord_id'), value=f'`{discord_user.id}`', inline=False)
            if discord_user.avatar != None:
                embed.set_thumbnail(url=discord_user.avatar.url)
        else:
            # Fallback for when the Discord Account can no longer be resolved (eg. they left/deleted their Account).
            title = db_user.DiscordName if db_user != None and db_user.DiscordName != None else i18n.t('embeds.user_info.unknown_user')
            discord_id = db_user.DiscordID if db_user != None else i18n.t('embeds.user_info.unknown')
            embed = discord.Embed(title=title, description=i18n.t('embeds.user_info.unresolvable'), color=0x808000)
            embed.add_field(name=i18n.t('embeds.user_info.discord_id'), value=f'`{discord_id}`', inline=False)

        embed.add_field(name=i18n.t('embeds.user_info.in_database'), value=f'`{db_user != None}`')
        if db_user != None:
            if db_user.MC_IngameName != None:
                embed.add_field(name=i18n.t('embeds.user_info.minecraft_ign'), value=f'`{db_user.MC_IngameName}`', inline=False)

            if db_user.MC_UUID != None:
                embed.add_field(name=i18n.t('embeds.user_info.minecraft_uuid'), value=f'`{db_user.MC_UUID}`', inline=True)

            if db_user.SteamID != None:
                embed.add_field(name=i18n.t('embeds.user_info.steam_id'), value=f'`{db_user.SteamID}`', inline=False)

            if db_user.Role != None:
                embed.add_field(name=i18n.t('embeds.user_info.permission_role'), value=f'`{db_user.Role}`', inline=False)

        return embed
