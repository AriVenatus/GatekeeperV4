__**Update 4.11.0**__
- Renamed this fork from `GatekeeperV3.1` to `GatekeeperV4` (README, `CLAUDE.md`, `pyproject.toml`, startup log lines, and every live GitHub URL — repo link, avatar images, docs links) to reflect the scope of everything below.
- Repo restructure:
    - Moved all root Python modules (`AMP.py`, `AMP_Handler.py`, `DB.py`, `discordBot.py`, `i18n.py`, `loader.py`, `logger.py`, `utils*.py`, etc.) into a new `core/` package; `start.py` stays at the repo root as the entry point.
    - Moved all user-facing docs (`BANNER.md`, `COMMANDS.md`, `PERMISSIONS.md`, `REGEX.md`, `WHITELIST.md`, `changelog.md`, etc.) into `docs/`, plus new guides `docs/INSTALL.md` (setup, split out of `README.md`) and `docs/LOCALIZATION.md` (how to add a language).
    - Renamed `modules/Counter-Strike_Go` -> `modules/CounterStrikeGo` and lowercased `AMP_server_cog.py`/`AMP_tasks_cog.py`/`DB_server_cog.py`/`DB_user_cog.py`/`Permissions_cog.py` for naming consistency with the rest of `cogs/`.
- Removed `tokens.py`/`tokenstemplate.py`/`tokens_dev.py` support entirely — a `.env` file or real environment variables (`.env.template`) are now the only way to configure secrets.
- Fixed a locale-file lookup bug introduced by the `core/` move: `i18n.py`'s locales path resolved relative to its own file location, which broke once it moved into `core/` (was silently falling back to raw i18n keys like `messages.bot.utils.sync.local_success` instead of translated text).
- Rewrote `README.md`: dropped "MAINTENANCE MODE ONLY" (this fork is under active development again), new intro, explicit credits to k8thekat (original author) and Leon Breidenbach, trimmed "Features" to flat one-liners, moved all setup/installation content to `docs/INSTALL.md`.
- Documented the correct `.env` placement for a systemd deployment (outside the repo checkout, wired via `EnvironmentFile=`, not inside `WorkingDirectory`) and added the missing `EnvironmentFile=` line to the example service unit in `docs/INSTALL.md`.
- Removed the duplicate `COPYING` (kept `LICENSE`) and the stale `discord-role-synced-whitelist.md` proposal doc; added `.DS_Store` to `.gitignore`.

__**Update 4.10.0**__
- Added English/German localization: a global (not per-user), admin-controlled language switch via `/bot language`, which retranslates the entire command tree (descriptions, parameters, choices) and every bot-authored message live, no restart required.
- Split `/user info` into `/user info discord`/`/user info minecraft`/`/user info steam` subcommands (was one command with an `identifier_type` Choice) — Discord slash commands can't conditionally show/hide a parameter based on another parameter's value, so the old version showed both `identifier` and `user` regardless of which type was picked.
- Escaped external/API-sourced display names (Steam personaname, Minecraft IGN) before interpolating them into `/link` confirmation embeds, so a name containing `_`/`*`/etc. can no longer bleed into the surrounding markdown formatting.
- Fixed a few bugs surfaced while translating: a `context.sned(...)` typo, `/server status` referencing an already-None-checked variable, and `ServerButton`'s AMP permission-node lookup being derived from its (now-translatable) display label instead of an explicit `action` param.
- Full text-quality audit of both locale files (grammar/accuracy) plus a German-naturalness pass (idiomatic phrasing over literal translation, a hardcoded English `' and '` literal that was bleeding into German sentences, a missing `need_selection` guard on `/bot bannergroup remove`, and a few broken sentence-composition bugs where interpolating one translated fragment into another produced disagreeing grammar).

