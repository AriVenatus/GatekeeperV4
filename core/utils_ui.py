from __future__ import annotations
import logging
import io
import sqlite3
from typing import Callable
from PIL import Image
import random

import discord
from discord.ext import commands
from discord.ui import Button, View
import asyncio

from core import DB
from core import AMP_Handler
from core import utils
from core import i18n


class ServerButton(Button):
    """Custom Start Button for when Servers are Offline."""

    def __init__(self, server: AMP_Handler.AMP.AMPInstance, view: discord.ui.View, function, label: str, callback_label: str, callback_disabled: bool, action: str, style=discord.ButtonStyle.green, context=None):
        # `custom_id`/`permission_node` are derived from `action` (a fixed, never-translated
        # identifier), NOT from the display `label` -- the label is user-facing text that changes
        # with the active language, but `server.start`/`server.stop`/etc. are permission nodes
        # checked against bot_perms.json and must stay stable across a language switch.
        super().__init__(label=label, style=style, custom_id=action)
        self.logger = logging.getLogger()
        self.server = server
        self.context = context
        self._label = label
        self.permission_node = 'server.' + action

        self.callback_label = callback_label
        self.callback_disabled = callback_disabled

        self._function = function
        self._view = view
        view.add_item(self)

    async def callback(self, interaction):
        """This is called when a button is interacted with."""
        if not await utils.async_rolecheck(interaction, self.permission_node):
            return
        self._interaction = interaction
        self.label = self.callback_label
        self.disabled = self.callback_disabled
        self._function()
        await interaction.response.edit_message(view=self._view)
        await asyncio.sleep(30)
        await self.reset()

    async def reset(self):
        self.logger.info('Resetting Buttons...')
        self.label = self._label
        self.disabled = False
        # server_embed = await self._view.update_view()
        await self._interaction.followup.edit_message(message_id=self._interaction.message.id, view=self._view)


class StartButton(ServerButton):
    def __init__(self, server, view, function):
        super().__init__(server=server, view=view, function=function, action='start', label=i18n.t('ui.server_button.start'), callback_label=i18n.t('ui.server_button.starting'), callback_disabled=True, style=discord.ButtonStyle.green)


class StopButton(ServerButton):
    def __init__(self, server, view, function):
        super().__init__(server=server, view=view, function=function, action='stop', label=i18n.t('ui.server_button.stop'), callback_label=i18n.t('ui.server_button.stopping'), callback_disabled=True, style=discord.ButtonStyle.red)


class RestartButton(ServerButton):
    def __init__(self, server, view, function):
        super().__init__(server=server, view=view, function=function, action='restart', label=i18n.t('ui.server_button.restart'), callback_label=i18n.t('ui.server_button.restarting'), callback_disabled=True, style=discord.ButtonStyle.blurple)


class KillButton(ServerButton):
    def __init__(self, server, view, function):
        super().__init__(server=server, view=view, function=function, action='kill', label=i18n.t('ui.server_button.kill'), callback_label=i18n.t('ui.server_button.killed'), callback_disabled=True, style=discord.ButtonStyle.danger)


class StatusView(View):
    def __init__(self, timeout=180, context: commands.Context = None, amp_server: AMP_Handler.AMP.AMPInstance = None):
        super().__init__(timeout=timeout)
        self.server = amp_server
        self.context = context
        self.uBot = utils.botUtils()

    async def on_timeout(self):
        """This Removes all the Buttons after timeout has expired"""
        self.stop()


def banner_file_handler(image: Image.Image):
    with io.BytesIO() as image_binary:
        image.save(image_binary, 'PNG')
        image_binary.seek(0)
        return discord.File(fp=image_binary, filename='image.png')


# Maps each Banner Editor field's stable (never-translated) SelectOption `value` to the i18n key
# suffix for its display text -- shared between the SelectOption label AND the Modal title that
# opens for it, so the two are always consistent (they used to diverge: the modal title was
# derived from the raw value via `.replace("_", " ")` instead of reusing the option's own label).
BANNER_FIELD_LABEL_KEYS = {
    'color_whitelist_open': 'whitelist_open_color',
    'color_whitelist_closed': 'whitelist_closed_color',
    'color_donator': 'donator_color',
    'blur_background_amount': 'blur_background',
    'color_header': 'header_color',
    'color_body': 'body_color',
    'color_host': 'host_color',
    'color_status_online': 'status_online_color',
    'color_status_offline': 'status_offline_color',
    'color_player_limit_min': 'player_limit_min_color',
    'color_player_limit_max': 'player_limit_max_color',
    'color_player_online': 'player_online_color',
}


