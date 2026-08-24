# **Whitelist**
Welcome to Gatekeeper's Whitelist section. Gatekeeper actually has **two separate Whitelist systems** that can be used together or independently:

1. **Whitelist Requests** - a player asks for access via `/whitelist_request`, and Staff (or the bot, if Auto-Whitelist is on for that Server) approve it.
2. **Discord Role Whitelist Sync** - an admin picks Discord Role(s), and the bot keeps Whitelist access in sync with who holds them automatically, no request needed. **Donator Roles** (see below) are a specialized flavor of this same mechanism - one Server can have both a general Whitelist Sync Role list and a separate Donator Role list.

Both rely on the same underlying Player Identity Database (Discord ID \<-\> Minecraft IGN/UUID \<-\> SteamID), so setting one up doesn't get in the way of the other.

- **NOTE**: This is unrelated to Console `filter_type = Whitelist`, which is a Regex Console-filtering option. See [Regex](/docs/REGEX.md#when-server-console-filter-has-a-filter_type--whitelist) if that's what you were looking for.

## **Whitelist Requests**
___
This is the original request/approval flow - a player asks, and either Staff or the bot (after a wait time) whitelists them.

### Player-facing:
- `/whitelist_request (server, ign)` - Requests Whitelist access for a specific Server.
    - `ign` is optional if the player has already linked their Minecraft account (via `/link minecraft`) or been added to the Database before.

### Staff Setup:
- `/bot whitelist request_channel (channel)` - Sets the channel the bot posts Whitelist requests to for Staff Approval (Accept/Deny buttons). Bot-wide - one channel for every Server.
- `/server settings whitelist_auto (server, flag)` - Turns Auto-Whitelist `ON`/`OFF` **for that Server**.
    - **ATTENTION**: Default is `OFF`, meaning a Staff member (Discord Admin, or `Moderator` Role or higher) must click Accept on each request. Each Server has its own setting - one Server can auto-approve while another still requires Staff approval.
- `/server settings whitelist_wait_time (server, time)` - When that Server's Auto-Whitelist is `ON`, how many minutes the bot waits before auto-approving a request (default `5`). Set to `0` for instant approval.
    - **TIP**: Players with a Donator Role for that Server skip this entire flow and get Whitelisted automatically via Role Sync - see [Donator Roles](#donator-roles) below.
- `/bot whitelist_reply add/remove/list (message)` - Manage a pool of custom messages the bot randomly picks from when it whitelists someone. See [Bot Whitelist Commands](/docs/COMMANDS.md#bot-whitelist-commands) for the supported `<user>`/`<server>`/`<guild>`/`<#channelid>` parameters.
- `/server settings whitelist (server, flag)` - Opens (`True`), closes (`False`), or hides (`Disabled`) Whitelisting for a specific Server.
- `/server settings donator (server, flag)` - *(Optional)* Restricts `/whitelist_request` on that Server to players who hold one of that Server's Donator Roles. Players without one can't even submit a request there. Doesn't affect Role Sync/Donator auto-Whitelisting itself.
- `/server settings role (server, role)` - *(Optional)* A Discord Role the bot grants a player as a reward **after** they get Whitelisted on that Server (in either direction, requests or sync). This is separate from the Role Sync/Donator Roles below - it doesn't gate anything, it's just a badge.
- `/server whitelist add/remove (server, name)` - Manually add or remove an in-game name from a Server's Whitelist yourself, bypassing the request flow entirely.

## **Account Linking**
___
Both Whitelist systems need to know a player's in-game identity. Rather than Staff entering it manually via `/user add`, players can self-link their own account:

- `/link minecraft (ign)` - Looks up the account via the official Mojang API and shows a preview (corrected name, UUID, and skin face) with Confirm/Deny buttons before saving anything.
- `/link steam (steam)` - Accepts a vanity name, full profile URL (`steamcommunity.com/id/...` or `/profiles/...`), or raw SteamID64. Looks it up via the official Steam Web API and shows a preview (persona name, avatar, profile link) with Confirm/Deny buttons.
    - **ATTENTION**: Requires Staff to set a Steam Web API Key (`GATEKEEPER_STEAM_API_KEY`) first - see the comment above that field in `.env.template` for where to get a free one.
- `/link show` - Shows your own currently linked accounts.
- `/link remove (identity)` - Clears a linked account (`Minecraft` or `Steam`).
    - **TIP**: If a Role Sync Role (below) is still gating your access to a Minecraft Server, removing your Minecraft link also removes you from that Server's live Whitelist, since the bot can no longer verify who you are.

- **TIP for Staff**: Once a player has linked their own account, `/user info minecraft` or `/user info steam` can find their Database entry without you needing to know their Discord identity first.

## **Discord Role Whitelist Sync**
___
This automates Whitelisting entirely around Discord Role membership - no request needed. A player gains a configured Role, they're Whitelisted; they lose it (or leave the Guild), they're removed - **unless they still hold some other configured Role (Whitelist Sync or Donator, either counts) that also gates that same Server**, in which case they correctly stay Whitelisted.

### Setup:
1. Have players link their game account first via `/link minecraft` or `/link steam` (see above) - Sync can't act on a player without a linked identity, it silently skips them (logged, no DM sent) until they `/link`.
2. Use `/server settings whitelist_role_add (server, role)` to pick which Discord Role(s) grant access to a Server.
    - **TIP**: A Server can have multiple gate Roles (any one of them is enough), and the same Role can gate multiple Servers.
    - Manage the list with `/server settings whitelist_role_remove` and `/server settings whitelist_role_list`.
3. Turn it on with `/whitelist_sync enabled true`.
4. *(Optional)* Adjust `/whitelist_sync interval (minutes)` - this controls a safety-net reconciliation pass (default `15` minutes) that re-checks every configured Role against the live Whitelist, catching anything missed while the bot was offline.
5. *(Optional)* Set `/whitelist_sync channel (channel)` - once someone is actually Whitelisted, Gatekeeper pings them in this Channel. If it's not set, no ping happens (this only covers the success case - a player with a qualifying Role but no linked identity is never pinged, see above).

### Behavior:
- Gaining a configured Role Whitelists the player automatically, as long as they have a linked identity, and pings them in the configured notify Channel (see Setup step 5) once it's done.
- Losing the Role, or leaving the Guild, removes them from that Server's Whitelist, unless another qualifying Role (see above) keeps them eligible.
- **ATTENTION**: Today this is fully functional for **Minecraft** (IGN/UUID-based) and **ARK: Survival Evolved** (SteamID64-based, via `/link steam`) Servers - the only Modules with real Whitelist file support. See [ARK](#ark-survival-evolved) below for a caveat specific to that Module. Other Server types safely no-op until their Modules add real Whitelist support - Sync won't error, it just won't have anything to actually add/remove yet.

## **Donator Roles**
___
Donator Roles are a separate, dedicated Role list per Server that works through the exact same automatic mechanism as Whitelist Role Sync above - same instant grant/revoke, same `/whitelist_sync enabled` master switch, same linked-identity requirement, same "any one of them is enough" logic. They're tracked separately from the general Whitelist Sync Roles so you can offer Donator perks without opening up general Whitelist Sync access, and vice versa.

### Setup:
1. Use `/server settings donator_role_add (server, role)` to pick which Discord Role(s) count as Donator for a Server.
    - **TIP**: A Server can have multiple Donator Roles (any one is enough), and the same Role can be a Donator Role on multiple Servers.
    - Manage the list with `/server settings donator_role_remove` and `/server settings donator_role_list`.
2. Make sure `/whitelist_sync enabled true` is set bot-wide - this is the same switch that controls Whitelist Sync above.
3. *(Optional)* `/server settings donator (server, flag)` - if `True`, only players holding one of that Server's Donator Roles may even submit a `/whitelist_request` there at all. Donators don't need this to get Whitelisted (they're covered by the automatic Role Sync mechanism regardless), it only restricts *non*-Donators from the manual request flow on that Server.

### Behavior:
Identical to Whitelist Role Sync above - gaining a Donator Role Whitelists the player automatically (once linked); losing it removes them, unless another qualifying Role (Whitelist Sync or Donator) still gates that Server.

## **ARK: Survival Evolved**
___
ARK's Whitelist works exactly like Minecraft's everywhere above - `/whitelist_request`, `/server whitelist add/remove`, and Discord Role Whitelist Sync all work the same way. The only difference is player identity: ARK is gated by **SteamID64**, not IGN, so link via `/link steam` (see [Account Linking](#account-linking)) rather than `/link minecraft`.

- **ATTENTION**: The ARK Server itself must be started with the `-exclusivejoin` launch parameter (set once by Staff in the AMP Instance's Application Settings, under Additional command line parameters) for Whitelisting to actually restrict who can join. Without it, Gatekeeper's whitelist add/remove commands still run and update the Server's Whitelist file, they just have **no access-control effect** - anyone can join regardless of Whitelist state. Gatekeeper cannot set this flag for you.
- **⚠ Needs live verification before relying on it in production** - the underlying file path/command behavior was established from community documentation, not a live-tested AMP+ARK instance. See [CLAUDE.md](/CLAUDE.md)'s "ARK whitelist enforcement needs live verification before production use" section.

## **Troubleshooting**
___
- **A player isn't getting auto-Whitelisted after gaining their Role**: Confirm `/whitelist_sync enabled` is `true`, that they've run `/link` for the correct game, and that the Server is running the Minecraft or ARK Module (see above). This applies equally to Whitelist Sync Roles and Donator Roles.
- **A player lost access unexpectedly**: Check whether they lost their *last* qualifying Role (Whitelist Sync or Donator - losing just one of several is fine), left and rejoined the Guild, or ran `/link remove`.
- **Custom Permissions**: All of the commands above respect Gatekeeper's permission system - see [Permissions](/docs/PERMISSIONS.md) if you want finer-grained control over who can use them.
