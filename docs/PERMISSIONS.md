# **Permissions**

This section is for those wanting to really "Fine Tune" your permissions. 

## **Features**
___
- Gatekeeper has the ability to set permissions *per command* or *globally* across a command tree.
    - *See below for [How to use!](#using-your-permission-nodes)*
- You can make as many "Roles" as you want and can assign them to Discord users however you want! 
    - The only restriction is that **ANY ROLE** you give a Discord User via the `/user role (user, role)` command **MUST EXIST** in the `bot_perms` file or it won't work.
        - **TIP**: `role` autocompletes with the Role names currently defined in your `bot_perms.json`.

## **Enabling Custom Permissons**
- After configuring your `bot_perms.json` file, simply restart Gatekeeper and use the command `/bot permissions` and select `Custom`
    - Gatekeeper will verify the file, reporting any issues it finds and exiting. You must restart the bot after fixing your permissions file.
        - **TIP**: I strongly recommend keeping a backup of the file when making changes. 
        - **WARNING**: **Gatekeeper will NOT START** if you are set to `Custom` and the file is invalid.
    - **TIP** - The bot will still respect those with __Discord Administrator Permission__ privelage under `Role -> Advanced Permissions`.
        - **WARNING**: The bot will no longer respect the role set by `/bot moderator`, it is completely bypassed.
    - **NOTE**: `/bot moderator`, `/bot permissions`, and `/bot language` always require real __Discord Administrator Permission__, regardless of `Custom`/`Default` mode. Unlike every other node in the list below, granting `bot.moderator`/`bot.permissions`/`bot.language` to a non-Administrator Role in `bot_perms.json` will **not** let that Role use those commands — they change bot-wide behavior for every user at once, so they're intentionally not delegable via Custom Permissions.

### **Setting up your Permissions File**
- Each role must have a `name`, `discord_role_id`, `prefix` and `permissions`. 
    - **ATTENTION**: All these values must exist! `discord_role_id` and `prefix` are the only ones that can be set to `"None"`
    - **TIP**: You can get a Discord role's ID via the `/bot utils roleid (role)` command.
    ```python
    "name": "Admin", #This field can be set to any name/phrase you want to set as a "role" 
    "discord_role_id": "1004516841932214373", #This must be the numeric value you get from Copy Role ID in developer mode.
    "prefix": "Admin", #This will be displayed when a User with this role talks On Discord and is sent to the Dedicated Server.
    "permissions": [
        "bot.utils.status",
        "bot.utils.ping",
        "bot.utils.sync"]
    ```

### **Using your Permission Nodes**
___

### Adding Permissions:
- Simply place the permission node inside the Roles permissions list.
    - **REMINDER**: You want to place the permission node inside the `opening "[" and closing "]"`, each entry needs `quotes("double")` and between each entry needs to be a `comma(,)`. *(eg `"-bot.utils.status", "-bot.utils.ping"`)*
    
    ```python
    {"name": "Admin",
    "discord_role_id": "1004516841932214373", #Must be a Discord Role ID.
    "prefix":
    "permissions": 
        ["bot.utils.status", #This is ALLOWING the command '/bot utils status'
        "bot.utils.ping",
        "bot.utils.sync"]} 
    ```
### Removing Permissions:
- Simply place the permission node inside the Roles permissions list with a `-` in front of it. *(eg. `-bot.utils.status`)*
    - **REMINDER**: You want to place the permission node inside the `opening "[" and closing "]"`, each entry needs `quotes("double")` and between each entry needs to be a `comma(,)`. *(eg `"-bot.utils.status", "-bot.utils.ping"`)*
    ```python
    {"name": "Admin",
    "discord_role_id": "1004516841932214373",
    "permissions": 
        ["-bot.utils.status", #This is REMOVING the permissions node bot.utils.status preventing the role from using the command '/bot utils status'
        "bot.utils.ping",
        "bot.utils.restart"]} 
    ```

### Adding Wildcard Permissions:
- Adding the permission node `server.*` would give the Role full access to any `/server` command.
    - *Location of the wildcard does not matter.*
- **TIP**: You can __REMOVE__ permission for a specific command simply by adding a `-` before the permission node *(eg. `-server.status`)* 
    - The user would still have access to all other `/server` commands __EXCEPT__ `/server status`.
    ```python
    {"name": "Admin",
    "discord_role_id": "1004516841932214373",
    "permissions": 
        ["bot.*", #This is my wildcard, allowing me to use any command that starts with '/bot'
        "-bot.utils.status"]} #This is REMOVING the permission to use the command '/bot utils status' even though the wildcard exists.
    ```

___
### Server Status Button Permissions:
- For a User to interact with the buttons from the `/server status` command. They need the respective permission nodes.
    - **Start Button** requires `server.start`
    - **Stop Button** requires `server.stop`
    - **Restart Button** requires `server.restart`
    - **Kill Button** requires `server.kill`
___
### Discord Console Channel Permissions:
- For a user to interact/send console commands via the Discord Console Channel. They need `server.console.interact`
    - See [Commands-Interacting via Discord Channels](/docs/COMMANDS.md#interacting-with-your-server-via-discord-channels)
___
#### **Full Permission Node List**
- This list may be missing permissions. You have been warned, check your logger for permission nodes.
- **NOTE**: A node is always the command's own Discord path with spaces replaced by dots (eg. `/server settings donator` -> `server.settings.donator`). Wildcards (`x.*`) only ever match the **first** dot-segment.
___
```py
whitelist_buttons #For Approve, Deny Buttons

staff #Changes layout of Server Autocomplete to show IDs

bot.*
bot.settings
bot.moderator
bot.permissions
bot.language #Administrator-only, see note above -- not delegable via Custom Permissions

bot.bannergroup.*
bot.bannergroup.rename
bot.bannergroup.remove
bot.bannergroup.add
bot.bannergroup.delete_group
bot.bannergroup.info
bot.bannergroup.create_group

bot.utils.*
bot.utils.message_timeout
bot.utils.roleid
bot.utils.ping
bot.utils.channelid
bot.utils.uuid
bot.utils.userid
bot.utils.status
bot.utils.sync
bot.utils.clear
bot.utils.restart
bot.utils.disconnect

bot.regex_pattern.*
bot.regex_pattern.update
bot.regex_pattern.add
bot.regex_pattern.list
bot.regex_pattern.delete

bot.banner_settings.*
bot.banner_settings.type
bot.banner_settings.auto_update
bot.banner_settings.auto_remove
bot.banner_settings.timeformat
bot.banner_settings.timezone

bot.cog.*
bot.cog.reload
bot.cog.load
bot.cog.unload

server.*
server.broadcast
server.restart
server.update
server.start
server.stop
server.users
server.status
server.backup
server.kill
server.msg

server.regex.*
server.regex.add
server.regex.list
server.regex.delete

server.banner.*
server.banner.settings
server.banner.background

server.console.*
server.console.interact #Not a slash command; sends commands via the Discord Console Channel
server.console.filter
server.console.channel

server.settings.*
server.settings.role
server.settings.host
server.settings.avatar
server.settings.prefix
server.settings.donator #Donator-only vs everyone gate for /whitelist_request on this Server
server.settings.info
server.settings.hidden
server.settings.displayname
server.settings.whitelist
server.settings.whitelist_role_add
server.settings.whitelist_role_remove
server.settings.whitelist_role_list
server.settings.donator_role_add #Which Discord Role(s) auto-whitelist as a Donator on this Server -- any one is enough
server.settings.donator_role_remove
server.settings.donator_role_list
server.settings.whitelist_auto #Per-Server: auto-whitelist /whitelist_request or require Staff approval
server.settings.whitelist_wait_time

server.chat.*
server.chat.channel

server.event.*
server.event.channel

server.whitelist.* #`/server whitelist add|remove` -- manually add/remove one IGN on one Server's whitelist
                    #(`server.settings.whitelist` above is the separate open/closed/hidden flag command)
server.whitelist.add
server.whitelist.remove

bot.whitelist.* #`/bot whitelist request_channel` -- the one remaining bot-wide setting for the
                 #`/whitelist_request` self-service flow; `auto`/`wait_time` are now per-Server
                 #(see `server.settings.whitelist_auto`/`whitelist_wait_time` above), and
                 #`donator_bypass` is gone (superseded by `server.settings.donator_role_add` --
                 #Donator Roles auto-whitelist via Whitelist Sync, they never reach this flow)
bot.whitelist.request_channel

bot.whitelist_reply.*
bot.whitelist_reply.list
bot.whitelist_reply.add
bot.whitelist_reply.remove

whitelist_sync.*
whitelist_sync.enabled
whitelist_sync.interval

whitelist_request

link #No permission node, same as whitelist_request; any Guild Member can use `/link` to self-service link their own account.

dbserver.*
dbserver.cleanup
dbserver.change_instance_id

user.*
user.role #The `/user role (user, role)` command referenced above under "Features"
user.update
user.info.discord #NOTE: `/user info` has 3 separate leaf permission nodes, not one `user.info`
user.info.minecraft
user.info.steam
user.add
```