__**Update 4.9.0**__
# First production deployment (Hetzner) and everything it surfaced
- Python 3.13 compatibility: bumped `certifi`/`aiohttp`/`multidict` and their new transitive deps in `requirements.txt`, added a shim for `haggis.logs.add_logging_level()`'s use of a `logging` API CPython 3.13 removed, and added `audioop-lts` for `discord.py`'s voice-import crash.
- Matched AMP's exact expected login request shape (found by diffing against the AMP web client): `Content-Type: application/x-www-form-urlencoded; charset=UTF-8` instead of `application/json`, added `X-Requested-With: XMLHttpRequest`, always send the `SESSIONID` field, and added an `Authorization: Bearer <SessionID>` header to every authenticated call.
- Fixed the real root cause of a Super-Admin bootstrap crash: `setup_AMPbotrole()` joined the bot's own account to the new `Gatekeeper` role *before* permissions were set on it, which (deny-beats-allow) cancelled out Super Admin mid-setup; reordered to set permissions first.
- Fixed a crash when `check_GatekeeperRole_Permissions()` referenced `self.Port` on the main AMP instance (which has no `Port` attribute), and a crash when a per-instance delegate session's `Core/GetAMPUserInfo` self-check gets rejected (now guarded and non-fatal for non-main instances).
- Reconciled `perms_super()`/`perms_whitelist_only()` against a live `Core/GetPermissionsSpec` dump: dropped `LocalFileBackup.*` and 3 more stale/renamed exclusion nodes, excluded several wildcard-granted-but-unused nodes.
- Hardened secrets/permissions handling: added a `.env`/environment-variable fallback for secrets, a loud startup warning when `-super`/`-dev` leaves the bot's AMP account as Super Admin, and a new `perms_whitelist_only()` profile + `-whitelist-only` flag for a minimal-permission whitelist-sync-only deployment mode.
- Closed a latent SQL-injection-via-column-name gap in `DB.py`'s dynamic `UPDATE` statement construction (added a column allowlist check).
- Performance: AMP API calls now reuse a single shared `requests.Session()` instead of a fresh connection per call; `start.py` skips re-running `pip install` on startup when `requirements.txt` is unchanged.
- Added raw-response logging on AMP login/permission-set failures, which is what made several of the fixes above possible instead of guessing blind.

