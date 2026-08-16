# Copyright (C) 2021-2022 Katelynn Cadwallader
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations
import logging
import json
import pathlib
import sys
from typing import Union

import discord
from discord.ext import commands

from core import DB
from core import i18n


def _resolve_rolecheck_author(context: Union[commands.Context, discord.Interaction]) -> discord.Member:
    """Resolves the invoking `discord.Member` from a command `Context` or an `Interaction`.

    These are the only two types ever passed to `async_rolecheck()` in this codebase:
    `discord.ext.commands.Context` (via the `role_check()` `commands.check` predicate, and
    the on-message `Context` built in `amp_tasks_cog.py`) and `discord.Interaction` (from
    UI components/autocomplete in `utils_ui.py`/`utils_discord.py`). Anything else is a programming
    error at the call site, so it raises rather than silently falling through.
    """
    if isinstance(context, commands.Context):
        return context.author
    if isinstance(context, discord.Interaction):
        return context.user
    raise TypeError(f'async_rolecheck() received an unsupported context type: {type(context)!r}')


async def _rolecheck_permission(context: Union[commands.Context, discord.Interaction], author: discord.Member, perm_node: str | None = None) -> tuple[bool, Union[str, None]]:
    """Pure permission decision: never touches Discord I/O.

    Returns `(allowed, denial_key)` where `denial_key` is the i18n key of the message
    `async_rolecheck()` should show the user on denial, or `None` when this particular
    denial path should stay silent (matches the pre-refactor behaviour, where a Custom
    Permissions denial was only logged, never messaged to the user).
    """
    DBHandler = DB.getDBHandler()
    DBConfig = DBHandler.DBConfig
    _mod_role = DBConfig.GetSetting('Moderator_role_id')
    logger = logging.getLogger()
    logger.dev(f'Permission Context command node {perm_node if perm_node != None else str(context.command).replace(" ", ".")}')

    # This fast tracks role checks for Admins, which also allows the bot to still work without a Staff Role set in the DB
    admin = author.guild_permissions.administrator
    if admin == True:
        logger.command(f'*Admin* Permission Check Okay on {author}')
        return True, None

    # This handles Custom Permissions for people with the flag set.
    if DBConfig.GetSetting('Permissions') == 1:  # 0 is Default, 1 is Custom
        if perm_node == None:
            perm_node = str(context.command).replace(" ", ".")

        bPerms = get_botPerms()
        if bPerms.perm_node_check(perm_node, author) is not True:
            logger.command(f'*Custom* Permission Check Failed on {author} missing {perm_node}')
            return False, None
        else:
            logger.command(f'*Custom* Permission Check Okay on {author}')
            return True, None

    # This is the final check before we attempt to use the "DEFAULT" permissions setup.
    if _mod_role == None:
        logger.error('DBConfig Moderator role has not been set yet!')
        return False, 'common.no_moderator_role'

    staff_role, author_top_role = 0, 0
    guild_roles = context.guild.roles
    # Guild Roles is a heirachy tree;
    # So here I am comparing if the author/user's top role is greater than or equal to the `_mod_role` in terms of index values from the list.
    for i in range(0, len(guild_roles)):
        if guild_roles[i].id == author.top_role.id:
            author_top_role = i

        if guild_roles[i].id == _mod_role:
            staff_role = i

    if author_top_role >= staff_role:
        logger.command(f'*Default* Permission Check Okay on {author}')
        return True, None

    logger.command(f'*Default* Permission Check Failed on {author}')
    return False, 'common.no_permission'


async def _send_rolecheck_denial(context: Union[commands.Context, discord.Interaction], i18n_key: str) -> None:
    """Reports a permission denial to the user.

    `commands.Context` has `.send()`; `discord.Interaction` does not - it needs
    `.response.send_message()` (or `.followup.send()` if a response was already sent,
    e.g. by a deferred interaction) instead. Dispatches on the actual type so both of
    async_rolecheck's live caller shapes get a real reply instead of an AttributeError.
    """
    message = i18n.t(i18n_key)
    if isinstance(context, discord.Interaction):
        # An autocomplete interaction only accepts a choice-list response (callback type 8);
        # answering it with a message (type 4) is rejected by Discord with an HTTP 400 -- once
        # per keystroke. There's nowhere to show text here anyway, so stay silent and let the
        # caller return a narrowed/empty choice list instead.
        if context.type is discord.InteractionType.autocomplete:
            return
        if context.response.is_done():
            await context.followup.send(message, ephemeral=True)
        else:
            await context.response.send_message(message, ephemeral=True)
    elif isinstance(context, commands.Context):
        await context.send(message, ephemeral=True)
    else:
        raise TypeError(f'async_rolecheck() received an unsupported context type: {type(context)!r}')


async def async_rolecheck(context: Union[commands.Context, discord.Interaction], perm_node: str | None = None) -> bool:
    """Primary authorization gate for the bot - used as a `commands.check` predicate
    (via `role_check()`) and called directly wherever a permission needs checking outside
    of a command invocation (autocomplete, UI components).

    Resolves the invoking Member, runs the permission decision (Admin fast-path -> Custom
    `bot_perms.json` backend if enabled -> Default moderator-role-hierarchy comparison),
    and reports denial to the user when the decision calls for it.
    """
    author = _resolve_rolecheck_author(context)
    allowed, denial_key = await _rolecheck_permission(context, author, perm_node)
    if not allowed and denial_key is not None:
        await _send_rolecheck_denial(context, denial_key)
    return allowed


