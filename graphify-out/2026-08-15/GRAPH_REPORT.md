# Graph Report - GatekeeperV3.1  (2026-08-15)

## Corpus Check
- 77 files · ~336,234 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1369 nodes · 2680 edges · 92 communities (63 shown, 29 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 80 edges (avg confidence: 0.5)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `e751bb01`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- I18nHandler
- role_check
- Banner
- LinkConfirmView
- WhitelistSync
- DB.py
- Whitelist
- .Login
- Cog_Template
- Handler
- AMPMinecraft
- amp_generic.py
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
- Codebase Audit — 2026-08-14
- DB_Server
- **Regex**
- Edited_DB_Banner
- ._bootstrap_permissions
- amp_starbound.py
- banner_file_handler
- Python 3.13 Bootstrap Compatibility Fixes
- amp_csgo.py
- DBConfig
- AMP.py
- .getStatus
- .check_GatekeeperRole_Permissions
- Minecraft
- **Enabling Custom Permissons**
- copy_to_select.py
- **Whitelist**
- .RemoveServerDonatorRole
- async_rolecheck
- AMPConsole
- DiscordPlumbingMixin
- GameAPIMixin
- AMPHandler
- AMPInitError
- cog_factorio.py
- AMP_Tasks
- AMPProjectzomboid
- AMPSevendays
- AMPTerraria
- ServerButton
- AMPFactorio
- **Banner**
- fulfill_whitelist_request
- **Adding a Language**
- .__init__
- cog_csgo.py
- Button
- .RemoveServerWhitelistRole
- Deny_Whitelist_Button
- Setup
- .AddServerDonatorRole
- cog_sevendays.py
- .ConsoleMessage_withUpdate
- cog_terraria.py
- .user_role
- GatekeeperV4
- changelog.md
- .CurrentSessionHasPermission
- cog_starbound.py
- generic.py
- .__init__
- cog_projectzomboid.py
- cog_valheim.py
- amp_permissions.py
- .__init__
- .removeWhitelist
- amp_valheim.py
- DBServer
- DBUser
- start.py (Setup / startup sequence)
- Bug Report Issue Template
- listener
- Member
- User

## God Nodes (most connected - your core abstractions)
1. `AMPInstance` - 110 edges
2. `role_check()` - 100 edges
3. `Database` - 55 edges
4. `DB_Update` - 41 edges
5. `Edited_DB_Banner` - 40 edges
6. `AMP_Server` - 36 edges
7. `Banner` - 34 edges
8. `Bot` - 30 edges
9. `WhitelistSync` - 30 edges
10. `AMPHandler` - 29 edges

## Surprising Connections (you probably didn't know these)
- `Copy_To_Select` --uses--> `DBServer`  [INFERRED]
  utils_dev/banner_editor/ui/copy_to_select.py → core/DB.py
- `AMP_Tasks` --uses--> `AMPInstance`  [INFERRED]
  cogs/amp_tasks_cog.py → core/AMP.py
- `Banner` --uses--> `Banner_Editor_View`  [INFERRED]
  cogs/banner_cog.py → utils_dev/banner_editor/ui/view.py
- `WhitelistSync` --uses--> `Gatekeeper`  [INFERRED]
  cogs/whitelist_sync_cog.py → core/discordBot.py
- `Cancel_Banner_Button` --uses--> `AMPInstance`  [INFERRED]
  utils_dev/banner_editor/ui/button.py → core/AMP.py

## Import Cycles
- 3-file cycle: `utils_dev/banner_editor/ui/button.py -> utils_dev/banner_editor/ui/modal.py -> utils_dev/banner_editor/ui/view.py -> utils_dev/banner_editor/ui/button.py`
- 4-file cycle: `utils_dev/banner_editor/ui/button.py -> utils_dev/banner_editor/ui/modal.py -> utils_dev/banner_editor/ui/textinput.py -> utils_dev/banner_editor/ui/view.py -> utils_dev/banner_editor/ui/button.py`

## Hyperedges (group relationships)
- **Python 3.13 / Hetzner Deployment Compatibility Fix Batch** — claude_python313_compatibility_fixes, requirements_dependencies, claude_logger, claude_amp_instance, claude_amp_permissions [EXTRACTED 1.00]

## Communities (92 total, 29 thin omitted)

### Community 0 - "I18nHandler"
Cohesion: 0.24
Nodes (3): I18nHandler, Re-derives each command/param/choice's locale key from its live…, Loads locale files and resolves translation keys for the currently active…

### Community 1 - "role_check"
Cohesion: 0.06
Nodes (36): AMP_Server, autocomplete, Choice, choices, Client, command, Context, group (+28 more)

### Community 2 - "Banner"
Cohesion: 0.08
Nodes (24): Banner, autocomplete, Choice, choices, command, Context, Guild, GuildChannel (+16 more)

### Community 3 - "LinkConfirmView"
Cohesion: 0.14
Nodes (12): apply_link(), Confirm_Link_Button, Deny_Link_Button, LinkConfirmView, DBUser, Interaction, Generic confirmation View shown after a `/link` lookup, so the user can confirm…, Gets (or creates) the DBUser row for the Discord account confirming a `/link`. (+4 more)

### Community 4 - "WhitelistSync"
Cohesion: 0.08
Nodes (28): before_loop, autocomplete, Choice, choices, command, Context, DBUser, describe (+20 more)

### Community 5 - "DB.py"
Cohesion: 0.18
Nodes (11): # NOTE: this parameter must NOT be named `AMP` -- that would shadow the module-…, Request the AMP handler background loops to stop., request_shutdown(), get_language(), getI18nHandler(), # NOTE: `Command._params` is a private/undocumented discord.py attribute…, retranslate_command_tree(), set_language() (+3 more)

### Community 6 - "Whitelist"
Cohesion: 0.06
Nodes (27): autocomplete, Choice, choices, command, Context, describe, GuildChannel, hybrid_command (+19 more)

### Community 7 - ".Login"
Cohesion: 0.08
Nodes (15): This is the main API Call function, This gets all Instances on AMP., Basic Console Message, Restarts AMP Instance, Returns a List of connected users., This is used to change an Instance's Friendly Name and or Description. Retains…, Test AMP API calls with this function, Ends specified User Session (+7 more)

### Community 8 - "Cog_Template"
Cohesion: 0.08
Nodes (24): guild_check(), Use this before any commands to limit it to a certain guild usage., guilds, Reaction, Cog_Template, autocomplete, Client, command (+16 more)

### Community 9 - "Handler"
Cohesion: 0.25
Nodes (5): Handler, Client, This is the Basic Module Loader for AMP to Discord Integration/Interactions, This loads all the required Cogs/Scripts for each unique AMPInstance.Module type, This will load all Cogs inside of the cogs folder.

### Community 10 - "AMPMinecraft"
Cohesion: 0.09
Nodes (14): DBUser, AMPMinecraft, AMPMinecraftConsole, Gets a Users Player Head via UUID, Bans a User from the Server, Sends a customized message via tellraw through the console., Handles returning customized discord message data for Minecraft Servers only., This is Minecraft Specific API calls for AMP (+6 more)

### Community 12 - "DB_Update"
Cohesion: 0.10
Nodes (4): DB_Update, SQLITE does not support dropping UNIQUE constraint, SQLITE does not support adding UNIQUE constraint, Seeds every Server row's new Auto_Whitelist/Whitelist_Wait_Time from the old…

### Community 13 - "Banner_Generator"
Cohesion: 0.14
Nodes (10): ImageFont, Banner_Generator, Image, Custom Banner Generator for Gatekeeper., Blurs the Background Image with GaussianBlur, Custom Word Wrap. Returns a `list` when `truncate` is `False`, Adjusted the RGB values for Player Limit Display., Rounds the corners of the Background Image. (+2 more)

### Community 14 - "AMPInstance"
Cohesion: 0.09
Nodes (12): AMPInstance, Base Function for AMP.addWhitelist, Base Function for AMP.getWhitelist, Base Function for AMP.name_Conversion, Base Function for AMP.resolve_canonical_IGN, Base Function for Discord Chat Messages to AMP ADS, Base Function for customized discord messages (Primarily Minecraft), Base Function for Broadcast Messages to AMP ADS (+4 more)

### Community 15 - "Database"
Cohesion: 0.11
Nodes (12): Database, Gets all Servers current in the DB, Returns all ServerIDs that the provided Discord Role ID gates Whitelist access…, Returns all ServerIDs that the provided Discord Role ID gates Donator access…, Gets all Regex Patterns from the RegexPatterns Table. Returns…, Gets all Whitelist Replies currently in the DB, Gets a Specific Banner Groups full information return…, Gets all BannerGroups Names/IDs returns `Banners[entry["ID"]] = entry["name"]` (+4 more)

### Community 16 - "._fetchone"
Cohesion: 0.09
Nodes (12): Finds a User using either DiscordID, DiscordName, MC_InGameName, MC_UUID, or…, Removes a entry RegexPatterns Table using either its `Name` or `ID`, Returns RegexPatterns Table Returns `row['ID'] = {'Name': row['Name'], 'Type':…, Update a Regex Pattern in the RegexPatterns Table using either its `Name` or…, Selects a Banner Group Table matching the `name` provided., Update a Banner Group, Add a Server to an existing Banner Group., Removes a Server from an existing Banner Group. (+4 more)

### Community 17 - "DB_User"
Cohesion: 0.20
Nodes (11): DB_User, Client, command, Context, describe, group, hybrid_group, listener (+3 more)

### Community 18 - "botUtils"
Cohesion: 0.17
Nodes (7): botUtils, Client, Context, Gatekeeper Utility Class, Formats the message for Discord `Bold = \\x01, \\x02` `Italic = \\x03, \\x04`…, Fills whitelist reply placeholders: `<user>`, `<server>`, `<guild>`., This checks the DB Server objects Avatar_url and returns the proper object…

### Community 19 - "botEmbeds"
Cohesion: 0.13
Nodes (15): botEmbeds, Context, DBServer, DBUser, Guild, User, Gatekeeper Embeds/Banners, This is the Server Status Embed Message (+7 more)

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
Cohesion: 0.11
Nodes (9): DBServer, Adds the provided RegexPattern ID/Name to the ServerRegexPatterns Table., Removes the provided RegexPattern ID/Name from the ServerRegexPatterns Table., Gets all Regex Patterns related to Server Returns `dict['ID': {'Name':…, Adds a Discord Role ID to this Server's Whitelist Role gate list. Any one of…, Gets all Discord Role IDs gating Whitelist access for this Server., Gets all Discord Role IDs gating Donator access for this Server., Adds a Discord Role to a Server's Whitelist Role gate list. (+1 more)

### Community 26 - "Codebase Audit — 2026-08-14"
Cohesion: 0.17
Nodes (11): Codebase Audit — 2026-08-14, Conflicts / Notes Between Subagents, Critical Issues (ranked by severity), Delete/remove, Doc fixes, Flag, don't auto-delete (needs judgment), Post-refactor code review (2026-08-15), Quick Wins (safe, low-risk cleanup) (+3 more)

### Community 27 - "DB_Server"
Cohesion: 0.16
Nodes (11): DB_Server, autocomplete, Choice, Client, command, Context, describe, hybrid_group (+3 more)

### Community 28 - "**Regex**"
Cohesion: 0.12
Nodes (16): ADD:, ADD:, DELETE:, DELETE:, Examples, **How Console Filtering can affect your Regex Patterns**, **How to Manage your Bot Regex Patterns**, **How to Manage your Servers Regex Patterns** (+8 more)

### Community 29 - "Edited_DB_Banner"
Cohesion: 0.12
Nodes (32): DBBanner, banner_field_label(), Modal, TextInput, Edited_DB_Banner, DB_Banner for Banner Editor All `attrs` inside this class must have a `_`…, Cancel_Banner_Button, Copy_To_All_Banner_Button (+24 more)

### Community 30 - "._bootstrap_permissions"
Cohesion: 0.20
Nodes (6): Creates a AMP User role, Sets the AMP Users Role Membership, Sets the AMP Role permission Node eg `Core.RoleManagement.DeleteRoles`, Runs the Gatekeeper role/permission bootstrap state machine -- for the main AMP…, Creates the `Gatekeeper` role, Adds us to the Membership of that Role and sets…, Sets the Permissions Nodes for AMP Gatekeeper Role

### Community 32 - "banner_file_handler"
Cohesion: 0.15
Nodes (7): banner_file_handler(), Image, Interaction, This is called when a button is interacted with., This is called when a button is interacted with., This is called when a button is interacted with., Interaction

### Community 33 - "Python 3.13 Bootstrap Compatibility Fixes"
Cohesion: 0.06
Nodes (43): AMP_Handler.py (AMPHandler singleton), AMP.py (AMPInstance base class), AMP Integration Layer, amp_permissions.py (AMP permission profiles), AMP Bot Role/Permission Bootstrap Ordering Bug, Core.UserManagement.ViewUserInfo Self-Check Crash Fix, Database Layer, DB.py (Database wrapper) (+35 more)

### Community 35 - "DBConfig"
Cohesion: 0.16
Nodes (3): DBConfig, DBHandler, getDBHandler()

### Community 37 - ".getStatus"
Cohesion: 0.17
Nodes (6): Use this to check if the AMP Dedicated Server(ADS) is running, NOT THE AMP…, AMP Instance(s) Thread Manager, AMP Instance Status Information, Returns `(TPS: str, Users: tuple(str, str), CPU: str, Memory: tuple(str, str),…, Server is Online and Proper AMP Permissions. So we check TPS/State to make sure…, Returns Number of Online Players over Player Limit. `eg 2/10`

### Community 38 - ".check_GatekeeperRole_Permissions"
Cohesion: 0.17
Nodes (6): - Will check `Gatekeeper Role` for `Permission Nodes` when we have `Super…, Looks up an AMP user by `name` (an AMP username, via `Core/GetAMPUserInfo`).…, Returns AMP Users ID Only., Gets full permission spec for Role (returns permission nodes), Gets a List of all Roles, if set_roleID is true; it checks for `Gatekeeper` and…, Sets `self.AMP_BotRoleID` and `self.super_AdminID` (if they exist)

### Community 39 - "Minecraft"
Cohesion: 0.20
Nodes (8): listener, Member, Minecraft, Bot, Called when a User updates any part of their Discord Profile; this provides…, Called when a member is kicked or leaves the Server/Guild. Returns a…, setup(), User

### Community 40 - "**Enabling Custom Permissons**"
Cohesion: 0.17
Nodes (11): Adding Permissions:, Adding Wildcard Permissions:, Discord Console Channel Permissions:, **Enabling Custom Permissons**, **Features**, **Full Permission Node List**, **Permissions**, Removing Permissions: (+3 more)

### Community 41 - "copy_to_select.py"
Cohesion: 0.27
Nodes (5): Copy_To_Select, Interaction, Select, Copy_To_View, View

### Community 42 - "**Whitelist**"
Cohesion: 0.15
Nodes (12): **Account Linking**, Behavior:, Behavior:, **Discord Role Whitelist Sync**, **Donator Roles**, Player-facing:, Setup:, Setup: (+4 more)

### Community 44 - "async_rolecheck"
Cohesion: 0.10
Nodes (24): autocomplete_servers(), autocomplete_servers_public(), Choice, Interaction, Autocomplete for AMP Instance Names, Autocomplete for AMP Instance Names, async_rolecheck(), botPerms (+16 more)

### Community 45 - "AMPConsole"
Cohesion: 0.23
Nodes (7): AMPConsole, ConsoleEntry, Controls what will be sent to the Discord Console Channel via AMP Console.…, This will handle all player chat messages from AMP to Discord. Format's Server…, This starts our console threads..., This handles AMP Console Updates; turns them into bite size messages and sends…, TypedDict

### Community 46 - "DiscordPlumbingMixin"
Cohesion: 0.11
Nodes (14): DiscordPlumbingMixin, Context, Member, Role, TextChannel, This is the bot utils User Parse Function It handles finding the specificed…, This is the botUtils Server Parse function. **Note** Use context.guild.id…, This will get the `Parent` command and then add a `Sub` command to said… (+6 more)

### Community 47 - "GameAPIMixin"
Cohesion: 0.14
Nodes (8): GameAPIMixin, Mojang/Steam profile lookup helpers, mixed into `botUtils` (see…, Converts an IGN to a UUID/Name Table `returns 'uuid'` else returns `None`,…, Resolves a Minecraft in-game name into profile info via the official Mojang…, Converts a Steam Name to a Steam ID returns `STEAM_0:0:2806383`, Returns `True` if a Steam Web API Key has been set via GATEKEEPER_STEAM_API_KEY, Parses a raw SteamID64, a full profile URL (`/profiles/<id>` or…, Resolves a SteamID64, profile URL, or vanity name into Steam profile info via…

### Community 48 - "AMPHandler"
Cohesion: 0.16
Nodes (12): AMP_init(), amp_server_instance_check(), AMPHandler, getAMPHandler(), Intializes the connection to AMP and creates AMP_Instance objects., Creates a list of Instance Names/DisplayName or Friendly Name., Builds a tokens-like namespace from environment variables (optionally loaded…, Validates the .env/environment-variable settings and 2FA. (+4 more)

### Community 49 - "AMPInitError"
Cohesion: 0.29
Nodes (5): AMPInitError, Sets the AMP API request headers, optionally attaches a default `AMPConsole`,…, Raised when `AMPInstance.__init__` cannot finish bringing up an instance (bad…, This is used to set/update the DB attributes for the AMP server, Exception

### Community 50 - "cog_factorio.py"
Cohesion: 0.50
Nodes (3): Factorio, Bot, setup()

### Community 51 - "AMP_Tasks"
Cohesion: 0.14
Nodes (12): AMP_Tasks, Client, listener, loop, Message, TextChannel, Find an existing webhook named `webhook_name` on `channel`, move it to…, This handles AMP Console messages and sends them to discord. (+4 more)

### Community 52 - "AMPProjectzomboid"
Cohesion: 0.29
Nodes (4): AMPProjectzomboid, AMPProjectzomboidConsole, Sends a customized message via servermsg through the console., Used to Send a Broadcast Message to the Server

### Community 53 - "AMPSevendays"
Cohesion: 0.29
Nodes (4): AMPSevendays, AMPSevendaysConsole, Sends a customized message via say through the console., Used to Send a Broadcast Message to the Server

### Community 54 - "AMPTerraria"
Cohesion: 0.29
Nodes (4): AMPTerraria, AMPTerrariaConsole, Sends a customized message via say through the console., Used to Send a Broadcast Message to the Server

### Community 55 - "ServerButton"
Cohesion: 0.17
Nodes (7): KillButton, Custom Start Button for when Servers are Offline., This is called when a button is interacted with., RestartButton, ServerButton, StartButton, StopButton

### Community 56 - "AMPFactorio"
Cohesion: 0.33
Nodes (3): AMPFactorio, AMPFactorioConsole, Sets the Permissions for Factorio Modules

### Community 57 - "**Banner**"
Cohesion: 0.33
Nodes (5): **Banner**, **Editing your Server Banner/Embed**, **How to Display your Banners**, Using the Custom Banner Image Editor:, **What is a Banner?**

### Community 58 - "fulfill_whitelist_request"
Cohesion: 0.17
Nodes (8): t(), Accept_Whitelist_Button, fulfill_whitelist_request(), Context, Domain logic run once a Whitelist request has been Accepted: syncs the server's…, Accepts the Whitelist Request, This Removes all the Buttons after timeout has expired, StatusView

### Community 59 - "**Adding a Language**"
Cohesion: 0.14
Nodes (12): Open issues / pick up here next time, Production deployment log (Hetzner, `fullsendhub.de`), **Adding a Language**, Bugs surfaced while translating, Coverage — what is and isn't translated, Full text-quality audit (2026-08-09), German naturalness pass (2026-08-09), How it works (+4 more)

### Community 60 - ".__init__"
Cohesion: 0.38
Nodes (5): Client, Message, View, Whitelist Request View, Whitelist_view

### Community 61 - "cog_csgo.py"
Cohesion: 0.50
Nodes (3): Csgo, Bot, setup()

### Community 62 - "Button"
Cohesion: 0.22
Nodes (8): Approve_Button, Cancel_Button, DB_Instance_ID_Swap, Button, DBServer, DB Instance ID Swap View, Deletes `to_db_server`'s DB row and reassigns its InstanceID onto…, swap_db_instance_ids()

### Community 70 - ".user_role"
Cohesion: 0.14
Nodes (11): Permissions, autocomplete, Choice, Client, Context, hybrid_command, Interaction, Member (+3 more)

### Community 75 - "cog_starbound.py"
Cohesion: 0.50
Nodes (3): Bot, setup(), Starbound

### Community 79 - "cog_valheim.py"
Cohesion: 0.50
Nodes (3): Bot, setup(), Valheim

## Knowledge Gaps
- **109 isolated node(s):** `**What is a Banner?**`, `Using the Custom Banner Image Editor:`, `**How to Display your Banners**`, `**Features**`, `**Setting up your Permissions File**` (+104 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **29 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `AMPInstance` connect `AMPInstance` to `Banner`, `WhitelistSync`, `DB.py`, `Whitelist`, `.Login`, `Banner_Generator`, `botUtils`, `botEmbeds`, `Edited_DB_Banner`, `._bootstrap_permissions`, `AMP.py`, `.getStatus`, `.check_GatekeeperRole_Permissions`, `AMPConsole`, `DiscordPlumbingMixin`, `AMPHandler`, `AMPInitError`, `AMP_Tasks`, `fulfill_whitelist_request`, `.__init__`, `.ConsoleMessage_withUpdate`, `.CurrentSessionHasPermission`, `.__init__`, `.removeWhitelist`?**
  _High betweenness centrality (0.200) - this node is a cross-community bridge._
- **Why does `role_check()` connect `role_check` to `Banner`, `WhitelistSync`, `DB.py`, `.user_role`, `Whitelist`, `Cog_Template`, `async_rolecheck`, `DB_User`, `Regex`, `DB_Server`?**
  _High betweenness centrality (0.129) - this node is a cross-community bridge._
- **Why does `Database` connect `Database` to `.AddServerDonatorRole`, `DBConfig`, `DB.py`, `AMPMinecraft`, `.RemoveServerDonatorRole`, `DB_Update`, `._fetchone`, `._execute`, `DBServer`, `.RemoveServerWhitelistRole`?**
  _High betweenness centrality (0.073) - this node is a cross-community bridge._
- **Are the 13 inferred relationships involving `AMPInstance` (e.g. with `AMP_Tasks` and `AMPHandler`) actually correct?**
  _`AMPInstance` has 13 INFERRED edges - model-reasoned connections that need verification._
- **Are the 6 inferred relationships involving `DB_Update` (e.g. with `Database` and `DBBanner`) actually correct?**
  _`DB_Update` has 6 INFERRED edges - model-reasoned connections that need verification._
- **Are the 14 inferred relationships involving `Edited_DB_Banner` (e.g. with `DBBanner` and `Cancel_Banner_Button`) actually correct?**
  _`Edited_DB_Banner` has 14 INFERRED edges - model-reasoned connections that need verification._
- **What connects `**What is a Banner?**`, `Using the Custom Banner Image Editor:`, `**How to Display your Banners**` to the rest of the system?**
  _109 weakly-connected nodes found - possible documentation gaps or missing edges._