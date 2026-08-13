# **Commands List**
*This documentation is subject to change at any point and may not reflect recent changes*

### **Using your commands!**
- Most commands are using some form of `autocomplete` or `choices` to help users.
___
### <u>Bot Commands</u>: 
- `/bot moderator (role)` - Sets the Discord Role for Bot Moderator. 
    - **ATTENTION**: Requires Discord Administrator to use!
    - **TIP**: Please see `/bot permissions` for more control. 
- `/bot permissions (permission)` - Sets the Bot Permissions to either `Default` or `Custom`.
    - **ATTENTION**: Requires Discord Administrator to use!
    - **TIP**: Please see **[Permissions](/docs/PERMISSIONS.md)** if you want `Custom` control over command usage.
- `/bot language (language)` - Switches Gatekeeper's language (`English`/`Deutsch`) for every user, bot-wide.
    - **ATTENTION**: Requires Discord Administrator to use!
- `/bot settings` - Lists Bot settings such as channels and whitelist status.

### <u>Bot Utils Commands</u>: 
- `/bot utils ping` - Pong!
- `/bot utils disconnect` - Closes the Connection with the Bot.
- `/bot utils restart` - Restarts the Bot.
- `/bot utils status` - Replies with **AMP version** and if setup is complete, **DB version** and if setup is complete and **Displays Bot version information**.
    - **TIP**: This information is useful when reporting bugs/errors on Github!
- `/bot utils sync (local, reset)` - Sync functionality for Gatekeeper
    - `local` `(true/false)` if `True` makes the sync or reset happen to the `guild` the command is used in.
    - `reset` `(true/false)` if `True` will clear all commands from the Command Tree and then re-sync's the command tree.
- `/bot utils roleid (role)` - Returns the role ID for the selected Discord Role.
- `/bot utils channelid (channel)` - Returns the Channel ID for the selected Discord Channel
- `/bot utils userid (user)` - Returns the User ID for the selected Discord User.
- `/bot utils uuid (mc_ign)` - This will convert a Minecraft IGN to a UUID if it exists.
- `/bot utils clear (channel, amount, all)` - Delete(s) the specified amount of Messages Sent by the Bot.
    - If `all` is set to `True` this will clear ALL messages regardless of sender.
- `/bot utils message_timeout (time)` - Sets the Delete After time in seconds for ephemeral messages sent from Gatekeeper.

### <u>Bot Cog Commands</u>: 
- `/bot cog load (cog)` - Loads a specific Cog, given its dotted module path. *(eg. cog = `cogs.regex_cog`)*
- `/bot cog unload (cog)` - Unloads a specific Cog, given its Cog class name. *(eg. cog = `Regex`)* `cog` autocompletes with the currently loaded Cogs.
- `/bot cog reload` - Reloads all currently loaded Cogs.

### <u>Bot Banner_Settings Commands</u>: 
- `/bot banner_settings auto_update (flag)` - Allows the bot to automatically update the Banner Group messages.
- `/bot banner_settings type (type)` - Select which type of Banner to display via Banner Group messages.
- `/bot banner_settings auto_remove (flag)` - Toggles whether Servers are automatically removed from Banner Groups when they are removed from AMP.
- `/bot banner_settings timeformat (format)` - Sets the time format used on Banners.
- `/bot banner_settings timezone (timezone)` - Sets the timezone used for times shown on Banners.

### <u>Bot BannerGroup Commands</u>: 
- `/bot bannergroup create_group (group_name)` - Creates a new Banner Group
- `/bot bannergroup add (group_name, server, channel)` - Allows the User to add `Channel` or `Server` to a Banner Group.
- `/bot bannergroup remove (group_name, server, channel)` - Allows the User to remove a `Server` or `Channel` from a Banner Group
- `/bot bannergroup rename (group_name, new_groupname)` - Allows a User to rename the selected Banner Group.
- `/bot bannergroup info (group_name)` - Displays information pertaining to the selected Banner Group.
- `/bot bannergroup delete_group (group_name)` - Allows the User to Delete an entire Banner Group.