def banner_field_label(value: str) -> str:
    return i18n.t(f'ui.banner_editor.fields.{BANNER_FIELD_LABEL_KEYS[value]}')


class Whitelist_view(View):
    """Whitelist Request View"""

    def __init__(self, client: discord.Client, discord_message: discord.Message, whitelist_message: discord.Message, amp_server: AMP_Handler.AMP.AMPInstance, context: commands.Context, timeout: float = None):
        self.logger = logging.getLogger()
        self.DB = DB.getDBHandler().DB
        self._client = client
        self._context = context
        self._whitelist_message = whitelist_message
        self._amp_server = amp_server

        # This is for when Auto-Whitelisting is Disabled to prevent the View from timing out...
        if timeout != None:
            # Converts my Minutes value I pass in into seconds which is what `Views` rely on..
            timeout = (timeout * 60)

        super().__init__(timeout=timeout)
        self.add_item(Accept_Whitelist_Button(discord_message=discord_message, view=self, client=client, amp_server=amp_server))
        self.add_item(Deny_Whitelist_Button(discord_message=discord_message, view=self, client=client, amp_server=amp_server))

    async def _whitelist_handler(self):
        db_server = self.DB.GetServer(self._amp_server.InstanceID)
        self.logger.dev(f'Whitelist Request; Attempting to Whitelist {self._whitelist_message.author.name} on {db_server.FriendlyName}')
        # This handles all the Discord Role stuff.
        if db_server != None and db_server.Discord_Role != None:
            discord_role = self._client.uBot.role_parse(db_server.Discord_Role, self._context, self._context.guild.id)
            discord_user = self._client.uBot.user_parse(self._context.author.id, self._context, self._context.guild.id)
            await discord_user.add_roles(discord_role, reason='Auto Whitelisting')

        # This is for all the Replies
        if len(self.DB.GetAllWhitelistReplies()) != 0:
            whitelist_reply = random.choice(self.DB.GetAllWhitelistReplies())
            await self._context.message.channel.send(content=f'{self._context.author.mention} \n{self._client.uBot.whitelist_reply_handler(message= whitelist_reply, context= self._context, server= self._amp_server)}', delete_after=self._client.Message_Timeout)
        else:
            await self._context.message.channel.send(content=i18n.t('ui.whitelist_view.success_no_reply', user_mention=self._context.author.mention, server_name=db_server.FriendlyName), delete_after=self._client.Message_Timeout)


class Accept_Whitelist_Button(Button):
    """Accepts the Whitelist Request"""

    def __init__(self, discord_message: discord.Message, view: Whitelist_view, client: discord.Client, amp_server: AMP_Handler.AMP.AMPInstance, style=discord.ButtonStyle.green):
        super().__init__(label=i18n.t('ui.whitelist_buttons.accept'), style=style, custom_id='Accept_Button')
        self._view = view
        self._discord_message = discord_message
        self._amp_server = amp_server
        self._client = client

    async def callback(self, interaction: discord.Interaction):
        if await utils.async_rolecheck(context=interaction, perm_node='whitelist_buttons'):
            self._view.logger.info(f'We Accepted a Whitelist Request by {self._view._whitelist_message.author.name}')
            await self._discord_message.edit(content=i18n.t('ui.whitelist_buttons.approved', approver=interaction.user.name, requester=self._view._whitelist_message.author.name), view=None)
            await self._view._whitelist_handler()
            self._amp_server.addWhitelist(self._client.Whitelist_wait_list[self._view._whitelist_message.id]['dbuser'])
            self._client.Whitelist_wait_list.pop(self._view._whitelist_message.id)
            self.disabled = True


class Deny_Whitelist_Button(Button):
    """Denys the Whitelist Request"""

    def __init__(self, discord_message: discord.Message, view: Whitelist_view, client: discord.Client, amp_server: AMP_Handler.AMP.AMPInstance, style=discord.ButtonStyle.red):
        super().__init__(label=i18n.t('ui.whitelist_buttons.deny'), style=style, custom_id='Deny_Button')
        self._view = view
        self._discord_message = discord_message
        self._amp_server = amp_server
        self._client = client

    async def callback(self, interaction: discord.Interaction):
        if await utils.async_rolecheck(context=interaction, perm_node='whitelist_buttons'):
            self._view.logger.info(f'We Denied a Whitelist Request by {self._view._whitelist_message.author.name}')
            await self._discord_message.edit(content=i18n.t('ui.whitelist_buttons.denied', approver=interaction.user.name, requester=self._view._whitelist_message.author.name), view=None)
            await self._view._whitelist_message.channel.send(content=i18n.t('ui.whitelist_buttons.denied_notice', approver=interaction.user.name, requester_mention=self._view._whitelist_message.author.mention))
            self._client.Whitelist_wait_list.pop(self._view._whitelist_message.id)
            self.disabled = True


