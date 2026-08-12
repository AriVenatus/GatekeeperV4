# Graph Report - GatekeeperV3.1  (2026-08-09)

## Corpus Check
- 71 files · ~327,626 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1266 nodes · 2576 edges · 83 communities (62 shown, 21 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 100 edges (avg confidence: 0.59)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `1a4424e9`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- discordBot.py
- role_check
- Banner
- DBHandler
- WhitelistSync
- DB.py
- Whitelist
- .Login
- Cog_Template
- DB_Update
- AMPMinecraft
- AMP.py
- AMPInstance
- Banner_Generator
- botUtils
- botEmbeds
- .emptyTrash
- DB_User
- ._fetchall
- .trashDirectory
- .Get_BannerGroup
- Regex
- DBServer
- AMPTemplate
- Database
- .__init__
- Permissions Documentation (PERMISSIONS.md)
- DB_Server
- .__init__
- AMP_Tasks
- Whitelist Documentation (WHITELIST.md)
- discordBot
- amp_generic.py
- Python 3.13 Bootstrap Compatibility Fixes
- Edited_DB_Banner
- .RemoveServerWhitelistRole
- Gatekeeper README
- DBConfig
- cog_minecraft.py
- botPerms
- .getStatus
- Commands List (COMMANDS.md)
- ._execute
- .check_GatekeeperRole_Permissions
- AMPConsole
- Handler
- .role_parse
- async_rolecheck
- Why Use This Fork (Fork Lineage & Deltas)
- Regex Documentation (REGEX.md)
- AMPProjectzomboid
- AMPSevendays
- AMPTerraria
- Banner Documentation (BANNER.md)
- AMPFactorio
- I18nHandler
- amp_csgo.py
- cog_csgo.py
- cog_factorio.py
- cog_starbound.py
- Context
- cog_valheim.py
- Setup
- .channel_parse
- amp_permissions.py
- CLAUDE.md Project Guidance
- generic.py
- cog_projectzomboid.py
- cog_terraria.py
- .CurrentSessionHasPermission
- .ConsoleMessage_withUpdate
- .user_role
- .AddServerWhitelistRole
- Cleanup-Roadmap
- DBUser
- start.py (Setup / startup sequence)
- Bug Report Issue Template
- GatekeeperV3.1
- cog_sevendays.py
- request_shutdown

## God Nodes (most connected - your core abstractions)
1. `AMPInstance` - 107 edges
2. `role_check()` - 99 edges
3. `Database` - 54 edges
4. `Edited_DB_Banner` - 40 edges
5. `DB_Update` - 37 edges
6. `AMP_Server` - 36 edges
7. `Banner` - 34 edges
8. `Banner_Editor_View` - 28 edges
9. `AMPHandler` - 27 edges
10. `t()` - 26 edges

## Surprising Connections (you probably didn't know these)
- `AMPInstance` --uses--> `AMPHandler`  [INFERRED]
  AMP.py → AMP_Handler.py
- `AMPConsole` --uses--> `AMPInstance`  [INFERRED]
  AMP_Console.py → AMP.py
- `ConsoleEntry` --uses--> `AMPInstance`  [INFERRED]
  AMP_Console.py → AMP.py
- `AMP_Tasks` --uses--> `AMPInstance`  [INFERRED]
  cogs/AMP_tasks_cog.py → AMP.py
- `Cancel_Banner_Button` --uses--> `AMPInstance`  [INFERRED]
  utils_dev/banner_editor/ui/button.py → AMP.py

## Import Cycles
- 3-file cycle: `utils_dev/banner_editor/ui/button.py -> utils_dev/banner_editor/ui/modal.py -> utils_dev/banner_editor/ui/view.py -> utils_dev/banner_editor/ui/button.py`
- 4-file cycle: `utils_dev/banner_editor/ui/button.py -> utils_dev/banner_editor/ui/modal.py -> utils_dev/banner_editor/ui/textinput.py -> utils_dev/banner_editor/ui/view.py -> utils_dev/banner_editor/ui/button.py`

## Hyperedges (group relationships)
- **Discord Role <-> Whitelist Sync Feature: Proposal to Implementation** — discord_role_synced_whitelist_role_sync, discord_role_synced_whitelist_identity_db, whitelist_discord_role_sync, whitelist_player_identity_database, changelog_v4_8_0 [INFERRED 0.90]
- **Python 3.13 / Hetzner Deployment Compatibility Fix Batch** — claude_python313_compatibility_fixes, requirements_dependencies, claude_logger, claude_amp_instance, claude_amp_permissions [EXTRACTED 1.00]
- **Banner Display Feature Documentation Set** — banner_banner_guide, banner_banner_group, commands_bannergroup_commands, commands_bot_banner_settings_commands, commands_amp_server_banner_commands [EXTRACTED 1.00]

## Communities (83 total, 21 thin omitted)

### Community 0 - "discordBot.py"
Cohesion: 0.09
Nodes (45): autocomplete_loadedcogs(), bot_cog(), bot_cog_loader(), bot_cog_reload(), bot_cog_unloader(), bot_donator(), bot_language(), bot_moderator() (+37 more)

### Community 1 - "role_check"
Cohesion: 0.14
Nodes (16): AMP_Server, autocomplete, Choice, choices, Client, command, Context, group (+8 more)

### Community 2 - "Banner"
Cohesion: 0.08
Nodes (26): Banner, autocomplete, Bot, Choice, choices, command, Context, datetime (+18 more)

### Community 3 - "DBHandler"
Cohesion: 0.40
Nodes (3): DBHandler, getDBHandler(), This sets the DB Server Console_Flag, Console_Filtered and…

### Community 4 - "WhitelistSync"
Cohesion: 0.08
Nodes (27): before_loop, autocomplete, Bot, Choice, choices, command, Context, DBUser (+19 more)

### Community 5 - "DB.py"
Cohesion: 0.25
Nodes (9): setup(), datetime, get_language(), getI18nHandler(), # NOTE: `Command._params` is a private/undocumented discord.py attribute…, retranslate_command_tree(), set_language(), t_plural() (+1 more)

### Community 6 - "Whitelist"
Cohesion: 0.09
Nodes (22): autocomplete, Bot, Choice, choices, command, Context, describe, GuildChannel (+14 more)

### Community 7 - ".Login"
Cohesion: 0.09
Nodes (13): This is the main API Call function, This gets all Instances on AMP., Basic Console Message, Restarts AMP Instance, Returns a List of connected users., This is used to change an Instance's Friendly Name and or Description. Retains…, Test AMP API calls with this function, Ends specified User Session (+5 more)

### Community 8 - "Cog_Template"
Cohesion: 0.08
Nodes (24): guilds, Reaction, Cog_Template, autocomplete, Client, command, Context, hybrid_command (+16 more)

### Community 9 - "DB_Update"
Cohesion: 0.11
Nodes (3): DB_Update, SQLITE does not support dropping UNIQUE constraint, SQLITE does not support adding UNIQUE constraint

### Community 10 - "AMPMinecraft"
Cohesion: 0.09
Nodes (15): AMPMinecraft, AMPMinecraftConsole, DBUser, Gets a Users Player Head via UUID, Bans a User from the Server, Sends a customized message via tellraw through the console., Formats the message for Discord \n, Handles returning customized discord message data for Minecraft Servers only. (+7 more)

### Community 11 - "AMP.py"
Cohesion: 0.19
Nodes (4): AMPStarbound, AMPStarboundConsole, AMPValheim, AMPValheimConsole

### Community 12 - "AMPInstance"
Cohesion: 0.08
Nodes (13): AMPInstance, DBUser, Base Function for AMP.addWhitelist, Base Function for AMP.getWhitelist, Base Function for AMP.removeWhitelist, Base Function for AMP.name_Conversion, Base Function for AMP.name_History, Base Function for Discord Chat Messages to AMP ADS (+5 more)

### Community 13 - "Banner_Generator"
Cohesion: 0.14
Nodes (10): ImageFont, Banner_Generator, Image, Custom Banner Generator for Gatekeeper., Blurs the Background Image with GaussianBlur, Custom Word Wrap. \n Returns a `list` when `truncate` is `False`, Adjusted the RGB values for Player Limit Display., Rounds the corners of the Background Image. (+2 more)

### Community 14 - "botUtils"
Cohesion: 0.08
Nodes (13): botUtils, Gatekeeper Utility Class, Formats the message for Discord \n `Bold = \\x01, \\x02` \n `Italic = \\x03,…, This checks the DB Server objects Avatar_url and returns the proper object…, Converts an IGN to a UUID/Name Table \n `returns 'uuid'` else returns `None`,…, Resolves a Minecraft in-game name into profile info via the official Mojang…, Converts a Steam Name to a Steam ID returns `STEAM_0:0:2806383`, Returns `True` if a Steam Web API Key has been set in tokens.py (+5 more)

### Community 15 - "botEmbeds"
Cohesion: 0.13
Nodes (15): botEmbeds, Bot, Context, DBServer, DBUser, Embed, Guild, User (+7 more)

### Community 17 - "DB_User"
Cohesion: 0.20
Nodes (11): DB_User, Client, command, Context, describe, group, hybrid_group, listener (+3 more)

### Community 18 - "._fetchall"
Cohesion: 0.10
Nodes (9): Gets all Regex Patterns related to Server \n Returns `dict['ID': {'Name':…, Gets all Discord Role IDs gating Whitelist access for this Server., Gets all Servers current in the DB, Returns all ServerIDs that the provided Discord Role ID gates Whitelist access…, Gets all Regex Patterns from the RegexPatterns Table. \n Returns…, Gets all Whitelist Replies currently in the DB, Gets all BannerGroups Names/IDs\n returns `Banners[entry["ID"]] = entry["name"]`, Removes a Banner Group. (+1 more)

### Community 20 - ".Get_BannerGroup"
Cohesion: 0.11
Nodes (9): Selects a Banner Group Table matching the `name` provided., Update a Banner Group, Gets a Specific Banner Groups full information\n return…, Add a Server to an existing Banner Group., Removes a Server from an existing Banner Group., Add a Channel to a BannerGroups listing., Returns a list of existing BannerGroups Discord Channel IDs., Adds a Discord Message ID to a BannerGroup (+1 more)

### Community 21 - "Regex"
Cohesion: 0.17
Nodes (12): autocomplete, Choice, choices, Client, command, Context, describe, hybrid_group (+4 more)

### Community 22 - "DBServer"
Cohesion: 0.11
Nodes (9): DBServer, DBServer, DB Server Attributes: `InstanceID: str` \n `InstanceName: str` \n…, Adds the provided RegexPattern ID/Name to the ServerRegexPatterns Table., Removes the provided RegexPattern ID/Name from the ServerRegexPatterns Table., Removes a entry RegexPatterns Table using either its `Name` or `ID`, Returns RegexPatterns Table \n Returns `row['ID'] = {'Name': row['Name'],…, Update a Regex Pattern in the RegexPatterns Table using either its `Name` or… (+1 more)

### Community 23 - "AMPTemplate"
Cohesion: 0.12
Nodes (8): AMPTemplate, AMPTemplateConsole, Sets the Permissions for Template Modules, Sends a message in a way to mimic that of in-game Chat Messages., Base Function for Broadcast Messages to AMP ADS, Base Function for AMP.addWhitelist, Base Function for AMP.getWhitelist, Base Function for AMP.removeWhitelist

### Community 24 - "Database"
Cohesion: 0.14
Nodes (7): Database, Adds a entry to table RegexPatterns, else Updates a matching pattern., Adds a Whitelist Reply to the DB, Deletes a Whitelist Reply from the DB, Creates a Banner Group Table with the provided `name`, Remove a Channel from a BannerGroups listing, this also removes any related…, Removes a Discord Message ID from a BannerGroup

### Community 25 - ".__init__"
Cohesion: 0.06
Nodes (33): Accept_Whitelist_Button, Approve_Button, Cancel_Button, Confirm_Link_Button, DB_Instance_ID_Swap, Deny_Link_Button, Deny_Whitelist_Button, KillButton (+25 more)

### Community 26 - "Permissions Documentation (PERMISSIONS.md)"
Cohesion: 0.14
Nodes (17): Update 4.5 (loader.py Dependencies, refactors), Discord Bot Layer, discordBot.py (Gatekeeper bot class), Escape External Text Before Embed Markdown Interpolation, Internationalization (i18n) System, loader.py (extension/cog auto-loader), Bot Commands, Link Commands (+9 more)

### Community 27 - "DB_Server"
Cohesion: 0.16
Nodes (11): DB_Server, autocomplete, Choice, Client, command, Context, describe, hybrid_group (+3 more)

### Community 28 - ".__init__"
Cohesion: 0.18
Nodes (6): Creates a AMP User role, Sets the AMP Users Role Membership, Sets the AMP Role permission Node eg `Core.RoleManagement.DeleteRoles`, Creates the `Gatekeeper` role, Adds us to the Membership of that Role and sets…, Sets the Permissions Nodes for AMP Gatekeeper Role, This is used to set/update the DB attributes for the AMP server

### Community 29 - "AMP_Tasks"
Cohesion: 0.15
Nodes (10): AMP_Tasks, Bot, Client, listener, loop, Message, This handles AMP Console messages and sends them to discord., This handles AMP Console Event messages and sends them to discord. (+2 more)

### Community 30 - "Whitelist Documentation (WHITELIST.md)"
Cohesion: 0.17
Nodes (15): AMP Server Whitelist Commands, Bot Whitelist Commands, Whitelist_Request Commands, Proposed: Global Ban / Moderation (unimplemented), Proposed: Player Identity Database (Account Linking), Discord Role Whitelist Sync Feature Proposal, Proposed: Discord Role to Whitelist Sync, New Feature: Self-Service Account Linking (v3.1) (+7 more)

### Community 31 - "discordBot"
Cohesion: 0.15
Nodes (9): file, discordBot, Client, Embed, Message, Deletes the message.\n Your own messages could be deleted without any proper…, Edits the message.\n The content must be able to be transformed into a string…, Sends a message to the destination with the content given.\n The content must… (+1 more)

### Community 33 - "Python 3.13 Bootstrap Compatibility Fixes"
Cohesion: 0.21
Nodes (14): amp_permissions.py (AMP permission profiles), Core.UserManagement.ViewUserInfo Self-Check Crash Fix, AMP HTTP Session Reuse (requests.Session()), logger.py (logging configuration), AMP Loopback Reachability False Lead, AMP Permission Node Drift Reconciliation, Production Deployment Log (Hetzner, fullsendhub.de), Python 3.13 Bootstrap Compatibility Fixes (+6 more)

### Community 34 - "Edited_DB_Banner"
Cohesion: 0.05
Nodes (58): AMP_init(), amp_server_instance_check(), AMPHandler, getAMPHandler(), Intializes the connection to AMP and creates AMP_Instance objects., Creates a list of Instance Names/DisplayName or Friendly Name., Secondary secrets loader: builds a tokens-like namespace from environment…, Validates the tokens.py settings and 2FA. (+50 more)

### Community 37 - "Gatekeeper README"
Cohesion: 0.17
Nodes (13): Changelog, Update 4.4.0 (AMP Instance Permission Setup Refactor, Gatekeeper role), Update 4.8.0 (Whitelist Sync + Account Linking), AMP_Handler.py (AMPHandler singleton), AMP.py (AMPInstance base class), AMP Integration Layer, AMP Bot Role/Permission Bootstrap Ordering Bug, -whitelist-only Flag Needs Live Verification (+5 more)

### Community 39 - "cog_minecraft.py"
Cohesion: 0.20
Nodes (8): Minecraft, Bot, listener, Member, User, Called when a User updates any part of their Discord Profile; this provides…, Called when a member is kicked or leaves the Server/Guild. Returns a…, setup()

### Community 40 - "botPerms"
Cohesion: 0.36
Nodes (4): botPerms, Validates the contents of bot_perms.json., Checks a Users for a DB Role then checks for that Role inside of bot_perms.py,…, Pre build my Permissions Role Name List

### Community 41 - ".getStatus"
Cohesion: 0.17
Nodes (6): Use this to check if the AMP Dedicated Server(ADS) is running, NOT THE AMP…, AMP Instance(s) Thread Manager, AMP Instance Status Information, Returns AMP Instance Metrics \n `Uptime str` \n `TPS str` \n `Users…, Server is Online and Proper AMP Permissions. \n So we check TPS/State to make…, Returns Number of Online Players over Player Limit. \n `eg 2/10`

### Community 42 - "Commands List (COMMANDS.md)"
Cohesion: 0.20
Nodes (12): AMP Server Banner Commands, AMP Server Chat Commands, AMP Server Commands, AMP Server Console Commands, AMP Server Database Commands, AMP Server Event Commands, Bot Cog Commands, Bot Utils Commands (+4 more)

### Community 44 - ".check_GatekeeperRole_Permissions"
Cohesion: 0.17
Nodes (6): - Will check `Gatekeeper Role` for `Permission Nodes` when we have `Super…, Gets AMP user info. if IdOnly is True; returns AMP User ID only!, Returns AMP Users ID Only., Gets full permission spec for Role (returns permission nodes), Gets a List of all Roles, if set_roleID is true; it checks for `Gatekeeper` and…, Sets `self.AMP_BotRoleID` and `self.super_AdminID` (if they exist)

### Community 45 - "AMPConsole"
Cohesion: 0.23
Nodes (7): AMPConsole, ConsoleEntry, Controls what will be sent to the Discord Console Channel via AMP Console. \n…, This will handle all player chat messages from AMP to Discord.\n Format's…, This starts our console threads..., This handles AMP Console Updates; turns them into bite size messages and sends…, TypedDict

### Community 46 - "Handler"
Cohesion: 0.22
Nodes (5): Handler, Client, This is the Basic Module Loader for AMP to Discord Integration/Interactions, This loads all the required Cogs/Scripts for each unique AMPInstance.Module type, This will load all Cogs inside of the cogs folder.

### Community 47 - ".role_parse"
Cohesion: 0.22
Nodes (6): Member, Role, Adds a Role to a User.\n Requires a `<user`> and `<role>` discord object.\n…, Removes a Role from the User.\n Requires a `<user>` and `<role>` discord…, This is the bot utils Role Parse Function\n It handles finding the specificed…, This is the bot utils User Parse Function\n It handles finding the specificed…

### Community 49 - "async_rolecheck"
Cohesion: 0.24
Nodes (9): async_rolecheck(), autocomplete_servers(), autocomplete_servers_public(), get_botPerms(), Choice, Interaction, Autocomplete for AMP Instance Names, Autocomplete for AMP Instance Names (+1 more)

### Community 50 - "Why Use This Fork (Fork Lineage & Deltas)"
Cohesion: 0.29
Nodes (8): Update 4.7.5 (Banner Timezone/Time Format + pyproject.toml fix), Per-Lookup-Type Commands Need Subcommands, Not Enum Param, User/Member Group Commands, Why Use This Fork (Fork Lineage & Deltas), k8thekat/GatekeeperV2 (original project), leonbreidenbach-pc/GatekeeperV3 (upstream fork), Fixed Broken pyproject.toml, Merged /user lookup into /user info

### Community 51 - "Regex Documentation (REGEX.md)"
Cohesion: 0.32
Nodes (8): AMP Server Regex Commands, Bot Regex_Pattern Commands, Bot Regex Pattern Management, Regex Examples, Python Regex HOWTO (PyDoc), Regex101 (external tester), Regex Documentation (REGEX.md), Server Regex Pattern Management

### Community 52 - "AMPProjectzomboid"
Cohesion: 0.29
Nodes (4): AMPProjectzomboid, AMPProjectzomboidConsole, Sends a customized message via servermsg through the console., Used to Send a Broadcast Message to the Server

### Community 53 - "AMPSevendays"
Cohesion: 0.29
Nodes (4): AMPSevendays, AMPSevendaysConsole, Sends a customized message via say through the console., Used to Send a Broadcast Message to the Server

### Community 54 - "AMPTerraria"
Cohesion: 0.29
Nodes (4): AMPTerraria, AMPTerrariaConsole, Sends a customized message via say through the console., Used to Send a Broadcast Message to the Server

### Community 55 - "Banner Documentation (BANNER.md)"
Cohesion: 0.33
Nodes (7): Custom Banner Image Editor, Banner Display (Discord Embed / Custom Banner Image), Banner Group, Banner Documentation (BANNER.md), Color Hex (external tool), Bot BannerGroup Commands, Bot Banner_Settings Commands

### Community 56 - "AMPFactorio"
Cohesion: 0.33
Nodes (3): AMPFactorio, AMPFactorioConsole, Sets the Permissions for Factorio Modules

### Community 58 - "I18nHandler"
Cohesion: 0.21
Nodes (3): I18nHandler, Re-derives each command/param/choice's locale key from its live…, Loads locale files and resolves translation keys for the currently active…

### Community 60 - "cog_csgo.py"
Cohesion: 0.50
Nodes (3): Csgo, Bot, setup()

### Community 61 - "cog_factorio.py"
Cohesion: 0.50
Nodes (3): Factorio, Bot, setup()

### Community 62 - "cog_starbound.py"
Cohesion: 0.50
Nodes (3): Bot, setup(), Starbound

### Community 63 - "Context"
Cohesion: 0.25
Nodes (5): Context, Handles the reply message for the whitelist event\n Supports the following: \n…, This is the botUtils Server Parse function. **Note** Use context.guild.id \n…, Verifies if the AMP Server exists and if its Instance is running and its ADS is…, Use to get a Users Role Prefix for displaying.

### Community 64 - "cog_valheim.py"
Cohesion: 0.50
Nodes (3): Bot, setup(), Valheim

### Community 66 - ".channel_parse"
Cohesion: 0.33
Nodes (4): datetime, TextChannel, This will be used to access channel history up to 100. Simple scraper with…, This is the bot utils Channel Parse Function\n It handles finding the…

### Community 68 - "CLAUDE.md Project Guidance"
Cohesion: 0.40
Nodes (5): Database Layer, DB.py (Database wrapper), DB_Update.py (versioned DB migrations), Gatekeeper Project (fork lineage & maintenance mode), CLAUDE.md Project Guidance

### Community 77 - ".user_role"
Cohesion: 0.14
Nodes (11): Permissions, autocomplete, Choice, Client, Context, hybrid_command, Interaction, Member (+3 more)

### Community 80 - "Cleanup-Roadmap"
Cohesion: 0.29
Nodes (6): 1. Toter Code 🟢 ✅ Erledigt, 2. Docstring-/Kommentar-Bloat 🟢, 3. Datei-Duplikate / veraltete Docs 🟡, 4. Backlog — bewusst zurückgestellt 🔴, Cleanup-Roadmap, Vorschlag für die Reihenfolge, wenn's losgeht

## Knowledge Gaps
- **34 isolated node(s):** `GatekeeperV3.1`, `1. Toter Code 🟢 ✅ Erledigt`, `2. Docstring-/Kommentar-Bloat 🟢`, `3. Datei-Duplikate / veraltete Docs 🟡`, `4. Backlog — bewusst zurückgestellt 🔴` (+29 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **21 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `AMPInstance` connect `AMPInstance` to `Banner`, `WhitelistSync`, `Whitelist`, `.Login`, `AMP.py`, `Banner_Generator`, `botUtils`, `botEmbeds`, `.emptyTrash`, `.trashDirectory`, `.__init__`, `.__init__`, `AMP_Tasks`, `Edited_DB_Banner`, `.getStatus`, `.check_GatekeeperRole_Permissions`, `AMPConsole`, `Context`, `.CurrentSessionHasPermission`, `.ConsoleMessage_withUpdate`?**
  _High betweenness centrality (0.223) - this node is a cross-community bridge._
- **Why does `role_check()` connect `role_check` to `discordBot.py`, `Banner`, `WhitelistSync`, `DB.py`, `Whitelist`, `Cog_Template`, `.user_role`, `DB_User`, `async_rolecheck`, `Regex`, `DB_Server`?**
  _High betweenness centrality (0.153) - this node is a cross-community bridge._
- **Why does `Banner` connect `Banner` to `Edited_DB_Banner`, `DB.py`?**
  _High betweenness centrality (0.099) - this node is a cross-community bridge._
- **Are the 13 inferred relationships involving `AMPInstance` (e.g. with `AMPHandler` and `AMPConsole`) actually correct?**
  _`AMPInstance` has 13 INFERRED edges - model-reasoned connections that need verification._
- **Are the 14 inferred relationships involving `Edited_DB_Banner` (e.g. with `DBBanner` and `Cancel_Banner_Button`) actually correct?**
  _`Edited_DB_Banner` has 14 INFERRED edges - model-reasoned connections that need verification._
- **Are the 6 inferred relationships involving `DB_Update` (e.g. with `Database` and `DBBanner`) actually correct?**
  _`DB_Update` has 6 INFERRED edges - model-reasoned connections that need verification._
- **What connects `GatekeeperV3.1`, `1. Toter Code 🟢 ✅ Erledigt`, `2. Docstring-/Kommentar-Bloat 🟢` to the rest of the system?**
  _34 weakly-connected nodes found - possible documentation gaps or missing edges._