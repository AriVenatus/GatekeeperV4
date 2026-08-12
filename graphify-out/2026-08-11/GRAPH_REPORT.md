# Graph Report - GatekeeperV3.1  (2026-08-11)

## Corpus Check
- 73 files · ~327,746 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1318 nodes · 2571 edges · 83 communities (60 shown, 23 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 71 edges (avg confidence: 0.5)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `2d43ba7f`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- discordBot.py
- role_check
- Banner
- utils_ui.py
- WhitelistSync
- DB.py
- Whitelist
- .Login
- Cog_Template
- I18nHandler
- AMPMinecraft
- amp_starbound.py
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
- AMP_init
- db_server_cog.py
- **Regex**
- i18n.py
- .__init__
- discordBot
- amp_generic.py
- Python 3.13 Bootstrap Compatibility Fixes
- Edited_DB_Banner
- DBConfig
- .AddServerWhitelistRole
- .getStatus
- .check_GatekeeperRole_Permissions
- cog_minecraft.py
- **Enabling Custom Permissons**
- .role_parse
- **Whitelist**
- .RemoveServerWhitelistRole
- utils.py
- AMP_Console.py
- Context
- botPerms
- Cleanup-Roadmap
- cog_sevendays.py
- DBUser
- DBHandler
- amp_projectzomboid.py
- amp_sevendays.py
- amp_terraria.py
- .channel_parse
- amp_factorio.py
- **Banner**
- Production deployment log (Hetzner, `fullsendhub.de`)
- **Adding a Language**
- amp_csgo.py
- cog_factorio.py
- cog_starbound.py
- cog_csgo.py
- cog_valheim.py
- Setup
- amp_valheim.py
- .CurrentSessionHasPermission
- .ConsoleMessage_withUpdate
- .get_steam_profile
- generic.py
- GatekeeperV4
- changelog.md
- .RestartInstance
- cog_projectzomboid.py
- cog_terraria.py
- permissions_cog.py
- datetime
- DBServer
- start.py (Setup / startup sequence)
- Bug Report Issue Template

## God Nodes (most connected - your core abstractions)
1. `AMPInstance` - 107 edges
2. `role_check()` - 99 edges
3. `Database` - 53 edges
4. `Edited_DB_Banner` - 40 edges
5. `AMP_Server` - 36 edges
6. `Banner` - 34 edges
7. `DB_Update` - 30 edges
8. `Banner_Editor_View` - 28 edges
9. `AMPHandler` - 27 edges
10. `t()` - 26 edges

## Surprising Connections (you probably didn't know these)
- `AMPMinecraft` --uses--> `DBUser`  [INFERRED]
  modules/Minecraft/amp_minecraft.py → core/DB.py
- `AMPMinecraftConsole` --uses--> `DBUser`  [INFERRED]
  modules/Minecraft/amp_minecraft.py → core/DB.py
- `Copy_To_Select` --uses--> `DBServer`  [INFERRED]
  utils_dev/banner_editor/ui/copy_to_select.py → core/DB.py
- `AMP_Tasks` --uses--> `AMPInstance`  [INFERRED]
  cogs/amp_tasks_cog.py → core/AMP.py
- `Banner` --uses--> `Banner_Editor_View`  [INFERRED]
  cogs/banner_cog.py → utils_dev/banner_editor/ui/view.py

## Import Cycles
- 3-file cycle: `utils_dev/banner_editor/ui/button.py -> utils_dev/banner_editor/ui/modal.py -> utils_dev/banner_editor/ui/view.py -> utils_dev/banner_editor/ui/button.py`
- 4-file cycle: `utils_dev/banner_editor/ui/button.py -> utils_dev/banner_editor/ui/modal.py -> utils_dev/banner_editor/ui/textinput.py -> utils_dev/banner_editor/ui/view.py -> utils_dev/banner_editor/ui/button.py`

## Hyperedges (group relationships)
- **Python 3.13 / Hetzner Deployment Compatibility Fix Batch** — claude_python313_compatibility_fixes, requirements_dependencies, claude_logger, claude_amp_instance, claude_amp_permissions [EXTRACTED 1.00]

## Communities (83 total, 23 thin omitted)

### Community 0 - "discordBot.py"
Cohesion: 0.10
Nodes (45): autocomplete_loadedcogs(), bot_cog(), bot_cog_loader(), bot_cog_reload(), bot_cog_unloader(), bot_donator(), bot_language(), bot_moderator() (+37 more)

### Community 1 - "role_check"
Cohesion: 0.11
Nodes (21): AMP_Server, autocomplete, Choice, choices, Client, command, Context, group (+13 more)

### Community 2 - "Banner"
Cohesion: 0.08
Nodes (26): Banner, autocomplete, Bot, Choice, choices, command, Context, datetime (+18 more)

### Community 3 - "utils_ui.py"
Cohesion: 0.06
Nodes (33): Accept_Whitelist_Button, Approve_Button, Cancel_Button, Confirm_Link_Button, DB_Instance_ID_Swap, Deny_Link_Button, Deny_Whitelist_Button, KillButton (+25 more)

### Community 4 - "WhitelistSync"
Cohesion: 0.06
Nodes (30): before_loop, autocomplete, Choice, choices, command, Context, DBUser, describe (+22 more)

### Community 5 - "DB.py"
Cohesion: 0.14
Nodes (10): setup(), setup(), Bot, setup(), Bot, setup(), Request the AMP handler background loops to stop., request_shutdown() (+2 more)

### Community 6 - "Whitelist"
Cohesion: 0.10
Nodes (20): autocomplete, Choice, choices, command, Context, describe, GuildChannel, hybrid_command (+12 more)

### Community 7 - ".Login"
Cohesion: 0.08
Nodes (14): This is the main API Call function, This gets all Instances on AMP., Basic Console Message, Returns a List of connected users., This is used to change an Instance's Friendly Name and or Description. Retains…, Test AMP API calls with this function, Ends specified User Session, Returns currently active AMP Sessions (+6 more)

### Community 8 - "Cog_Template"
Cohesion: 0.08
Nodes (24): guild_check(), Use this before any commands to limit it to a certain guild usage., guilds, Reaction, Cog_Template, autocomplete, Client, command (+16 more)

### Community 9 - "I18nHandler"
Cohesion: 0.21
Nodes (3): I18nHandler, Re-derives each command/param/choice's locale key from its live…, Loads locale files and resolves translation keys for the currently active…

### Community 10 - "AMPMinecraft"
Cohesion: 0.05
Nodes (25): AMP_Tasks, Bot, Client, listener, loop, Message, This handles AMP Console messages and sends them to discord., This handles AMP Console Event messages and sends them to discord. (+17 more)

### Community 12 - "DB_Update"
Cohesion: 0.12
Nodes (3): DB_Update, SQLITE does not support dropping UNIQUE constraint, SQLITE does not support adding UNIQUE constraint

### Community 13 - "Banner_Generator"
Cohesion: 0.14
Nodes (10): ImageFont, Banner_Generator, Image, Custom Banner Generator for Gatekeeper., Blurs the Background Image with GaussianBlur, Custom Word Wrap. Returns a `list` when `truncate` is `False`, Adjusted the RGB values for Player Limit Display., Rounds the corners of the Background Image. (+2 more)

### Community 14 - "AMPInstance"
Cohesion: 0.08
Nodes (13): AMPInstance, DBUser, Base Function for AMP.addWhitelist, Base Function for AMP.getWhitelist, Base Function for AMP.removeWhitelist, Base Function for AMP.name_Conversion, Base Function for AMP.name_History, Base Function for Discord Chat Messages to AMP ADS (+5 more)

### Community 15 - "Database"
Cohesion: 0.12
Nodes (11): Database, Gets all Servers current in the DB, Returns all ServerIDs that the provided Discord Role ID gates Whitelist access…, Gets all Regex Patterns from the RegexPatterns Table. Returns…, Gets all Whitelist Replies currently in the DB, Gets a Specific Banner Groups full information return…, Gets all BannerGroups Names/IDs returns `Banners[entry["ID"]] = entry["name"]`, Removes a Banner Group. (+3 more)

### Community 16 - "._fetchone"
Cohesion: 0.11
Nodes (11): Removes a entry RegexPatterns Table using either its `Name` or `ID`, Returns RegexPatterns Table Returns `row['ID'] = {'Name': row['Name'], 'Type':…, Update a Regex Pattern in the RegexPatterns Table using either its `Name` or…, Selects a Banner Group Table matching the `name` provided., Update a Banner Group, Add a Server to an existing Banner Group., Removes a Server from an existing Banner Group., Add a Channel to a BannerGroups listing. (+3 more)

### Community 17 - "DB_User"
Cohesion: 0.21
Nodes (10): DB_User, Client, command, Context, describe, group, hybrid_group, listener (+2 more)

### Community 18 - "botUtils"
Cohesion: 0.10
Nodes (11): botUtils, Gatekeeper Utility Class, Formats the message for Discord `Bold = \\x01, \\x02` `Italic = \\x03, \\x04`…, This checks the DB Server objects Avatar_url and returns the proper object…, Converts an IGN to a UUID/Name Table `returns 'uuid'` else returns `None`,…, Resolves a Minecraft in-game name into profile info via the official Mojang…, Converts a Steam Name to a Steam ID returns `STEAM_0:0:2806383`, Returns `True` if a Steam Web API Key has been set via GATEKEEPER_STEAM_API_KEY (+3 more)

### Community 19 - "botEmbeds"
Cohesion: 0.13
Nodes (15): botEmbeds, Bot, Context, DBServer, DBUser, Embed, Guild, User (+7 more)

### Community 20 - "**Commands List**"
Cohesion: 0.08
Nodes (23): **Commands List**, **Interacting with your AMP Server via Discord Channels**:, <u>AMP Server Banner Commands</u>:, <u>AMP Server Chat Commands</u>:, <u>AMP Server Commands</u>:, <u>AMP Server Console Commands</u>:, <u>AMP Server Database Commands</u>:, <u>AMP Server Event Commands</u>: (+15 more)

### Community 21 - "Regex"
Cohesion: 0.16
Nodes (12): autocomplete, Choice, choices, Client, command, Context, describe, hybrid_group (+4 more)

### Community 22 - "**Interacting with the Bot**"
Cohesion: 0.08
Nodes (23): **AMP Instance Instructions**, **Creating a Discord Bot Account**, **First Time Startup**, **Installation Methods**, Installing Python 3.11, Installing Python on Linux, Installing Python on  Windows, **Interacting with the Bot** (+15 more)

### Community 23 - "AMPTemplate"
Cohesion: 0.12
Nodes (8): AMPTemplate, AMPTemplateConsole, Sets the Permissions for Template Modules, Sends a message in a way to mimic that of in-game Chat Messages., Base Function for Broadcast Messages to AMP ADS, Base Function for AMP.addWhitelist, Base Function for AMP.getWhitelist, Base Function for AMP.removeWhitelist

### Community 24 - "._execute"
Cohesion: 0.17
Nodes (6): dump_to_json(), Adds a entry to table RegexPatterns, else Updates a matching pattern., Adds a Whitelist Reply to the DB, Deletes a Whitelist Reply from the DB, Creates a Banner Group Table with the provided `name`, Removes a Discord Message ID from a BannerGroup

### Community 25 - "DBServer"
Cohesion: 0.14
Nodes (6): DBServer, DB Server Attributes: `InstanceID: str` `InstanceName: str` `FriendlyName: str`…, Adds the provided RegexPattern ID/Name to the ServerRegexPatterns Table., Removes the provided RegexPattern ID/Name from the ServerRegexPatterns Table., Gets all Regex Patterns related to Server Returns `dict['ID': {'Name':…, Gets all Discord Role IDs gating Whitelist access for this Server.

### Community 26 - "AMP_init"
Cohesion: 0.31
Nodes (7): AMP_init(), amp_server_instance_check(), getAMPHandler(), Intializes the connection to AMP and creates AMP_Instance objects., This checks if any new instances have been created since last check. If so,…, Checks for new AMP Instances every 30 seconds.., Namespace

### Community 27 - "db_server_cog.py"
Cohesion: 0.15
Nodes (11): DB_Server, autocomplete, Choice, Client, command, Context, describe, hybrid_group (+3 more)

### Community 28 - "**Regex**"
Cohesion: 0.12
Nodes (16): ADD:, ADD:, DELETE:, DELETE:, Examples, **How Console Filtering can affect your Regex Patterns**, **How to Manage your Bot Regex Patterns**, **How to Manage your Servers Regex Patterns** (+8 more)

### Community 29 - "i18n.py"
Cohesion: 0.48
Nodes (6): get_language(), getI18nHandler(), # NOTE: `Command._params` is a private/undocumented discord.py attribute…, retranslate_command_tree(), set_language(), t_plural()

### Community 30 - ".__init__"
Cohesion: 0.18
Nodes (6): Creates the `Gatekeeper` role, Adds us to the Membership of that Role and sets…, Sets the Permissions Nodes for AMP Gatekeeper Role, This is used to set/update the DB attributes for the AMP server, Creates a AMP User role, Sets the AMP Users Role Membership, Sets the AMP Role permission Node eg `Core.RoleManagement.DeleteRoles`

### Community 31 - "discordBot"
Cohesion: 0.15
Nodes (9): discordBot, Client, Embed, Message, Deletes `message`. Deleting another user's message requires the…, Edits `message`; `content` must be convertible to `str`., Sends `content` to `parameter`. Only one of `file`/`files` may be given, not…, The name and ID of a custom emoji can be found with the client by prefixing… (+1 more)

### Community 33 - "Python 3.13 Bootstrap Compatibility Fixes"
Cohesion: 0.06
Nodes (43): AMP_Handler.py (AMPHandler singleton), AMP.py (AMPInstance base class), AMP Integration Layer, amp_permissions.py (AMP permission profiles), AMP Bot Role/Permission Bootstrap Ordering Bug, Core.UserManagement.ViewUserInfo Self-Check Crash Fix, Database Layer, DB.py (Database wrapper) (+35 more)

### Community 34 - "Edited_DB_Banner"
Cohesion: 0.05
Nodes (53): AMPHandler, Creates a list of Instance Names/DisplayName or Friendly Name., Builds a tokens-like namespace from environment variables (optionally loaded…, Validates the .env/environment-variable settings and 2FA., AMPs class Loader for specific server types., perms_whitelist_only(), Minimal permission profile for the MAIN AMP instance (ID 0) Gatekeeper role,…, DBBanner (+45 more)

### Community 37 - ".getStatus"
Cohesion: 0.17
Nodes (6): Use this to check if the AMP Dedicated Server(ADS) is running, NOT THE AMP…, AMP Instance(s) Thread Manager, AMP Instance Status Information, Returns `(TPS: str, Users: tuple(str, str), CPU: str, Memory: tuple(str, str),…, Server is Online and Proper AMP Permissions. So we check TPS/State to make sure…, Returns Number of Online Players over Player Limit. `eg 2/10`

### Community 38 - ".check_GatekeeperRole_Permissions"
Cohesion: 0.17
Nodes (6): - Will check `Gatekeeper Role` for `Permission Nodes` when we have `Super…, Gets AMP user info. if IdOnly is True; returns AMP User ID only!, Returns AMP Users ID Only., Gets full permission spec for Role (returns permission nodes), Gets a List of all Roles, if set_roleID is true; it checks for `Gatekeeper` and…, Sets `self.AMP_BotRoleID` and `self.super_AdminID` (if they exist)

### Community 39 - "cog_minecraft.py"
Cohesion: 0.20
Nodes (8): Minecraft, Bot, listener, Member, User, Called when a User updates any part of their Discord Profile; this provides…, Called when a member is kicked or leaves the Server/Guild. Returns a…, setup()

### Community 40 - "**Enabling Custom Permissons**"
Cohesion: 0.17
Nodes (11): Adding Permissions:, Adding Wildcard Permissions:, Discord Console Channel Permissions:, **Enabling Custom Permissons**, **Features**, **Full Permission Node List**, **Permissions**, Removing Permissions: (+3 more)

### Community 41 - ".role_parse"
Cohesion: 0.22
Nodes (6): Member, Role, Adds `role` to `user`., Removes `role` from `user`., This is the bot utils Role Parse Function It handles finding the specificed…, This is the bot utils User Parse Function It handles finding the specificed…

### Community 42 - "**Whitelist**"
Cohesion: 0.20
Nodes (9): **Account Linking**, Behavior:, **Discord Role Whitelist Sync**, Player-facing:, Setup:, Staff Setup:, **Troubleshooting**, **Whitelist** (+1 more)

### Community 44 - "utils.py"
Cohesion: 0.31
Nodes (9): async_rolecheck(), autocomplete_servers(), autocomplete_servers_public(), get_botPerms(), Choice, Interaction, Autocomplete for AMP Instance Names, Autocomplete for AMP Instance Names (+1 more)

### Community 45 - "AMP_Console.py"
Cohesion: 0.22
Nodes (7): AMPConsole, ConsoleEntry, Controls what will be sent to the Discord Console Channel via AMP Console.…, This will handle all player chat messages from AMP to Discord. Format's Server…, This starts our console threads..., This handles AMP Console Updates; turns them into bite size messages and sends…, TypedDict

### Community 46 - "Context"
Cohesion: 0.25
Nodes (5): Context, Fills whitelist reply placeholders: `<user>`, `<server>`, `<guild>`., This is the botUtils Server Parse function. **Note** Use context.guild.id…, Verifies if the AMP Server exists and if its Instance is running and its ADS is…, Use to get a Users Role Prefix for displaying.

### Community 47 - "botPerms"
Cohesion: 0.36
Nodes (4): botPerms, Validates the contents of bot_perms.json., Checks a Users for a DB Role then checks for that Role inside of bot_perms.py,…, Pre build my Permissions Role Name List

### Community 48 - "Cleanup-Roadmap"
Cohesion: 0.29
Nodes (6): 1. Toter Code 🟢 ✅ Erledigt, 2. Docstring-/Kommentar-Bloat 🟢 ✅ Erledigt, 3. Datei-Duplikate / veraltete Docs 🟡 ✅ Erledigt, 4. Backlog — bewusst zurückgestellt 🔴, Cleanup-Roadmap, Vorschlag für die Reihenfolge, wenn's losgeht

### Community 51 - "DBHandler"
Cohesion: 0.50
Nodes (3): DBHandler, getDBHandler(), This sets the DB Server Console_Flag, Console_Filtered and…

### Community 52 - "amp_projectzomboid.py"
Cohesion: 0.28
Nodes (4): AMPProjectzomboid, AMPProjectzomboidConsole, Sends a customized message via servermsg through the console., Used to Send a Broadcast Message to the Server

### Community 53 - "amp_sevendays.py"
Cohesion: 0.28
Nodes (4): AMPSevendays, AMPSevendaysConsole, Sends a customized message via say through the console., Used to Send a Broadcast Message to the Server

### Community 54 - "amp_terraria.py"
Cohesion: 0.28
Nodes (4): AMPTerraria, AMPTerrariaConsole, Sends a customized message via say through the console., Used to Send a Broadcast Message to the Server

### Community 55 - ".channel_parse"
Cohesion: 0.33
Nodes (4): datetime, TextChannel, This will be used to access channel history up to 100. Simple scraper with…, This is the bot utils Channel Parse Function It handles finding the specificed…

### Community 56 - "amp_factorio.py"
Cohesion: 0.32
Nodes (3): AMPFactorio, AMPFactorioConsole, Sets the Permissions for Factorio Modules

### Community 57 - "**Banner**"
Cohesion: 0.33
Nodes (5): **Banner**, **Editing your Server Banner/Embed**, **How to Display your Banners**, Using the Custom Banner Image Editor:, **What is a Banner?**

### Community 58 - "Production deployment log (Hetzner, `fullsendhub.de`)"
Cohesion: 0.33
Nodes (5): Current status (updated 2026-08-09), Fixes made getting from "won't even `pip install`" to a working AMP bootstrap, Open issues / pick up here next time, Production deployment log (Hetzner, `fullsendhub.de`), Resolved this session (2026-08-09)

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

### Community 77 - "permissions_cog.py"
Cohesion: 0.25
Nodes (6): Permissions, Choice, Client, Interaction, This is for roles inside of the bot_perms file. Returns a list of all the…, setup()

## Knowledge Gaps
- **100 isolated node(s):** `**Using your commands!**`, `<u>Bot Commands</u>:`, `<u>Bot Utils Commands</u>:`, `<u>Bot Cog Commands</u>:`, `<u>Bot Banner_Settings Commands</u>:` (+95 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **23 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `AMPInstance` connect `AMPInstance` to `Banner`, `utils_ui.py`, `WhitelistSync`, `Whitelist`, `.Login`, `AMPMinecraft`, `Banner_Generator`, `botUtils`, `botEmbeds`, `AMP_init`, `.__init__`, `Edited_DB_Banner`, `.getStatus`, `.check_GatekeeperRole_Permissions`, `AMP_Console.py`, `Context`, `.CurrentSessionHasPermission`, `.ConsoleMessage_withUpdate`, `.RestartInstance`?**
  _High betweenness centrality (0.248) - this node is a cross-community bridge._
- **Why does `role_check()` connect `role_check` to `discordBot.py`, `Banner`, `WhitelistSync`, `Whitelist`, `Cog_Template`, `utils.py`, `DB_User`, `Regex`, `db_server_cog.py`?**
  _High betweenness centrality (0.138) - this node is a cross-community bridge._
- **Why does `Database` connect `Database` to `DBConfig`, `.AddServerWhitelistRole`, `DB.py`, `.RemoveServerWhitelistRole`, `._fetchone`, `DBUser`, `._execute`, `DBServer`?**
  _High betweenness centrality (0.064) - this node is a cross-community bridge._
- **Are the 13 inferred relationships involving `AMPInstance` (e.g. with `AMP_Tasks` and `AMPHandler`) actually correct?**
  _`AMPInstance` has 13 INFERRED edges - model-reasoned connections that need verification._
- **Are the 14 inferred relationships involving `Edited_DB_Banner` (e.g. with `DBBanner` and `Cancel_Banner_Button`) actually correct?**
  _`Edited_DB_Banner` has 14 INFERRED edges - model-reasoned connections that need verification._
- **What connects `**Using your commands!**`, `<u>Bot Commands</u>:`, `<u>Bot Utils Commands</u>:` to the rest of the system?**
  _100 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `discordBot.py` be split into smaller, more focused modules?**
  _Cohesion score 0.09725490196078432 - nodes in this community are weakly interconnected._