### <u>Bot Regex_Pattern Commands</u>:
- See [Regex How-to](/docs/REGEX.md) for full documentation.
- `/bot regex_pattern list` - Displays an Embed list of All Regex Patterns
- `/bot regex_pattern add (name, filter_type, pattern)` - Adds a Regex pattern to the Database
    - **TIP**: `pattern` is used in a re.search().
- `/bot regex_pattern delete (name)` - Remove a Regex Pattern from the Database
- `/bot regex_pattern update (name, new_name, filter_type, pattern)` - Update a Regex Patterns Name, Pattern and or Type.
    - **TIP**: `new_name` must not match the original `name`
    - `filter_type` dictates where the match will be sent. (eg. `Event` would send all matches to the `Event Channel` for said Server - See [Regex Examples](/docs/REGEX.md#examples) for examples.)

### <u>Bot Whitelist Commands</u>:
- See [Whitelist How-to](/docs/WHITELIST.md) for full documentation.
- `/bot whitelist request_channel (channel)` - Sets the Whitelist Request Channel for the Bot to send Whitelist requests for Staff approval.
    - **ATTENTION**: This is the only bot-wide Whitelist Request setting left -- whether requests are auto-approved and how long the wait time is are now set **per Server**, see [`/server settings whitelist_auto`](#amp-server-settings-commands) below.
- `/bot whitelist_reply add (message)` - Adds the message to the possibly list of replies the bot can use during Whitelist handling.
    - **TIP**: Messages support the following parameteres.
        - `<user>` - Which changes to use the message author's name inside your message.
        - `<server>` - Which returns with the provided AMP Instance Name or Display Name respectively.
        - `<guild>` - Which changes to the Discord Guild Name.
        - `<#channelid>` - Which is replaces with a channel jump_to link. Simply use `<#` and `>` wrapped around the channel's id. *(eg. `<#1234567890>`)*
            - It will create a jump_to link during usage; but it gets saved into the DB as the example.
- `/bot whitelist_reply remove (message)` - Removes the selected message from the list of replies the bot can use during Whitelist handling.
- `/bot whitelist_reply list` - Lists all the currently available replies the bot can use during Whitelist handling.

### <u>Whitelist_Request Commands</u>:
- `/whitelist_request (server, ign)` - Allows a user to request Whitelist for a specific Server.
    - **TIP**: `ign` is optional if the Discord User has done this before and or already in the Database.

### <u>Link Commands</u>:
- `/link minecraft (ign)` - Links your Discord account to a Minecraft in-game name.
    - **TIP**: Looks up the account via the official Mojang API and shows you a preview (name, UUID and skin face) with Confirm/Deny buttons before saving anything.
    - **ATTENTION**: Only you can respond to your own confirmation prompt.
- `/link steam (steam)` - Links your Discord account to a Steam account.
    - **TIP**: Accepts a vanity name, a full profile URL (`steamcommunity.com/id/...` or `/profiles/...`), or a raw SteamID64.
    - **ATTENTION**: Requires Staff to have configured a Steam Web API Key (`GATEKEEPER_STEAM_API_KEY`) first, otherwise the command will let you know it isn't set up yet.
    - Shows a preview (persona name, avatar, profile link) with Confirm/Deny buttons before saving anything, same as `/link minecraft`.
- `/link show` - Shows your currently linked Minecraft/Steam accounts.
- `/link remove (identity)` - Removes one of your linked accounts. `identity` is either `Minecraft` or `Steam`.

### <u>User/Member Group Commands</u>: 
- `/user info discord (user)` - Displays a Users Database information overview, looked up by the native Discord Member picker.
- `/user info minecraft (identifier)` - Displays a Users Database information overview, looked up by Minecraft IGN/UUID (free text) - handy when you don't know who the Discord User is yet.
- `/user info steam (identifier)` - Displays a Users Database information overview, looked up by SteamID (free text).
    - **ATTENTION**: If the matching Discord Account can no longer be resolved (they left/deleted their account), still shows their stored Database info with a note instead of failing.
- `/user add (user, mc_ign, mc_uuid, steamid)` - Adds a User to the Database with the provided arguments.
    - **ATTENTION**: `user` is the **only required paramater**. 
        - **TIP**: Supports Discord Name/ID or Discord Display Name/Nickname's.
    - `mc_ign` and `mc_uuid` are optional.
        - **TIP**: When providing `mc_ign`, the bot will fetch the `mc_uuid` and set it for you in the Database if not provided.
    - `steamid` is optional. 
        - **TIP**: If the player has already self-linked via `/link steam`, you don't need this at all - use `/user info steam` to find their account instead of entering it manually here.
- `/user update (user, mc_ign, steamid)` - Updates the Users Database information with the provided arguments.
- `/user role (user, role)` - Assigns a Custom Permissions Role (from `bot_perms.json`) to a User.
    - **TIP**: `role` autocompletes with the Role names currently defined in your `bot_perms.json`. See [Permissions](/docs/PERMISSIONS.md).

### <u>AMP Server Database Commands</u>: 
- `/dbserver cleanup` - Removes any Database Server entries that are not in your AMP Instances list.
- `/dbserver change_instance_id (from_server, to_server)` - Use this to switch an AMP instance with another AMP Instance in the Database.

### <u>AMP Server Commands</u>: 
- `/server update` - Updates the current list of AMP servers. *(This is also done every 30 seconds)*
    - **TIP**: This is used when creating a new Instance and needing to update the bots listings.
- `/server start (server)` - Starts the specified dedicated server.
    - **TIP**: `server` supports server nicknames that are set via `/server settings displayname` command.
- `/server stop (server)` - Stops the specified AMP Dedicated server.
- `/server restart (server)` - Restarts the specified AMP Dedicated server.
- `/server kill (server)` - Kills the specified AMP Dedicated server. 
- `/server msg (server, message)` - Sends a message to the console for the specified AMP Dedicated server.
- `/server broadcast (prefix, message)` - Sends a Broadcast to all AMP Servers with the specified Prefix
- `/server users (server)` - Shows a list of the currently connected Users to the Server.
- `/server status (server)`- AMP Server Status(TPS, Player Count, CPU Usage, Memory Usage and Online Players), with buttons for start, stop, kill and restart.
    - **ATTENTION**: Everyone can see the buttons, but only people with proper permission can interact with the buttons.
    - **TIP**: To interact with the buttons the user must have the respective permisisons. See [Server Status Button Permissions](/docs/PERMISSIONS.md#server-status-button-permissions).
- `/server backup (server)` - Creates a backup of the AMP Dedicated server.
    - **ATTENTION**: Set's the Title to `<user> generated backup` where `<user>` is the command users Discord Name.
        - The Description gets set to the current Date and Time in UTC

### <u>AMP Server Regex Commands</u>:
- See [Regex How-to](/docs/REGEX.md) for full documentation.
- `/server regex add (server, name)` - Adds a Regex Pattern to the Server Regex List
- `/server regex delete (server, name)` - Deletes a Regex pattern from the Server Regex List.
- `/server regex list (server)` - Displays an Embed list of all the Server Regex Patterns.

### <u>AMP Server Settings Commands</u>:
- `/server settings info (server)` - Displays information such as IP, Donator Only, Whitelist Open, Discord Role, Discord Chat/Console/Event Channels and Nicknames.
- `/server settings hidden (server, flag)` - Hides or Shows the Server from Autocomplete lists when *NON-Moderators* are using slash commands.
- `/server settings host (server, hostname)` - Sets the Host of the AMP Dedicated server in the Database.
    - **ATTENTION**: This is only used and displayed on commands such as `/server status`.
    - **TIP**: `hostname` is what you want your players to use to connect to the server!
- `/server settings role (server, role)` - Sets the role of the AMP Dedicated Server in the Database.
    - **ATTENTION**: This is the Discord Role the bot will give the User when requesting whitelist on said AMP Dedicated Server.
    - **TIP**: `role` can be a Discord Role ID or Discord Role Name.
- `/server settings whitelist_role_add (server, role)` - Adds a Discord Role that automatically grants Whitelist access to the specified Server.
    - **ATTENTION**: This is separate from `/server settings role` above; a Server can have multiple Whitelist Sync Roles, and the same Role can gate multiple Servers.
    - **TIP**: Requires `/whitelist_sync enabled True` to actually take effect. See [Whitelist Sync Commands](#whitelist-sync-commands).
- `/server settings whitelist_role_remove (server, role)` - Removes a Discord Role from a Server's Whitelist Sync gate list.
    - **TIP**: `role` autocompletes with only the Roles currently configured for the selected `server`.
- `/server settings whitelist_role_list (server)` - Lists all Discord Roles currently gating Whitelist access for the specified Server.
- `/server settings donator_role_add (server, role)` - Adds a Discord Role that automatically Whitelists a Member as a Donator on the specified Server.
    - **ATTENTION**: Works exactly like `whitelist_role_add` above (same automatic grant/revoke), just tracked as its own list. A Server can have multiple Donator Roles, and the same Role can be a Donator Role on multiple Servers -- holding just ONE of them is enough.
    - **TIP**: Requires `/whitelist_sync enabled True` to actually take effect. See [Whitelist Sync Commands](#whitelist-sync-commands).
- `/server settings donator_role_remove (server, role)` - Removes a Discord Role from a Server's Donator Role list.
    - **TIP**: `role` autocompletes with only the Donator Roles currently configured for the selected `server`.
- `/server settings donator_role_list (server)` - Lists all Discord Roles currently gating Donator access for the specified Server.
- `/server settings whitelist (server, flag)` - Sets the whitelist to `flag` for the AMP Dedicated server.
    - Using the flag `Disabled` hides the `Whitelist Open/Closed` from the Banner. 
        - Simply set the flag to `True` or `False` for the Banner to show `Whitelist Open/Closed` respectively.
    - **ATTENTION**: This is only for Whitelisting purposes with auto-whitelist. This will not prevent players from connecting if already Whitelisted.
- `/server settings whitelist_auto (server, flag)` - Allows the bot to automatically approve `/whitelist_request`s on this Server, instead of requiring Staff approval.
    - **ATTENTION**: `flag` must be *True or False*. Default is False, meaning a Staff member (Discord Admin, or `Moderator` Role or higher) must approve each request.
    - **TIP**: Members with a Donator Role (see above) skip this flow entirely and get Whitelisted automatically regardless of this setting.
- `/server settings whitelist_wait_time (server, time)` - Sets how many minutes this Server waits after a `/whitelist_request` before auto-approving it, once `whitelist_auto` is on.
    - **REMINDER**: All time values are in **Minutes**! Please keep that in mind.
    - **TIP**: Set the value to `0` to have the bot instantly whitelist users. Default value is 5 minutes.
- `/server settings prefix (server, server_prefix)` - Set a prefix to be displayed on Chat messages IN-game from other servers.
    - **ATTENTION**: Any messages from Discord to a Server will be prefixed with `[DISCORD]`, otherwise if it comes from another AMP Server it will use the server's prefix.
- `/server settings displayname (server, name)` - Sets the display name of the AMP Dedicated server in the Database.
    - **ATTENTION**: This is used and displayed on commands such as `/server status` in place of the Instance Name.
    - **TIP**: You can use the `display name` in place of any `server` paramater for commands.
- `/server settings avatar (server, url)` - Sets the Avatar Icon for the specified AMP Dedicated Server.
    - **TIP**: Supports `webp`, `jpeg`, `jpg`, `png`, or `gif` if it's animated. 
        - `url` Can be set to **None** so it displays the default/original Icon created.
- `/server settings donator (server, flag)` - Sets Donator Only Flag for the AMP Dedicated server to `True` or `False`
    - **ATTENTION**: This only gates the manual `/whitelist_request` flow -- when `True`, only Members with a Donator Role (see `donator_role_add` above) may use `/whitelist_request` on this Server. It does not affect the automatic Donator Whitelisting itself, and it doesn't prevent players already whitelisted without the rank from connecting.

### <u>AMP Server Console Commands</u>: 
- `/server console channel (server, channel)` - Sets the Discord Channel for the AMP Dedicated Server Console to output to.
    - **TIP**: You can type commands in the set channel similar to typing in AMP Console web GUI.
- `/server console filter (server, flag, filter_type)` - Set Console filtering for the AMP Dedicated server.
    - `flag` supports *True or False*. Simply enables/disabled filtering.
    - **TIP**: Setting the `filter_type` to either `whitelist` or `blacklist` can have mixed results depending on the `regex` patterns you have set.
        - See [Regex](/docs/REGEX.md#how-console-filtering-can-affect-your-regex-patterns)

### <u>AMP Server Chat Commands</u>: 
- `/server chat channel (server, channel)` - Sets the Discord Channel for the AMP Dedicated server to output its chat messages to.
    - **TIP**: Discord Users can talk back and forth to in-game users as if they were playing too!

### <u>AMP Server Event Commands</u>:
- `/server event channel (server, channel)`- Sets the Event Channel for the provided AMP Dedicated Server to output event type messages to.
    - **ATTENTION**: This is events such as join/leave and achievements. Currently experimental, some may be missed.

### <u>AMP Server Whitelist Commands</u>: 
- See [Whitelist How-to](/docs/WHITELIST.md) for full documentation.
- `/server whitelist add (server, name)` - Adds the IGN to the AMP Dedicated server whitelist.
    - `name` only supports in-game names.
- `/server whitelist remove (server, name)` - Removes the IGN from the AMP Dedicated server whitelist.
    - `name` only supports in-game names.

### <u>Whitelist Sync Commands</u>:
- `/whitelist_sync enabled (flag)` - Turns Discord Role Whitelist Syncing `ON` or `OFF` bot-wide. This same switch also controls automatic Donator Whitelisting (see `/server settings donator_role_add` above).
    - **ATTENTION**: When `True`, any Member gaining a configured Whitelist Sync or Donator Role is automatically Whitelisted on the matching Server(s); losing a Role removes them, unless they still hold another Role (Whitelist Sync or Donator, either counts) that also gates that Server. Leaving the Guild always removes them from any Server their Roles were gating.
    - **TIP**: A Member needs a linked game account first (via `/link`), otherwise the bot will DM them asking to link before it can Whitelist them.
- `/whitelist_sync interval (minutes)` - Sets how often (in minutes) the Whitelist Sync reconciliation pass runs.
    - **TIP**: This is a safety-net pass that re-checks every configured Role against the live Whitelist, catching any drift missed while the bot was offline. Default is `15` minutes.

### <u>AMP Server Banner Commands</u>:
- `/server banner settings (server)` - Prompts the Banner Editor View.
- `/server banner background (server, image)` - Select the Background Image to be used as the Banner Image for the selected AMP Server.
___

### **Interacting with your AMP Server via Discord Channels**:
- Set your Discord Channels per Server via
    - `/server console channel (server, channel)`
    - `/server chat channel (server, channel)`
    - `/server event channel (server, channel)`
- After setting your Discord Console Channel you should see console messages be displayed to the Discord Channel.
    - **TIP**: You can filter these messages. See [/server console filter (server, flag, filter_type)](/docs/COMMANDS.md#amp-server-console-commands)
        - Also take a look at [Regex Filtering](/docs/REGEX.md)
    - **TIP**: You can type commands in the set channel similar to typing in AMP Console web GUI.
        - You must prefix any command with `.`; example `./list` would pass `/list` to the Console.

- After setting your Discord Chat Channel you can talk to players inside the server via Discord. 
    - Any message you send to that set channel; goes to that specific AMP Server and is sent like an in-game Chat Message.