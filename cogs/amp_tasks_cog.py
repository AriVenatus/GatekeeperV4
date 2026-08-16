# Copyright (C) 2021-2022 Katelynn Cadwallader
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING

import discord
from discord.ext import commands, tasks

from core import AMP_Handler
from core import DB
from core import utils
from core import utils_permissions
from core.AMP import AMPInstance

if TYPE_CHECKING:
    from ..AMP import AMPInstance
    from ..modules.Minecraft.amp_minecraft import AMPMinecraft

# This is used to force cog order to prevent missing methods.
Dependencies = None


class AMP_Tasks(commands.Cog):
    def __init__(self, client: discord.Client):
        self._client: discord.Client = client
        self.name = os.path.basename(__file__)
        self.logger = logging.getLogger()

        self.AMPHandler = AMP_Handler.getAMPHandler()
        self.AMPInstances: dict[str, AMPInstance] = self.AMPHandler.AMP_Instances

        self.DBHandler = DB.getDBHandler()
        self.DB = self.DBHandler.DB  # Main Database object
        self.DBConfig = self.DBHandler.DBConfig

        self.bPerms = utils_permissions.get_botPerms()

        self.uBot = utils.botUtils(client)
        self.logger.info(f'**SUCCESS** Initializing {self.name.title().replace("Amp", "AMP")}')

        self.amp_server_console_messages_send.start()
        self.logger.dev('AMP_Cog Console Message Handler Running: ' + str(self.amp_server_console_messages_send.is_running()))

        self.amp_server_console_chat_messages_send.start()
        self.logger.dev('AMP_Cog Console Chat Message Handler Running: ' + str(self.amp_server_console_chat_messages_send.is_running()))

        self.amp_server_console_event_messages_send.start()
        self.logger.dev('AMP_Cog Console Event Message Handler Running: ' + str(self.amp_server_console_event_messages_send.is_running()))

    @commands.Cog.listener('on_message')
    async def on_message(self, message: discord.Message):
        context = await self._client.get_context(message)
        # Force the Tasks to ignore any "prefix" commands.
        if message.author == self._client.user:
            return

        for amp_server in list(self.AMPInstances):
            self.AMPServer = self.AMPInstances[amp_server]
            if not self.AMPServer.Running:
                continue
            self.AMPServer._ADScheck()

            # Check and see if our Discord Console Channel matches the current message.id
            if self.AMPServer.Discord_Console_Channel == message.channel.id:

                # Makes sure we are not responding to a webhook message (ourselves/bots/etc)
                if message.webhook_id == None:
                    # This checks user permissions. Just in case.
                    if await utils_permissions.async_rolecheck(context=context, perm_node='server.console.interact'):
                        # Since Integrations hijacks any commands with a `/` in front of it. We are now going to be using a `.` in front of any command to bypass.
                        if message.content.startswith('.'):
                            # Remove the prefix char.
                            message.content = message.content[1:]

                        self.AMPServer.ConsoleMessage(message.content)
                        return

            # Check and see if our Discord Chat channel matches the message.id
            if self.AMPServer.Discord_Chat_Channel == message.channel.id:
                if message.author == self._client.user:
                    self.logger.dev('AMP_Tasks_Cog Found my own Message, oops')
                    return
                # If its NOT a webhook (eg a bot/outside source uses webhooks) send the message as normal. This is usually a USER sending a message..
                if message.webhook_id == None:
                    # This fetch's a users prefix from the bot_perms.json file.
                    author_prefix = await self.bPerms.get_role_prefix(str(message.author.id))

                    # Strip newlines so a Discord message can't smuggle a second, separate console command.
                    chat_message = message.content.replace('\r\n', ' ').replace('\r', ' ').replace('\n', ' ')

                    # This calls the generic AMP Function; each server will handle this differently
                    self.AMPServer.Chat_Message(chat_message, author=message.author.name, author_prefix=author_prefix)

        return message

    async def _get_or_create_webhook(
        self,
        channel: discord.TextChannel,
        friendly_name: str,
        webhook_name: str,
        expected_channel_id: int,
        log_prefix: str,
    ) -> discord.Webhook:
        """Find an existing webhook named `webhook_name` on `channel`, move it to
        `channel` if it's currently attached to a different channel, or create a
        new one if none exists.

        `webhook_name` is a stored identity key matched by exact string equality
        across restarts (see CLAUDE.md's i18n section) - callers must pass the
        exact literal name, never an i18n-translated one, or restarts will
        orphan/duplicate webhooks.
        """
        webhook_list = await channel.webhooks()
        self.logger.debug(f'{log_prefix} webhooks {webhook_list}')
        found_webhook = None
        for webhook in webhook_list:
            if webhook.name == webhook_name:
                self.logger.debug(f'{log_prefix} found an old webhook, reusing it {friendly_name}')
                if webhook.channel_id == expected_channel_id:
                    found_webhook = webhook
                else:
                    await webhook.edit(channel=channel)
                    self.logger.dev(f'{log_prefix} **Editing Webhook for {friendly_name} // ID: {webhook.id} // Channel: {webhook.channel_id}')
                    found_webhook = webhook
                break

        if found_webhook is None:
            self.logger.dev(f'{log_prefix} creating a new webhook for {friendly_name}')
            found_webhook = await channel.create_webhook(name=webhook_name)

        return found_webhook

    @tasks.loop(seconds=1)
    async def amp_server_console_messages_send(self):
        """This handles AMP Console messages and sends them to discord."""
        if self._client.is_ready():
            Sent_Data = True
            while (Sent_Data):
                Sent_Data = False
                for amp_server in list(self.AMPInstances):
                    AMPServer = self.AMPInstances[amp_server]
                    AMP_Server_Console = AMPServer.Console

                    if AMPServer.Discord_Console_Channel == None:
                        continue

                    channel = self._client.get_channel(AMPServer.Discord_Console_Channel)
                    if channel == None:
                        continue

                    if not len(AMP_Server_Console.console_messages):
                        continue

                    Sent_Data = True
                    AMP_Server_Console.console_message_lock.acquire()
                    message = AMP_Server_Console.console_messages.pop(0)
                    AMP_Server_Console.console_message_lock.release()

                    # This setup is for getting/used old webhooks and allowing custom avatar names per message.
                    console_webhook = await self._get_or_create_webhook(
                        channel,
                        AMPServer.FriendlyName,
                        f'{AMPServer.FriendlyName} Console',
                        AMPServer.Discord_Console_Channel,
                        '*AMP Console Message*',
                    )

                    if AMPServer.DisplayName is not None:  # Lets check for a Display name and use that instead.
                        self.logger.dev('*AMP Console Message* sending a message with displayname')
                        await console_webhook.send(message, username=AMPServer.DisplayName, avatar_url=AMPServer.Avatar_url)
                    else:
                        self.logger.dev('*AMP Console Message* sending a message with friendlyname')
                        await console_webhook.send(message, username=AMPServer.FriendlyName, avatar_url=AMPServer.Avatar_url)

    @tasks.loop(seconds=1)
    async def amp_server_console_event_messages_send(self):
        """This handles AMP Console Event messages and sends them to discord."""
        if self._client.is_ready():
            Sent_Data = True
            while (Sent_Data):
                Sent_Data = False
                for amp_server in list(self.AMPInstances):
                    AMPServer_Event = self.AMPInstances[amp_server]
                    AMP_Server_Console_Event = AMPServer_Event.Console

                    if AMPServer_Event.Discord_Event_Channel == None:
                        continue

                    channel = self._client.get_channel(AMPServer_Event.Discord_Event_Channel)
                    if channel == None:
                        continue

                    if not len(AMP_Server_Console_Event.console_event_messages):
                        continue

                    Sent_Data = True
                    AMP_Server_Console_Event.console_event_message_lock.acquire()
                    message = AMP_Server_Console_Event.console_event_messages.pop(0)
                    AMP_Server_Console_Event.console_event_message_lock.release()

                    # This setup is for getting/used old webhooks and allowing custom avatar names per message.
                    console_webhook = await self._get_or_create_webhook(
                        channel,
                        AMPServer_Event.FriendlyName,
                        f'{AMPServer_Event.FriendlyName} Events',
                        AMPServer_Event.Discord_Event_Channel,
                        '*AMP Event Message*',
                    )

                    if AMPServer_Event.DisplayName is not None:  # Lets check for a Display name and use that instead.
                        self.logger.dev('*AMP Event Message* sending a message with displayname')
                        await console_webhook.send(message, username=AMPServer_Event.DisplayName, avatar_url=AMPServer_Event.Avatar_url)
                    else:
                        self.logger.dev('*AMP Event Message* sending a message with friendlyname')
                        await console_webhook.send(message, username=AMPServer_Event.FriendlyName, avatar_url=AMPServer_Event.Avatar_url)

    @tasks.loop(seconds=1)
    async def amp_server_console_chat_messages_send(self):
        """This handles IN game chat messages and sends them to discord."""
        if self._client.is_ready():
            AMPChatChannels: dict[str | int, list[AMPInstance | AMPMinecraft]] = {}
            for amp_server in list(self.AMPInstances):
                AMPServer = self.AMPInstances[amp_server]

                if AMPServer.Discord_Chat_Channel == None:
                    continue

                if AMPServer.Discord_Chat_Channel not in AMPChatChannels:
                    AMPChatChannels[AMPServer.Discord_Chat_Channel] = []
                AMPChatChannels[AMPServer.Discord_Chat_Channel].append(AMPServer)

            Sent_Data = True
            while (Sent_Data):
                Sent_Data = False
                for amp_server in list(self.AMPInstances):
                    AMPServer_Chat: AMPMinecraft | AMPInstance = self.AMPInstances[amp_server]
                    AMP_Server_Console_Chat = AMPServer_Chat.Console

                    if AMPServer_Chat.Discord_Chat_Channel == None:
                        continue

                    channel = self._client.get_channel(AMPServer_Chat.Discord_Chat_Channel)
                    if channel == None:
                        continue

                    if not len(AMP_Server_Console_Chat.console_chat_messages):
                        continue

                    Sent_Data = True
                    AMP_Server_Console_Chat.console_chat_message_lock.acquire()
                    message = AMP_Server_Console_Chat.console_chat_messages.pop(0)
                    AMP_Server_Console_Chat.console_chat_message_lock.release()

                    # This setup is for getting/used old webhooks and allowing custom avatar names per message.
                    chat_webhook = await self._get_or_create_webhook(
                        channel,
                        AMPServer_Chat.FriendlyName,
                        f'{AMPServer_Chat.FriendlyName} Chat',
                        AMPServer_Chat.Discord_Chat_Channel,
                        '*AMP Chat Message*',
                    )

                    # This is the person who wrote the In-Game Message
                    author = message['Source']
                    author_prefix = None

                    message_contents = message['Contents'].replace('\n', ' ')
                    server_prefix = AMPServer_Chat.Discord_Chat_Prefix

                    db_author: None | DB.DBUser = self.DB.GetUser(author)
                    name, avatar = author, AMPServer_Chat.Avatar_url
                    if db_author != None:
                        author_prefix = await self.bPerms.get_role_prefix(db_author.DiscordID)

                        if AMPServer_Chat.get_IGN_Avatar(db_user=db_author):
                            self.logger.dev('Using AMP Server Information')
                            name, avatar = AMPServer_Chat.get_IGN_Avatar(db_user=db_author)

                        else:
                            discord_user = self._client.get_user(int(db_author.DiscordID))
                            if discord_user != None:
                                self.logger.dev('Using Discord Server Information')
                                name, avatar = discord_user.name, discord_user.avatar
                            # else: keep the (author, Avatar_url) fallback set above

                    elif AMPServer_Chat.get_IGN_Avatar(user=author):
                        self.logger.dev('Using Message Information')
                        name, avatar = AMPServer_Chat.get_IGN_Avatar(user=author)
                    # else: keep the (author, Avatar_url) fallback set above

                    if author_prefix != None:
                        self.logger.dev('Adding Author Prefix to Name')
                        name = f'[{author_prefix}] ' + name

                    if server_prefix != None:
                        self.logger.dev('Adding Server Prefix to Name')
                        name = f'[{server_prefix}] - ' + name

                    await chat_webhook.send(content=message_contents, username=name, avatar_url=avatar)

                    # This is the Chat Relay to separate AMP Servers.
                    if chat_webhook.channel is not None and chat_webhook.channel.id in AMPChatChannels:
                        self.logger.dev('Found another Server Chat Channel Listening to this Discord channel.')
                        for Server in AMPChatChannels[chat_webhook.channel.id]:

                            # Dont re-send the Console Chat message we sent to Discord to the same server.
                            if AMPServer_Chat == Server:
                                continue

                            self.logger.dev(f'Sending the Mesage from {AMPServer_Chat.FriendlyName} to Other Server: {Server.FriendlyName}')
                            Server.Chat_Message(message=message_contents, author_prefix=author_prefix, author=author, server_prefix=AMPServer_Chat.Discord_Chat_Prefix)


async def setup(client: commands.Bot):
    await client.add_cog(AMP_Tasks(client))