class LinkConfirmView(View):
    """Generic confirmation View shown after a `/link` lookup, so the user can confirm the resolved Account is theirs.
    `apply` is called with the caller's `DB.DBUser` once they hit Confirm, and should set whichever fields on it are needed."""

    def __init__(self, invoker_id: int, apply: Callable[[DB.DBUser], None], confirm_message: str, timeout: float = 60):
        self.logger = logging.getLogger()
        self.DB = DB.getDBHandler().DB
        self._invoker_id = invoker_id
        self._apply = apply
        self._confirm_message = confirm_message
        self.message: discord.Message | None = None

        super().__init__(timeout=timeout)
        self.add_item(Confirm_Link_Button(view=self))
        self.add_item(Deny_Link_Button(view=self))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self._invoker_id:
            await interaction.response.send_message(i18n.t('ui.link_confirm.not_for_you'), ephemeral=True)
            return False
        return True

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        if self.message != None:
            try:
                await self.message.edit(content=i18n.t('ui.link_confirm.timed_out'), embed=None, view=self)
            except discord.HTTPException:
                pass


class Confirm_Link_Button(Button):
    """Confirms an Account Link"""

    def __init__(self, view: LinkConfirmView, style=discord.ButtonStyle.green):
        super().__init__(label=i18n.t('ui.link_confirm.confirm_label'), style=style, custom_id='Confirm_Link')
        self._view = view

    async def callback(self, interaction: discord.Interaction):
        db_user = self._view.DB.GetUser(interaction.user.id)
        if db_user == None:
            db_user = self._view.DB.AddUser(DiscordID=interaction.user.id, DiscordName=interaction.user.name)

        for child in self._view.children:
            child.disabled = True

        try:
            self._view._apply(db_user)
        except sqlite3.IntegrityError as e:
            if 'UNIQUE constraint failed' in e.args[0]:
                await interaction.response.edit_message(content=i18n.t('ui.link_confirm.already_linked'), embed=None, view=self._view)
                return
            raise

        self._view.logger.info(f'Linked {interaction.user.name} via /link confirmation')
        await interaction.response.edit_message(content=self._view._confirm_message, embed=None, view=self._view)


class Deny_Link_Button(Button):
    """Cancels an Account Link"""

    def __init__(self, view: LinkConfirmView, style=discord.ButtonStyle.red):
        super().__init__(label=i18n.t('ui.link_confirm.deny_label'), style=style, custom_id='Deny_Link')
        self._view = view

    async def callback(self, interaction: discord.Interaction):
        for child in self._view.children:
            child.disabled = True
        await interaction.response.edit_message(content=i18n.t('ui.link_confirm.cancelled'), embed=None, view=self._view)


class DB_Instance_ID_Swap(View):
    """DB Instance ID Swap View"""

    def __init__(self, discord_message: discord.Message, timeout: float, from_db_server: DB.DBServer, to_db_server: DB.DBServer):
        super().__init__(timeout=timeout)
        self._from_db_server = from_db_server
        self._to_db_server = to_db_server
        self.add_item(Approve_Button(view=self, discord_message=discord_message))
        self.add_item(Cancel_Button(view=self, discord_message=discord_message))


class Approve_Button(Button):
    def __init__(self, view: View, discord_message: discord.Message, style=discord.ButtonStyle.green):
        self._view = view
        self.message = discord_message
        super().__init__(label=i18n.t('ui.db_instance_swap.approve'), style=style, custom_id='Approve_Button')

    async def callback(self, interaction: discord.Interaction):
        to_db_server_ID = self._view._to_db_server.InstanceID
        to_db_server_Name = self._view._to_db_server.InstanceName
        self._view._to_db_server.delServer()
        self._view._from_db_server.InstanceID = to_db_server_ID
        await self.message.edit(content=i18n.t('ui.db_instance_swap.replaced', from_name=self._view._from_db_server.InstanceName, from_id=self._view._from_db_server.InstanceID, to_name=to_db_server_Name, to_id=to_db_server_ID), view=None)


class Cancel_Button(Button):
    def __init__(self, view: View, discord_message: discord.Message, style=discord.ButtonStyle.red):
        self._view = view
        self.message = discord_message
        super().__init__(label=i18n.t('common.button.cancel'), style=style, custom_id='Cancel_Button')

    async def callback(self, interaction: discord.Interaction):
        return await self.message.edit(content=i18n.t('ui.db_instance_swap.cancelled', from_name=self._view._from_db_server.InstanceName), view=None)