def role_check():
    """Use this before any Commands that require a Staff/Mod level permission Role, this will also check for Administrator"""
    # return commands.check(async_rolecheck(permission_node=perm))
    return commands.check(async_rolecheck)


def guild_check(guild_id: int | None = None):
    """Use this before any commands to limit it to a certain guild usage."""
    async def predicate(context: commands.Context):
        if context.guild.id == guild_id:
            return True
        else:
            await context.send(i18n.t('common.no_permission'), ephemeral=True)
            return False
    return commands.check(predicate)


# Used to maintain a "Global" botPerms() object.
bPerms = None


def get_botPerms():
    """Returns the Global botPerms() object; otherwise creates it."""
    global bPerms
    if bPerms == None:
        bPerms = botPerms()
    return bPerms


class botPerms:
    def __init__(self):
        self.logger = logging.getLogger()
        self.DBHandler = DB.getDBHandler()
        self.DB = self.DBHandler.DB

        self._last_modified = 0
        self.permissions = None
        self.permission_roles = []

        self.validate_and_load()
        self.get_roles()
        self.logger.info('**SUCCESS** Loading Bot Permissions')

    def validate_and_load(self):
        """Validates the contents of bot_perms.json."""
        self.json_file = pathlib.Path.cwd().joinpath('bot_perms.json')
        if self.json_file.stat().st_mtime > self._last_modified:
            try:
                self.permissions = json.load(open(self.json_file, 'r'))
                self._last_modified = self.json_file.stat().st_mtime

                # Soft validation of the file to help with errors.
                # Verifies each role has a numeric discord_role_id or is equal to None and the name is not empty.
                for role in self.permissions['Roles']:
                    if len(role['name']) == 0:
                        self.logger.critical('You are missing a role name, please do not leave role names empty..')
                        sys.exit(0)

                    if role['discord_role_id'] == 'None':
                        continue

                    elif type(role['discord_role_id']) != str:
                        self.logger.critical(f'Your Discord Role ID for {role["name"]} does not appear to be string. Please check your bot_perms.json.')
                        sys.exit(0)

                    elif not role['discord_role_id'].isnumeric():
                        self.logger.critical(f'Your Discord Role ID for {role["name"]} does not appear to be all numbers. Please check your bot_perms.json.')
                        sys.exit(0)

            except json.JSONDecodeError:
                self.permissions = None
                self.logger.critical('Unable to load your permissions file. Please check your formatting.')

    def perm_node_check(self, command_perm_node: str, author: discord.Member) -> bool:
        """Checks a Users for a DB Role then checks for that Role inside of bot_perms.py, then checks that Role for the proper permission node."""
        # Lets get our DB user and check if they exist.
        DB_user = self.DB.GetUser(str(author.id))
        if DB_user == None:
            return False

        # Lets also check for their DB Role
        user_role = DB_user.Role
        if user_role == None:
            return False

        # Need to turn author roles into a list of ints.
        user_discord_role_ids = []
        for user_roles in author.roles:
            user_discord_role_ids.append(str(user_roles.id))

        # This is to check for Super perm nodes such as `server.*`
        command_super_node = command_perm_node.split(".")[0] + '.*'

        if self.permissions == None:
            self.logger.error('**ATTENTION** Please verify your bot_perms file, it failed to load.')
            return False

        self.validate_and_load()
        self.logger.info('Validated and Loaded Permissions File.')
        roles = self.permissions['Roles']
        for role in roles:
            if user_role.lower() in role['name'].lower() or role['discord_role_id'] in user_discord_role_ids:
                if command_super_node in role['permissions']:
                    command_perm_node_false_check = '-' + command_perm_node
                    if command_perm_node_false_check in role['permissions']:
                        self.logger.dev('This perm node has been denied even though you have global permissions.', command_perm_node_false_check, command_perm_node)
                        return False

                    self.logger.dev('Found super permission node in Roles Permissions list.', command_super_node)
                    return True

                if command_perm_node in role['permissions']:
                    self.logger.dev('Found command perm node in Roles Permissions list.', command_perm_node)
                    return True

        return False

    def get_roles(self) -> list[str]:
        """Pre build my Permissions Role Name List"""
        self.permission_roles = []
        for role in self.permissions['Roles']:
            self.permission_roles.append(role['name'])
        return self.permission_roles

    async def get_role_prefix(self, user_id: str | None = None, context: commands.Context = None) -> Union[str, None]:
        """Use to get a Users Role Prefix for displaying."""

        # This grabs all a Users discord roles and makes a list of their ids
        discord_roles = []
        if context != None:
            for role in context.author.roles:
                discord_roles.append(str(role.id))

            # This works because you can only have one bot_perms role.
            for role in self.permissions['Roles']:
                if role['discord_role_id'] in discord_roles:
                    return role['prefix']

        db_user = self.DB.GetUser(user_id)
        if db_user != None and db_user.Role != None:
            rolename = db_user.Role
            if rolename in self.permission_roles:
                for role in self.permissions['Roles']:
                    if role['name'] == rolename:
                        return role['prefix']
                    else:
                        continue
        return None