__**Update 4.8.0**__
- Added a Discord Role \<-> Whitelist Sync system (new `whitelist_sync_cog.py`):
    - `/server settings whitelist_role_add/remove/list` lets Staff configure one or more Discord Roles per Server that grant Whitelist access; the same Role can gate multiple Servers.
    - `/whitelist_sync enabled` turns the sync on/off bot-wide; `/whitelist_sync interval` controls a periodic reconciliation pass that catches any Role/Whitelist drift missed while the bot was offline.
    - Members gaining a configured Role are automatically Whitelisted (if they've linked a game account); losing the Role, or leaving the Guild, removes them again.
    - Added the `ServerWhitelistRoles` table and `Whitelist_Role_Sync`/`Whitelist_Role_Sync_Interval` settings (DB version 3.0 -> 3.1).
- Added self-service account linking via `/link minecraft (ign)` and `/link steam (steam)`:
    - Both resolve the account (Mojang API for Minecraft, official Steam Web API for Steam) and show a Confirm/Deny preview (skin face / Steam avatar, name, ID) before saving anything, so Staff no longer need to run `/user add` on a player's behalf.
    - `/link steam` accepts a vanity name, full profile URL, or raw SteamID64; requires a Steam Web API Key (`SteamAPIKey` in `tokens.py`) to be configured.
    - `/link show` displays your currently linked accounts; `/link remove` clears one, refusing to claim success if there was nothing to remove, and proactively removing you from any role-synced Minecraft Whitelist before clearing the identity that was gating it.
- Merged `/user lookup` into `/user info`: it now takes an `identifier_type` (Discord/Minecraft/Steam) plus either the native Discord Member picker or a free-text `identifier`, so Staff can find a Database entry by Discord Member, Minecraft IGN/UUID, or SteamID from one command.
- Updated `COMMANDS.md`, `PERMISSIONS.md`, `README.md`, and wrote `WHITELIST.md` to document all of the above.

__**Update 4.7.5**__
- Ported the banner timestamp timezone/time-format feature from upstream:
    - Added `/bot banner_settings timezone` (with IANA timezone autocomplete) and `/bot banner_settings timeformat` (12h/24h) commands.
    - Added `Banner_Timezone` (default `UTC`) and `Banner_Use_12Hour` (default `True`) settings.
    - Fixed the "Edited at ..." banner timestamp being missing on embed-based banners and hardcoded to German/UTC on image-based banners; both now show a consistent, timezone-aware timestamp.
- Fixed `pyproject.toml` failing to parse due to a missing closing quote in the `authors` table.
- Updated `pyproject.toml` to reflect this fork: renamed package to `GatekeeperV3.1`, added Ari as an author, and pointed `project.urls` at this repo.
- Repointed hardcoded avatar image and `PERMISSIONS.md` links (`discordBot.py` and the `modules/*` server type files) from `k8thekat/GatekeeperV2` to this fork's repo.

__**Update 4.7.4**__
# Hotfix for issue #102
- Added a TypedDict for Console entries.
- Fixed logic in time handling for AMP 2.6.0.0
- Added attributes to DBServer to fix linter in AMP_Console.py.

__**Update**__
- stealth update; no version change with this.
- Fixed minor issues inside `banner_cog`
- Fixed issue with older verions of python trying to run GK (should support 3.8++ now.)

__**Update 4.5.3**__
- Minor fixes to logger statements on `AMP_tasks_cog`, `regex_cog`, `cog_template` and `Permissions_cog`.
- updated `banner_cog`
    - Updated naming scheme for logging statements.
    - Added `autocomplete_bannergroups_servers` for `/bot bannergroup remove`
        - Updated autocomplete for `/bot bannergroup remove`
    - Added `@property` for `self._client.Message_Timeout` to `_Message_Timeout`
    - Fixed edge case inside `autocomplete_bannergroups_channels` that could fail on `empty` or `None` returns.
- updated `DB`
    - Added `@property` to help linter with list returns.
    - Added `return types` to many methods.
    - Added `Get_all_Servers_for_Bannergroup` to be used in `autocomplete_bannergroups_servers`
    - Cleaned up methods and updated return statements.
- updated `utils`
    - Added `traceback` prints to `sub_command_handler` and `sub_group_command_handler`
- updated `loader.py`
    - updated naming convetion for `module_name`
    - Fixed logic for checking dependencies of a cog.

__**Update 4.5.1 and 4.5.2**__
- Hotfix
    - Fixed typo in `DB_Update.py` table creation code.
    - Removed typo in `/bot banner_settings auto_update`
    - Updated versions.

__**Update 4.5**__
- changes to `AMP_server_cog.py`
    - relocated and renamed methods to better facilate redability
    - relocated banner related functions to `banner_cog`
    - fixed edge case where `stopping` an Instance just before Banner Generator fires would cause the loop to crash.

- changes to `whitelist_cog.py`
    - added validation of `Whitelist_request_channel` when enabling auto-whitelist. Should warn if channel doesn't exists and or not set.
    - moved all whitelist specific settings commands under `/bot`
    - changed `/whitelist reply` to `/bot whitelist_reply`.
    - clarified doc strings on some commands.
    - combined `/server whitelist true` and `/server whitelist false` into `/server settings whitelist`
        - You can set Whitelist to True or False in one command.
        - Added `Disabled` to hide `Whitelist Open/Closed` on Banners.

- added extensive documentation to `amp_template.py`
    - added required methods and notes to indicate this.

- Updated `loader.py`
- Added the ability to support `.disabled` to the end of a cog file and have it be ignored.
    - Revamped the entire `cog_auto_loader` to better handle cogs that rely on other cogs.
    - Cogs will now require a `Dependencies` var at the top of their files and will use a list to define any required cogs they need to load. If the cog has no dependency set it to `None`
        - See `cog_template.py` for examples if needed.

- Created `REGEX.md`
    - Here you will find useful information regarding Console Filtering and how to impliment Regex filtering.

- Updated `Commands.md`
    - Fixed spelling mistakes and cleaned up formatting of commands.
    - Removed documenation for commands that no longer exist; updated documenation for commands that have changed.

- Updated `AMP.py`
    - relocated `getWhitelist` to `amp_minecraft.py`, there is a generic method inside of `AMP.py` for linters.
    - Changed logic inside of `Login()` to better handle SessionIDs when an Instance is offline.

- Updated `AMP_Console.py`
    - Fixed logic inside of `console_filter()` when handling Event type filtering.
    - Added two `dev` print statements.
    - Added an `_ADScheck()` when console parsing fails to find any entries.

- Updated `AMP_Handler.py`
    - Changed layout of server names when using autocompletes
        - Removed displaying of `TargetName` when equal to `None`.

- Updated `utils.py`
    - Added `sub_group_command_handler()` for adding commands to existing groups when accross seperate files.
    - fixed edge case with `__remove_commands()` on first time startup failing to find command group.
    - Updated `autocomplete_servers` to better handle partial matches of server names when typing to narrow results.

- Updated `utils_embeds.py`
    - Added `InstanceID` field to embed footers.

  
- Updated `DB.py`
    - Moved `DB_Update` to its on file, whew.. that file was getting big.
    - Added multiple functions for `BannerGroups` to help interacting with them.
    - Added `ServerID` parameter to `GetServer` to help searching.

- Update `discordBot.py`
    - Fixed typo in `/bot utils sync` command.

__**HotFix 4.4.9**__
- changed default `DBBanner` blur amount to `0`
- fixed issue in `on_command_error`
- Updated `banner_creator.py`
    - fixed issue with `banner_creator.py` raising an issue about `_font_Whitelist_y` not existing. Thanks @IceOfWraith#6057
    - changed resolution of Banners in `banner_creator.py` from `1800x600` to `800x270`
        - changed `self._font_default_size` from 25 to 12
    - fixed issue with `word_wrap` not handling text without a blank space. Too long of Instance Names will show like this `InstaceN...` or similar depending on length.
- fixed issue with `/server banner settings` Modal/View

__**Update 4.4.8**__
- added `Donator` role bypass for Auto whitelist wait time.
    - added `/whitelist donator_bypass` command.

__**Update 4.4.7**__
- fixed issue with `whitelist_request_handler()` when attempting to use a non unique IGN. Thanks @Snaggolicious#4987
- split `AMP.py` class's into seperate files for future ease of usage/editing.
    - Updated any related `AMP.py` calls and any type checking related to `AMPInstance, AMPHandler` and `AMPConsole`
- fixed logic on `/bot permissions` command
- updated info on `/bot utils clear` command
- cleaned up formatting of `bot_utils_sync` method
- updated the layout of `bot_settings_embed` inside `utils_embeds.py` which will provide a cleaner display for `/bot settings` command
- fixed issue with donator flag not updating on banners. Thanks @FeminalPanda#7879
    - updated `commands.md` to reflect the changes.
- began making `sub_group_handler` for adding commands to an existing command group.
- fixed issue with `server banners` not resetting when the discord channel was deleted. Thanks @hotdamnitsaaron#1501
- fixed issue with `whitelisting`, was failing with duplicate IGNs. Thanks @Snaggolicious#4987
- added `intents.jpg` to be used with `Readme.md`
- Servers that are `Hidden` via `/server settings hidden` will be omitted when a `NON STAFF` member uses an autocomplete that provides server names.
- added a `dev` print to `AMP` Login's if they fail.
- fixed typo in `/bot permissions` when attempting to sync commands to the current guild. 
- changed formatting of `dev` prints inside of `loader.py`
- added fix for `dict` issues inside of `AMP_server_cog.py` for method `_banner_generator`. 
    - Edge case when generating banners and creating an new instance at the same time.
- changed formatting of `dev` prints on multiple files for better readability.
- Updated `Display Banners` --
    - fixed issue with `Banners` not displaying `Donator Only` when the flag was set.
    - split `Donator Only` and `Whitelist Open/Closed` into seperate methods and placed `Donator Only` below Whitelist.
    - changed layout of banners slightly; moved the setting `AMP Description` below the Server Name to be used as a possible version indicator/similar.
        - changed `AMP Description` to no longer word wrap to next line; it will truncate when it hits the Shadow box on the right of Banners.(Sorry)
    - fixed issue with `host` color not updating on banners, DB was using `Host` instead of `host`. Thanks @hotdamnitsaaron#1501
    - added `Donator color` to `/server banner settings`.

__**Update 4.4.6**__
- changes to `AMP_server_cog.py`
    - Added except `discord.errors.NotFound`
    - Removed all `server_display_update.stop()` calls to prevent the task loop from exiting. Thanks @HunterAP and @FeminalPanda#7879
- changes to `discordbot.py`
    - Fixed typo in `/bot utils clear` reply message.
- changes to `banner_creator.py`
    - Fixed typo in `_validate_image()`
- changes to `whitelist_cog.py`
    - Changed message for reply regarding `Auto-Whitelist` being `False` when a user uses `/whitelist request` to better inform players/staff.
    - Fixed typo in `whitelist request message` that displays the Buttons/View
- changes to `amp_minecraft.py`
    - Changed logic in `check_whitelist()` method for validation.
- changes to `AMP.py`
    - Added `type hinting` to `getWhitelist()` method
    - Added `Exception` raising when a Server fails to be added to the `DB`
- changes to `utils_embeds.py`
    - Changed layout of `server_status_embed()` embed fields for clarity on Instances vs Applications. Thanks @FeminalPanda#7879
    - Changed layout of `server_display_embed()` embed fields for clarity on Instances vs Applications. Thanks @FeminalPanda#7879
- changes to `DB.py`
    - Updated to `2.7`
    - Fixed typo in `server_regex_pattern_table_creation` SQL statement; this is addressed when updating DB to `v2.7`

__**Update 4.4.5**__
- Fixed issue with `/bot utils clear` failing if you do not provide an `amount` parameter.
    - Added `Default channel` if not provided to the channel the command was run in and `type` check the `all` parameter
- Updated `Permissions.md` with all new Permission Nodes.
- Updated `AMP_server_cog.py`
    - Added `Error handler` for `_embed_generator()` when the Bot User is missing Discord Permissions.
    - Added `Error handler` for `_banner_generator()` when the Bot User is missing Discord Permissions.
    - Fixed issue with `amp_server_display` not respecting the `Hidden` attr of an AMP Server.
- Updated `whitelist_cog.py`
    - Fixed issue with `/server whitelist add` and `/server whitelist remove`. Thanks @Dann
        - Added `Whitelist check` back to both methods.
            - Currently there is an issue with the AMP API; unable to resolve at this time. See https://github.com/CubeCoders/AMP/issues/806
- Updated `AMP.py` / `amp_minecraft.py`
    - Changed parameters for `AMP` object `check_whitelist`, `addWhitelist` and `removeWhitelist`
        - Fixed issue with `logger.dev()` statement.
- Updated `AMP_tasks_cog.py`
    - Changed logic for when a In-Game message comes through to use the users Avatar first instead of using the Servers avatar Icon.
- Updated `start.py`
    - Added someo development args for handling tokens.

__**Update 4.4.4**__
- Fixed issue with `async_rolecheck()` failing if you had the `Moderator` role set by the Bot but nothing higher.
- Removed un-used imports

__**Update 4.4.3**__
- Implemented a Hotfix for `cogs` failing to load and retrying to load the `cog`
    - Added `failed_cog_load_list` and will retry failed to load `cogs`

__**Update 4.4.2**__
- Fixed issue with `DBConfig()` object handling causing issues with `GetSetting()` not returning proper values
    - Pointed all class Objects to reference `DB.DBConfig`

__**Update 4.4.1**__
- Fixed issue with `-super` not being handled properly by the `DBHandler`
    - Changed logic on `line 1056`

__**Update 4.4.0**__
- Refactored `AMP Instance` Permission setup.
    - Fixed issue with `Gatekeeper` not setting up proper `AMP` permissions. 
    - Renamed the AMP bot role to `Gatekeeper`
    - Fixed individual `AMP Instance` permission issues.
    - Added `check_SessionPermissions` method for startup validation
    - Renamed `check_AMPpermissions` to `check_GatekeeperRole_Permissions`
    - Renamed `setup_AMPpermissions` to `setup_Gatekeeper_Permissions`
    - Cleaned up `dev` logger prints and naming schemes for `info` messages.
    - Added check for `-super` arg to bypass Instance permission checks.
    - Cleaned up code for `CallAPI` method inside of `AMP.py`
        - Added `Exception` clause to `CallAPI` with `Unauthorized Access`

    - Removed setting `Super Admin ID` and `Gatekeeper Role ID` from `getRoleIDs`
        - New method called `setRoleIDs` to handle setting `Role ID vars`

    - Changed `setAMPRolePermissions`
        - Now checks API call properly and prints a `critical` if failed to set.

    - Added support for `expired` Session IDs with AMP Instances preventing Gatekeeper from interacting with said Instance.

    - Refactored `Gatekeeper` AMP Instances to `DB` handling.
        - Can now handle `Duplicate Instance Names` if `Friendly Name` is set for one of the Duplicate Instance and is unique.
            - Changed how discord based `Autocompletes` for AMP Servers is handled. 
                - Added `TargetName` to `AMP` classes for helping identify similar named Instances.
                - Rebuilt `AMPHandler.get_Instance_Names()` to handle new system.
                - Rebuilt `utils.serverparse` to handle the new system.
                - Should allow for duplicate `AMP Instance Names`
                - Updated `Server List` autocompletes to handle these changes.

    - Removed `Display_Description` from `AMPInstances`
        - Now uses the description set inside of `AMP` as the description (Usually you set this when creating/Updating the Instance).

    - AMP Instance Validation can now notice and handle deleted `AMP Instances` while running.
        - Now handles sudden `starting` and `stopping` of Instances.
    
     - Moved `dev` prints to better locations inside of `AMP Console` class


- Refactored `Gatekeeper` 
    - Added support for `slash types`  method parameters. This should provide a better choice list and autocomplete.
        - Converted all cogs with `discord User`, `discord Role` and `discord Channel` command parameters to use `slash types` instead of autocompletes.
    
    - Removed all `test()` commands and development related `print` statements.
    - Fixed issue with `/bot cog unload` not unloading cogs properly.

    - Changes to `DB_server_cog.py`
        - Changed `/dbserver swap` to `/dbserver change_instance_id`
            - Updated to support new `AMP Server Autocompletes`
            - Changed to using Buttons and Views

    -Changes to `DB_user_cog`
        - Updated logic to handle new `user` parameter type.
            - Fixed logic inside of `/user update`.
                - Added `Exception` handling for failed SQLite constraints.
                - *NEW* To reset/remove a users `mc_ign` or `steamid` pass `None` in as the parameter to the command.
            - Removed `mc_uuid` parameter from `/user update`

    - Changes to `Permissions_cog.py`
        - Updated `typehinting` of class `Permissions`

    - Changes to `regex_cog.py`
        - Added `@app_commands.describe()` to all parameters of `regex_pattern_add()` to assist users.
        - Changed formatting of reply on `regex_pattern_remove()`
        - Changed formatting of reply on `regex_pattern_update()`
        - Changed formatting of reply on `regex_pattern_list()`

    - Changes to `discordBot.py`
        - Moved `db_bot_donator` and renamed to `bot_donator`
        - Moved `bot_utils_uuid` and nested under `/bot utils`
     
    - Changes to `AMP_Tasks_cog.py`
        - Updated `typehinting` of class `AMP_Tasks`

    - Changes to `loader.py`
        - Removed un-used `imports`
        - Updated `typehinting`

    - Changes to `utils_embeds.py`
        - Switched from using `custom channel/role parse` functions to using `context.guild` object respectively
        - Updated `server_info_embed()` 
            - Added `Whitelist Hidden`
            - Renamed `Server Host` to `Host`
            - Changed layout of embed
        - Updated `server_status_embed()`
            - Changed Embed `title` format
        - Updated `bot_settings_embed()`
            - Removed embed field`Whitelist_emoji_pending` and `Whitelist_emoji_done`.
            - Changed embed field `whitelist_channel` to `whitelist_request_channel`.
        - Updated `user_info_embed()`
            - Fixed issue with not displaying `In Database` if you were not in the Database.

    - Changes to `utils_ui.py`
        - Added new class `DB_Instance_ID_Swap`
            - Used with `/dbserver change_instance_id`
            - Has two Buttons `Approve` and `Cancel`

    - Changed to `utils.py`
        - Removed un-used `imports`
        - Removed un-used `prints()`
        - Changed formatting on `autocomplete_servers()`
        - Updated `typehinting` on class `discordBot()`, `botUtils()`

    - Changes to `AMP_server_cog.py`
        - Fixed an issue with `/server display` if you changed the `type` it would display both types.
        - Removed `autocomplete_message_type()` and replaced with `choices()` to prevent issues.
        - Fixed a `type` issue with commands and its `regex` commands.
        - Changed to new `AMP Server Autocompletes`
            - Updated logic for `amp_server_start()`
            - Formatted the time of `display_description` for `amp_server_backup()`

    - Changes to `banner_cog.py`
        - Removed un-used `imports`
        - Updated `typehinting` of class `Banner()`
        - Fixed typo with `self.DBConfig()`
        - Fixed edge case issue with `_validate_image()` failing if you renamed a Banner file while the bot is running.
        - Fixed offset of `Whitelist Closed` display on Banner Images.
        - Updated `vars` to reflect changes to `AMP Description`
        - Moved the methods `bot_banner()`, `bot_banner_autoupdate()` and `bot_banner_type()` to `banner_cog`
            - Renamed `/bot banner` to `/bot banner_settings` to fix issues with group commands.
    
    - Changes to `whitelist_cog.py`
        - Updated `typehinting` of class `Whitelist()`
        - Removed `events` `on_message_edit()` and `on_message()`
        - Updated logic inside of `whitelist_waitlist_handler()` for new Request style
        - *NEW* - Replaced `/whitelist channel` with `/whitelist request_channel` for displaying Whitelist Request Approve/Deny messages.
            - Players will now use a slash command to handle all whitelist requests.
            - Respect all previous whitelist settings.
            - Gives `Staff` the ability to `Approve` or `Deny`
        - Updated `DB` to match naming scheme.
        - Updated `vars` to respect new commands and removed `DB` attrs.
        - Removed `/whitelist pending emoji`
        - Removed `/whitelist done emoji`

- Updated `DB` to Version `2.6`
    - Changed `DB` value `Banner Type` from `str` to `int`
    - Changed `DB` value `Permissions` from `str` to `int`
    - Changed `DB` value `IP` to `Host`
    - Removed `Description` value from `Servers` Table.
    - Added `Unique` constrait to `Users` column `MC_IngameName`
    - Updated all `Gatekeeper` slash commands to match these changes.
    - Updated `bot settings` embed to reflect these changes.
    - Changed `GetAllServers()` to return a `dict`
    - Changed `GetServer()` to use `InstanceID` instead of `Name`
    - Removed `DBConfig` setting `Whitelist_emoji_pending` and `Whitelist_emoji_done`
    - Changed `AMP Instance` attr `IP` to `Host`
        - Updated all related attr interactions.
   
- Added Resources
    - Added `Minecraft_banner2.jpg` to our selections.

__**Hotfix Update 4.3.8**__
- Fixed Issue with `/bot permissions` failing when used prior to syncing commands.
- Refactored code inside of `discordBot.py` and `DB_user_Cog`
- Fixed `type` issue with `/server donator` command. Thanks @Dann
- Fixed `type` comparison with `/bot settings` command. Thanks @Dann
- Fixed `URL` issue with AMP Instance not displaying the proper Banner Image. Thanks @Ice
- Changed `avatar_urls` for AMP Modules to use Github.

