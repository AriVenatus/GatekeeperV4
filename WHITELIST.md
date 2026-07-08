# **Whitelist**
Welcome to Gatekeeper's Whitelist section. Gatekeeper actually has **two separate Whitelist systems** that can be used together or independently:

1. **Whitelist Requests** - a player asks for access via `/whitelist_request`, and Staff (or the bot, if Auto-Whitelist is on) approve it.
2. **Discord Role Whitelist Sync** - an admin picks a Discord Role, and the bot keeps Whitelist access in sync with who holds that Role automatically, no request needed.

Both rely on the same underlying Player Identity Database (Discord ID \<-\> Minecraft IGN/UUID \<-\> SteamID), so setting one up doesn't get in the way of the other.

- **NOTE**: This is unrelated to Console `filter_type = Whitelist`, which is a Regex Console-filtering option. See [Regex](/REGEX.md#when-server-console-filter-has-a-filter_type--whitelist) if that's what you were looking for.

## **Whitelist Requests**
___
This is the original request/approval flow - a player asks, and either Staff or the bot (after a wait time) whitelists them.

### Player-facing:
- `/whitelist_request (server, ign)` - Requests Whitelist access for a specific Server.
    - `ign` is optional if the player has already linked their Minecraft account (via `/link minecraft`) or been added to the Database before.

### Staff Setup:
- `/bot whitelist request_channel (channel)` - Sets the channel the bot posts Whitelist requests to for Staff Approval (Accept/Deny buttons).
- `/bot whitelist auto (flag)` - Turns Auto-Whitelist `ON`/`OFF`.
    - **ATTENTION**: Default is `OFF`, meaning a Staff member (Discord Admin, or `Moderator` Role or higher) must click Accept on each request.
- `/bot whitelist wait_time (time)` - When Auto-Whitelist is `ON`, how many minutes the bot waits before auto-approving a request (default `5`). Set to `0` for instant approval.
- `/bot whitelist donator_bypass (flag)` - Lets players with the `/bot donator` Role skip the wait time entirely.
- `/bot whitelist_reply add/remove/list (message)` - Manage a pool of custom messages the bot randomly picks from when it whitelists someone. See [Bot Whitelist Commands](/COMMANDS.md#bot-whitelist-commands) for the supported `<user>`/`<server>`/`<guild>`/`<#channelid>` parameters.
- `/server settings whitelist (server, flag)` - Opens (`True`), closes (`False`), or hides (`Disabled`) Whitelisting for a specific Server.
- `/server settings role (server, role)` - *(Optional)* A Discord Role the bot grants a player as a reward **after** they get Whitelisted on that Server (in either direction, requests or sync). This is separate from the Role Sync Roles below - it doesn't gate anything, it's just a badge.
- `/server whitelist add/remove (server, user)` - Manually add or remove an in-game name from a Server's Whitelist yourself, bypassing the request flow entirely.

## **Account Linking**
___
Both Whitelist systems need to know a player's in-game identity. Rather than Staff entering it manually via `/user add`, players can self-link their own account:

- `/link minecraft (ign)` - Looks up the account via the official Mojang API and shows a preview (corrected name, UUID, and skin face) with Confirm/Deny buttons before saving anything.
- `/link steam (steam)` - Accepts a vanity name, full profile URL (`steamcommunity.com/id/...` or `/profiles/...`), or raw SteamID64. Looks it up via the official Steam Web API and shows a preview (persona name, avatar, profile link) with Confirm/Deny buttons.
    - **ATTENTION**: Requires Staff to set a Steam Web API Key (`SteamAPIKey` in `tokens.py`) first - see the comment above that field in `tokenstemplate.py` for where to get a free one.
- `/link show` - Shows your own currently linked accounts.
- `/link remove (identity)` - Clears a linked account (`Minecraft` or `Steam`).
    - **TIP**: If a Role Sync Role (below) is still gating your access to a Minecraft Server, removing your Minecraft link also removes you from that Server's live Whitelist, since the bot can no longer verify who you are.

- **TIP for Staff**: Once a player has linked their own account, `/user info` (with `identifier_type` set to `Minecraft` or `Steam`) can find their Database entry without you needing to know their Discord identity first.

## **Discord Role Whitelist Sync**
___
This automates Whitelisting entirely around Discord Role membership - no request needed. A player gains the Role, they're Whitelisted; they lose it (or leave the Guild), they're removed.

### Setup:
1. Have players link their game account first via `/link minecraft` or `/link steam` (see above) - Sync can't act on a player without a linked identity, it'll just DM them asking to `/link` first.
2. Use `/server settings whitelist_role_add (server, role)` to pick which Discord Role(s) grant access to a Server.
    - **TIP**: A Server can have multiple gate Roles (any one of them is enough), and the same Role can gate multiple Servers.
    - Manage the list with `/server settings whitelist_role_remove` and `/server settings whitelist_role_list`.
3. Turn it on with `/whitelist_sync enabled true`.
4. *(Optional)* Adjust `/whitelist_sync interval (minutes)` - this controls a safety-net reconciliation pass (default `15` minutes) that re-checks every configured Role against the live Whitelist, catching anything missed while the bot was offline.

### Behavior:
- Gaining a configured Role Whitelists the player automatically, as long as they have a linked identity.
- Losing the Role, or leaving the Guild, removes them from that Server's Whitelist.
- **ATTENTION**: Today this is fully functional for **Minecraft** Servers (the only Module with real Whitelist file support). Other Server types safely no-op until their Modules add real Whitelist support - Sync won't error, it just won't have anything to actually add/remove yet.

## **Troubleshooting**
___
- **A player isn't getting auto-Whitelisted after gaining their Role**: Confirm `/whitelist_sync enabled` is `true`, that they've run `/link` for the correct game, and that the Server is running the Minecraft Module (see above).
- **A player lost access unexpectedly**: Check whether they lost a Role Sync Role, left and rejoined the Guild, or ran `/link remove`.
- **Custom Permissions**: All of the commands above respect Gatekeeper's permission system - see [Permissions](/PERMISSIONS.md) if you want finer-grained control over who can use them.
