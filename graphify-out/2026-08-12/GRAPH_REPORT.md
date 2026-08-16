# Graph Report - GatekeeperV3.1  (2026-08-12)

## Corpus Check
- 72 files · ~327,779 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1334 nodes · 2624 edges · 82 communities (63 shown, 19 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 79 edges (avg confidence: 0.5)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `fbabd342`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- discordBot.py
- role_check
- Banner
- .__init__
- WhitelistSync
- DB.py
- Whitelist
- .Login
- Cog_Template
- Edited_DB_Banner
- AMPMinecraft
- AMP.py
- DB_Update
- Banner_Generator
- AMPInstance
- Database
- ._fetchone
- DB_User
- botUtils
- botEmbeds
- **Commands List**
- Regex
- **Interacting with the Bot**
- AMPTemplate
- ._execute
- DBServer
- AMPHandler
- DB_Server
- **Regex**
- Cancel_Banner_Button
- .__init__
- discordBot
- I18nHandler
- Python 3.13 Bootstrap Compatibility Fixes
- Banner_Editor_View
- DBConfig
- amp_starbound.py
- .getStatus
- .check_GatekeeperRole_Permissions
- Minecraft
- **Enabling Custom Permissons**
- .role_parse
- **Whitelist**
- .RemoveServerWhitelistRole
- async_rolecheck
- AMPConsole
- Context
- botPerms
- Banner_Editor_Select
- cog_sevendays.py
- DBUser
- AMP_Tasks
- AMPProjectzomboid
- AMPSevendays
- AMPTerraria
- .channel_parse
- AMPFactorio
- **Banner**
- Production deployment log (Hetzner, `fullsendhub.de`)
- **Adding a Language**
- .AddServerWhitelistRole
- cog_factorio.py
- cog_starbound.py
- cog_csgo.py
- cog_valheim.py
- start.py
- amp_valheim.py
- .CurrentSessionHasPermission
- .ConsoleMessage_withUpdate
- modal.py
- generic.py
- GatekeeperV4
- changelog.md
- .RestartInstance
- cog_projectzomboid.py
- cog_terraria.py
- permissions_cog.py
- amp_permissions.py
- start.py (Setup / startup sequence)
- Bug Report Issue Template

## God Nodes (most connected - your core abstractions)
1. `AMPInstance` - 107 edges
2. `role_check()` - 100 edges
3. `Database` - 57 edges
4. `DB_Update` - 41 edges
5. `Edited_DB_Banner` - 40 edges
6. `AMP_Server` - 36 edges
7. `Banner` - 34 edges
8. `WhitelistSync` - 30 edges
9. `Banner_Editor_View` - 28 edges
10. `AMPHandler` - 27 edges

## Surprising Connections (you probably didn't know these)
- `AMP_Tasks` --uses--> `AMPInstance`  [INFERRED]
  cogs/amp_tasks_cog.py → core/AMP.py
- `Banner` --uses--> `Banner_Editor_View`  [INFERRED]
  cogs/banner_cog.py → utils_dev/banner_editor/ui/view.py
- `Whitelist` --uses--> `Gatekeeper`  [INFERRED]
  cogs/whitelist_cog.py → core/discordBot.py
- `WhitelistSync` --uses--> `Gatekeeper`  [INFERRED]
  cogs/whitelist_sync_cog.py → core/discordBot.py
- `Cancel_Banner_Button` --uses--> `AMPInstance`  [INFERRED]
  utils_dev/banner_editor/ui/button.py → core/AMP.py

## Import Cycles
- 3-file cycle: `utils_dev/banner_editor/ui/button.py -> utils_dev/banner_editor/ui/modal.py -> utils_dev/banner_editor/ui/view.py -> utils_dev/banner_editor/ui/button.py`
- 4-file cycle: `utils_dev/banner_editor/ui/button.py -> utils_dev/banner_editor/ui/modal.py -> utils_dev/banner_editor/ui/textinput.py -> utils_dev/banner_editor/ui/view.py -> utils_dev/banner_editor/ui/button.py`

## Hyperedges (group relationships)
- **Python 3.13 / Hetzner Deployment Compatibility Fix Batch** — claude_python313_compatibility_fixes, requirements_dependencies, claude_logger, claude_amp_instance, claude_amp_permissions [EXTRACTED 1.00]

## Communities (82 total, 19 thin omitted)

### Community 0 - "discordBot.py"
Cohesion: 0.07
Nodes (49): autocomplete_loadedcogs(), bot_cog(), bot_cog_loader(), bot_cog_reload(), bot_cog_unloader(), bot_language(), bot_moderator(), bot_permissions() (+41 more)

### Community 1 - "role_check"
Cohesion: 0.11
Nodes (21): AMP_Server, autocomplete, Choice, choices, Client, command, Context, group (+13 more)

### Community 2 - "Banner"
Cohesion: 0.08
Nodes (26): Banner, autocomplete, Bot, Choice, choices, command, Context, datetime (+18 more)

### Community 3 - ".__init__"
Cohesion: 0.06
Nodes (33): Accept_Whitelist_Button, Approve_Button, Cancel_Button, Confirm_Link_Button, DB_Instance_ID_Swap, Deny_Link_Button, Deny_Whitelist_Button, KillButton (+25 more)

### Community 4 - "WhitelistSync"
Cohesion: 0.08
Nodes (29): before_loop, autocomplete, Bot, Choice, choices, command, Context, DBUser (+21 more)

### Community 5 - "DB.py"
Cohesion: 0.21
Nodes (11): setup(), Request the AMP handler background loops to stop., request_shutdown(), datetime, get_language(), getI18nHandler(), # NOTE: `Command._params` is a private/undocumented discord.py attribute…, retranslate_command_tree() (+3 more)

### Community 6 - "Whitelist"
Cohesion: 0.10
Nodes (22): autocomplete, Bot, Choice, choices, command, Context, describe, GuildChannel (+14 more)

### Community 7 - ".Login"
Cohesion: 0.08
Nodes (14): This is the main API Call function, This gets all Instances on AMP., Basic Console Message, Returns a List of connected users., This is used to change an Instance's Friendly Name and or Description. Retains…, Test AMP API calls with this function, Ends specified User Session, Returns currently active AMP Sessions (+6 more)

### Community 8 - "Cog_Template"
Cohesion: 0.08
Nodes (24): guild_check(), Use this before any commands to limit it to a certain guild usage., guilds, Reaction, Cog_Template, autocomplete, Client, command (+16 more)

### Community 9 - "Edited_DB_Banner"
Cohesion: 0.19
Nodes (8): DBBanner, Edited_DB_Banner, DB_Banner for Banner Editor All `attrs` inside this class must have a `_`…, Copy_To_Select, Interaction, Select, Copy_To_View, View

### Community 10 - "AMPMinecraft"
Cohesion: 0.09
Nodes (15): AMPMinecraft, AMPMinecraftConsole, DBUser, Gets a Users Player Head via UUID, Bans a User from the Server, Sends a customized message via tellraw through the console., Formats the message for Discord \n, Handles returning customized discord message data for Minecraft Servers only. (+7 more)

### Community 11 - "AMP.py"
Cohesion: 0.19
Nodes (4): AMPCsgo, AMPCsgoConsole, AMPGeneric, AMPGenericConsole

### Community 12 - "DB_Update"
Cohesion: 0.10
Nodes (4): DB_Update, SQLITE does not support dropping UNIQUE constraint, SQLITE does not support adding UNIQUE constraint, Seeds every Server row's new Auto_Whitelist/Whitelist_Wait_Time from the old…

### Community 13 - "Banner_Generator"
Cohesion: 0.14
Nodes (10): ImageFont, Banner_Generator, Image, Custom Banner Generator for Gatekeeper., Blurs the Background Image with GaussianBlur, Custom Word Wrap. Returns a `list` when `truncate` is `False`, Adjusted the RGB values for Player Limit Display., Rounds the corners of the Background Image. (+2 more)

### Community 14 - "AMPInstance"
Cohesion: 0.08
Nodes (13): AMPInstance, DBUser, Base Function for AMP.addWhitelist, Base Function for AMP.getWhitelist, Base Function for AMP.removeWhitelist, Base Function for AMP.name_Conversion, Base Function for AMP.name_History, Base Function for Discord Chat Messages to AMP ADS (+5 more)

### Community 15 - "Database"
Cohesion: 0.12
Nodes (11): Database, Gets all Servers current in the DB, Returns all ServerIDs that the provided Discord Role ID gates Whitelist access…, Returns all ServerIDs that the provided Discord Role ID gates Donator access…, Gets all Regex Patterns from the RegexPatterns Table. Returns…, Gets all Whitelist Replies currently in the DB, Gets a Specific Banner Groups full information return…, Gets all BannerGroups Names/IDs returns `Banners[entry["ID"]] = entry["name"]` (+3 more)

### Community 16 - "._fetchone"
Cohesion: 0.09
Nodes (13): DBServer, Removes a entry RegexPatterns Table using either its `Name` or `ID`, Returns RegexPatterns Table Returns `row['ID'] = {'Name': row['Name'], 'Type':…, Update a Regex Pattern in the RegexPatterns Table using either its `Name` or…, Selects a Banner Group Table matching the `name` provided., Update a Banner Group, Removes a Banner Group., Add a Server to an existing Banner Group. (+5 more)

### Community 17 - "DB_User"
Cohesion: 0.20
Nodes (11): DB_User, Client, command, Context, describe, group, hybrid_group, listener (+3 more)

### Community 18 - "botUtils"
Cohesion: 0.08
Nodes (13): botUtils, Gatekeeper Utility Class, Formats the message for Discord `Bold = \\x01, \\x02` `Italic = \\x03, \\x04`…, This checks the DB Server objects Avatar_url and returns the proper object…, Converts an IGN to a UUID/Name Table `returns 'uuid'` else returns `None`,…, Resolves a Minecraft in-game name into profile info via the official Mojang…, Converts a Steam Name to a Steam ID returns `STEAM_0:0:2806383`, Returns `True` if a Steam Web API Key has been set via GATEKEEPER_STEAM_API_KEY (+5 more)

### Community 19 - "botEmbeds"
Cohesion: 0.13
Nodes (15): botEmbeds, Bot, Context, DBServer, DBUser, Embed, Guild, User (+7 more)

### Community 20 - "**Commands List**"
Cohesion: 0.08
Nodes (23): **Commands List**, **Interacting with your AMP Server via Discord Channels**:, <u>AMP Server Banner Commands</u>:, <u>AMP Server Chat Commands</u>:, <u>AMP Server Commands</u>:, <u>AMP Server Console Commands</u>:, <u>AMP Server Database Commands</u>:, <u>AMP Server Event Commands</u>: (+15 more)

### Community 21 - "Regex"
Cohesion: 0.17
Nodes (12): autocomplete, Choice, choices, Client, command, Context, describe, hybrid_group (+4 more)

### Community 22 - "**Interacting with the Bot**"
Cohesion: 0.08
Nodes (24): **AMP Instance Instructions**, **Creating a Discord Bot Account**, **First Time Startup**, **Installation Methods**, Installing Python 3.13, Installing Python on Linux, Installing Python on  Windows, **Interacting with the Bot** (+16 more)

### Community 23 - "AMPTemplate"
Cohesion: 0.12
Nodes (8): AMPTemplate, AMPTemplateConsole, Sets the Permissions for Template Modules, Sends a message in a way to mimic that of in-game Chat Messages., Base Function for Broadcast Messages to AMP ADS, Base Function for AMP.addWhitelist, Base Function for AMP.getWhitelist, Base Function for AMP.removeWhitelist

### Community 24 - "._execute"
Cohesion: 0.17
Nodes (6): dump_to_json(), Adds a entry to table RegexPatterns, else Updates a matching pattern., Adds a Whitelist Reply to the DB, Deletes a Whitelist Reply from the DB, Creates a Banner Group Table with the provided `name`, Removes a Discord Message ID from a BannerGroup

### Community 25 - "DBServer"
Cohesion: 0.09
Nodes (11): DBServer, DB Server Attributes: `InstanceID: str` `InstanceName: str` `FriendlyName: str`…, Adds the provided RegexPattern ID/Name to the ServerRegexPatterns Table., Removes the provided RegexPattern ID/Name from the ServerRegexPatterns Table., Gets all Regex Patterns related to Server Returns `dict['ID': {'Name':…, Gets all Discord Role IDs gating Whitelist access for this Server., Adds a Discord Role ID to this Server's Donator Role gate list. Any one of…, Removes a Discord Role ID from this Server's Donator Role gate list. (+3 more)

### Community 26 - "AMPHandler"
Cohesion: 0.16
Nodes (12): AMP_init(), amp_server_instance_check(), AMPHandler, getAMPHandler(), Intializes the connection to AMP and creates AMP_Instance objects., Creates a list of Instance Names/DisplayName or Friendly Name., Builds a tokens-like namespace from environment variables (optionally loaded…, Validates the .env/environment-variable settings and 2FA. (+4 more)

### Community 27 - "DB_Server"
Cohesion: 0.16
Nodes (11): DB_Server, autocomplete, Choice, Client, command, Context, describe, hybrid_group (+3 more)

### Community 28 - "**Regex**"
Cohesion: 0.12
Nodes (16): ADD:, ADD:, DELETE:, DELETE:, Examples, **How Console Filtering can affect your Regex Patterns**, **How to Manage your Bot Regex Patterns**, **How to Manage your Servers Regex Patterns** (+8 more)

### Community 29 - "Cancel_Banner_Button"
Cohesion: 0.13
Nodes (14): Cancel_Banner_Button, Copy_To_All_Banner_Button, Copy_To_Banner_Button, Button, Interaction, Message, Coppies the current banner settings to the Text Input server., Resets the Banners current settings to the original DB. (+6 more)

### Community 30 - ".__init__"
Cohesion: 0.18
Nodes (6): Creates the `Gatekeeper` role, Adds us to the Membership of that Role and sets…, Sets the Permissions Nodes for AMP Gatekeeper Role, This is used to set/update the DB attributes for the AMP server, Creates a AMP User role, Sets the AMP Users Role Membership, Sets the AMP Role permission Node eg `Core.RoleManagement.DeleteRoles`

### Community 31 - "discordBot"
Cohesion: 0.15
Nodes (9): discordBot, Client, Embed, Message, Deletes `message`. Deleting another user's message requires the…, Edits `message`; `content` must be convertible to `str`., Sends `content` to `parameter`. Only one of `file`/`files` may be given, not…, The name and ID of a custom emoji can be found with the client by prefixing… (+1 more)

### Community 32 - "I18nHandler"
Cohesion: 0.21
Nodes (3): I18nHandler, Re-derives each command/param/choice's locale key from its live…, Loads locale files and resolves translation keys for the currently active…

### Community 33 - "Python 3.13 Bootstrap Compatibility Fixes"
Cohesion: 0.06
Nodes (43): AMP_Handler.py (AMPHandler singleton), AMP.py (AMPInstance base class), AMP Integration Layer, amp_permissions.py (AMP permission profiles), AMP Bot Role/Permission Bootstrap Ordering Bug, Core.UserManagement.ViewUserInfo Self-Check Crash Fix, Database Layer, DB.py (Database wrapper) (+35 more)

### Community 34 - "Banner_Editor_View"
Cohesion: 0.16
Nodes (14): Modal, TextInput, TextStyle, Banner_Modal, Copy_To_Modal, Interaction, Message, Used for Copy To Button within the Banner Settings Editor View. (+6 more)

### Community 35 - "DBConfig"
Cohesion: 0.15
Nodes (4): DBConfig, DBHandler, getDBHandler(), This sets the DB Server Console_Flag, Console_Filtered and…

### Community 37 - ".getStatus"
Cohesion: 0.17
Nodes (6): Use this to check if the AMP Dedicated Server(ADS) is running, NOT THE AMP…, AMP Instance(s) Thread Manager, AMP Instance Status Information, Returns `(TPS: str, Users: tuple(str, str), CPU: str, Memory: tuple(str, str),…, Server is Online and Proper AMP Permissions. So we check TPS/State to make sure…, Returns Number of Online Players over Player Limit. `eg 2/10`

### Community 38 - ".check_GatekeeperRole_Permissions"
Cohesion: 0.17
Nodes (6): - Will check `Gatekeeper Role` for `Permission Nodes` when we have `Super…, Gets AMP user info. if IdOnly is True; returns AMP User ID only!, Returns AMP Users ID Only., Gets full permission spec for Role (returns permission nodes), Gets a List of all Roles, if set_roleID is true; it checks for `Gatekeeper` and…, Sets `self.AMP_BotRoleID` and `self.super_AdminID` (if they exist)

### Community 39 - "Minecraft"
Cohesion: 0.20
Nodes (8): Minecraft, Bot, listener, Member, User, Called when a User updates any part of their Discord Profile; this provides…, Called when a member is kicked or leaves the Server/Guild. Returns a…, setup()

### Community 40 - "**Enabling Custom Permissons**"
Cohesion: 0.17
Nodes (11): Adding Permissions:, Adding Wildcard Permissions:, Discord Console Channel Permissions:, **Enabling Custom Permissons**, **Features**, **Full Permission Node List**, **Permissions**, Removing Permissions: (+3 more)

### Community 41 - ".role_parse"
Cohesion: 0.22
Nodes (6): Member, Role, Adds `role` to `user`., Removes `role` from `user`., This is the bot utils Role Parse Function It handles finding the specificed…, This is the bot utils User Parse Function It handles finding the specificed…

### Community 42 - "**Whitelist**"
Cohesion: 0.15
Nodes (12): **Account Linking**, Behavior:, Behavior:, **Discord Role Whitelist Sync**, **Donator Roles**, Player-facing:, Setup:, Setup: (+4 more)

### Community 44 - "async_rolecheck"
Cohesion: 0.28
Nodes (9): async_rolecheck(), autocomplete_servers(), autocomplete_servers_public(), get_botPerms(), Choice, Interaction, Autocomplete for AMP Instance Names, Autocomplete for AMP Instance Names (+1 more)

### Community 45 - "AMPConsole"
Cohesion: 0.23
Nodes (7): AMPConsole, ConsoleEntry, Controls what will be sent to the Discord Console Channel via AMP Console.…, This will handle all player chat messages from AMP to Discord. Format's Server…, This starts our console threads..., This handles AMP Console Updates; turns them into bite size messages and sends…, TypedDict

### Community 46 - "Context"
Cohesion: 0.25
Nodes (5): Context, Fills whitelist reply placeholders: `<user>`, `<server>`, `<guild>`., This is the botUtils Server Parse function. **Note** Use context.guild.id…, Verifies if the AMP Server exists and if its Instance is running and its ADS is…, Use to get a Users Role Prefix for displaying.

### Community 47 - "botPerms"
Cohesion: 0.36
Nodes (4): botPerms, Validates the contents of bot_perms.json., Checks a Users for a DB Role then checks for that Role inside of bot_perms.py,…, Pre build my Permissions Role Name List

### Community 48 - "Banner_Editor_Select"
Cohesion: 0.33
Nodes (5): banner_field_label(), Banner_Editor_Select, Interaction, Message, Select

### Community 51 - "AMP_Tasks"
Cohesion: 0.15
Nodes (10): AMP_Tasks, Bot, Client, listener, loop, Message, This handles AMP Console messages and sends them to discord., This handles AMP Console Event messages and sends them to discord. (+2 more)

### Community 52 - "AMPProjectzomboid"
Cohesion: 0.29
Nodes (4): AMPProjectzomboid, AMPProjectzomboidConsole, Sends a customized message via servermsg through the console., Used to Send a Broadcast Message to the Server

### Community 53 - "AMPSevendays"
Cohesion: 0.29
Nodes (4): AMPSevendays, AMPSevendaysConsole, Sends a customized message via say through the console., Used to Send a Broadcast Message to the Server

### Community 54 - "AMPTerraria"
Cohesion: 0.29
Nodes (4): AMPTerraria, AMPTerrariaConsole, Sends a customized message via say through the console., Used to Send a Broadcast Message to the Server

### Community 55 - ".channel_parse"
Cohesion: 0.33
Nodes (4): datetime, TextChannel, This will be used to access channel history up to 100. Simple scraper with…, This is the bot utils Channel Parse Function It handles finding the specificed…

### Community 56 - "AMPFactorio"
Cohesion: 0.33
Nodes (3): AMPFactorio, AMPFactorioConsole, Sets the Permissions for Factorio Modules

### Community 57 - "**Banner**"
Cohesion: 0.33
Nodes (5): **Banner**, **Editing your Server Banner/Embed**, **How to Display your Banners**, Using the Custom Banner Image Editor:, **What is a Banner?**

### Community 59 - "**Adding a Language**"
Cohesion: 0.33
Nodes (5): **Adding a Language**, How it works, Key naming (for anything you add later, not for translating existing keys), Steps, Things to watch for

### Community 61 - "cog_factorio.py"
Cohesion: 0.50
Nodes (3): Factorio, Bot, setup()

### Community 62 - "cog_starbound.py"
Cohesion: 0.50
Nodes (3): Bot, setup(), Starbound

### Community 63 - "cog_csgo.py"
Cohesion: 0.50
Nodes (3): Csgo, Bot, setup()

### Community 64 - "cog_valheim.py"
Cohesion: 0.50
Nodes (3): Bot, setup(), Valheim

### Community 69 - "modal.py"
Cohesion: 0.28
Nodes (5): banner_file_handler(), Image, Saves the Banners current settings to the DB., This is called when a button is interacted with., Save_Banner_Button

### Community 77 - "permissions_cog.py"
Cohesion: 0.25
Nodes (6): Permissions, Choice, Client, Interaction, This is for roles inside of the bot_perms file. Returns a list of all the…, setup()

## Knowledge Gaps
- **96 isolated node(s):** `GatekeeperV4`, `**What is a Banner?**`, `Using the Custom Banner Image Editor:`, `**How to Display your Banners**`, `**Using your commands!**` (+91 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **19 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `AMPInstance` connect `AMPInstance` to `Banner`, `.__init__`, `WhitelistSync`, `Whitelist`, `.Login`, `AMP.py`, `Banner_Generator`, `botUtils`, `botEmbeds`, `AMPHandler`, `Cancel_Banner_Button`, `.__init__`, `Banner_Editor_View`, `.getStatus`, `.check_GatekeeperRole_Permissions`, `AMPConsole`, `Context`, `Banner_Editor_Select`, `AMP_Tasks`, `.CurrentSessionHasPermission`, `.ConsoleMessage_withUpdate`, `modal.py`, `.RestartInstance`?**
  _High betweenness centrality (0.214) - this node is a cross-community bridge._
- **Why does `role_check()` connect `role_check` to `discordBot.py`, `Banner`, `WhitelistSync`, `DB.py`, `Whitelist`, `Cog_Template`, `async_rolecheck`, `DB_User`, `Regex`, `DB_Server`?**
  _High betweenness centrality (0.131) - this node is a cross-community bridge._
- **Why does `Database` connect `Database` to `DBConfig`, `DB.py`, `.RemoveServerWhitelistRole`, `DB_Update`, `._fetchone`, `DBUser`, `._execute`, `DBServer`, `.AddServerWhitelistRole`?**
  _High betweenness centrality (0.128) - this node is a cross-community bridge._
- **Are the 13 inferred relationships involving `AMPInstance` (e.g. with `AMP_Tasks` and `AMPHandler`) actually correct?**
  _`AMPInstance` has 13 INFERRED edges - model-reasoned connections that need verification._
- **Are the 6 inferred relationships involving `DB_Update` (e.g. with `Database` and `DBBanner`) actually correct?**
  _`DB_Update` has 6 INFERRED edges - model-reasoned connections that need verification._
- **Are the 14 inferred relationships involving `Edited_DB_Banner` (e.g. with `DBBanner` and `Cancel_Banner_Button`) actually correct?**
  _`Edited_DB_Banner` has 14 INFERRED edges - model-reasoned connections that need verification._
- **What connects `GatekeeperV4`, `**What is a Banner?**`, `Using the Custom Banner Image Editor:` to the rest of the system?**
  _96 weakly-connected nodes found - possible documentation gaps or missing edges._