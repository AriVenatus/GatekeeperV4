# **Gatekeeper**


Gatekeeper is a Discord bot for managing CubeCoders AMP game servers — console/chat bridging, Discord Role \<-> Whitelist syncing, self-service account linking, custom banners, and more, all without leaving Discord.

This fork (GatekeeperV4) actively builds on k8thekat's original GatekeeperV2 and Leon Breidenbach's GatekeeperV3, adding new features, performance work, security hardening, and English/German localization. See [Why use this fork?](#why-use-this-fork) below for the full list.

Need Support or have questions about this fork? Join the **[FullSendHub Discord](https://discord.gg/mPJZ4NU44)**.


## **Why use this fork?**
___
This is a fork of [Leon Breidenbach's GatekeeperV3](https://github.com/leonbreidenbach-pc/GatekeeperV3), which is itself a fork of the original [k8thekat/GatekeeperV2](https://github.com/k8thekat/GatekeeperV2). Compared to the original GatekeeperV2:

**From Leon's GatekeeperV3:**
- More defensive handling of malformed/unexpected AMP API responses in `AMP.py` (`getStatus`, `getUserList`, `getActiveUsers`).
- A `threading.Event`-based shutdown mechanism for the AMP background thread, with try/except wrapping so one bad polling iteration doesn't kill the thread, and daemon-thread behavior so the process doesn't hang on exit.
- Per-server/per-group error handling in the banner auto-update loop, so one broken server, guild, or channel no longer takes down the whole banner refresh.

**New in this fork (v3.1):**
- Banner timestamps now support a configurable timezone and 12h/24h format (`/bot banner_settings timezone`/`timeformat`), with a consistent, timezone-aware "Edited at ..." shown on both banner types.
- Added Discord Role \<-> Whitelist syncing (`/whitelist_sync`, `/server settings whitelist_role_add`) and self-service account linking (`/link minecraft`/`/link steam` with a Confirm/Deny preview), so players gain/lose Whitelist access automatically as their Discord Role changes, without Staff needing to run `/user add` for them. See [Whitelist Sync Commands](/docs/COMMANDS.md#whitelist-sync-commands) and [Link Commands](/docs/COMMANDS.md#link-commands).
- Merged `/user lookup` into `/user info` (now `/user info discord`/`minecraft`/`steam`) for one unified way to look up a Database entry.
- Added English/German localization with a global, admin-controlled language switch (`/bot language`) — the whole command surface and all bot-authored messages retranslate live, no restart required.
- **Performance**: AMP API calls reuse a shared `requests.Session()` instead of a fresh connection per call, and `start.py` skips redundant `pip install` runs on startup — cutting typical bot startup time from ~90 seconds down to roughly 5-10 seconds.
- **Security**: closed a SQL-injection gap in `DB.py`'s dynamic `UPDATE` statements, markdown-escaped external display names before they're shown in embeds, patched `requests`/`urllib3`, added a minimal-permission `-whitelist-only` launch mode, and a loud startup warning whenever `-super`/`-dev` leaves the bot's AMP account as Super Admin.

See [changelog.md](/docs/changelog.md) for the full version history.


## **Features**
___
- Self-managing AMP permissions with minimal setup — see the [Permissions Guide](/docs/PERMISSIONS.md) for advanced setups.
- Control AMP Servers via Discord slash commands, with Console/Chat/Event channel bridging.
- SQL Database-backed User and Server storage.
- Full AMP Template support with constant updates — see [AMP Instance Instructions](/docs/INSTALL.md#amp-instance-instructions).
- Cross-platform: Windows or Linux — see [Running as a Service](/docs/INSTALL.md#using-gatekeeper-as-a-service).
- Extensible via custom Cogs / your own AMP Dedicated Server module.
- Autocomplete for Discord Channels, Roles, and AMP Servers.
- Custom Banner displays (Discord Embeds or Images) with AMP Server info.
- Regex-based filtering of Console output and Events (Disconnects, Deaths, Kills, ...) to Discord channels.
- Discord Role \<-> Whitelist syncing plus self-service account linking — see [Whitelist Sync Commands](/docs/COMMANDS.md#whitelist-sync-commands) and [Link Commands](/docs/COMMANDS.md#link-commands).
- English/German localization with a global, live-switchable language setting — adding another language is easy: mostly a translation file plus two one-line registrations, no deeper code changes. See [LOCALIZATION.md](/docs/LOCALIZATION.md) for the step-by-step guide.

## **Getting Started**
___
Requirements, Python setup, Discord Bot account creation, installation (Manual or AMP Instance), first-time configuration walkthrough, Launch Args, and running Gatekeeper as a systemd service have all moved to **[INSTALL.md](/docs/INSTALL.md)**.

___
### **Credits**
"**Thank You**" to [k8thekat](https://github.com/k8thekat), the original creator of [GatekeeperV2](https://github.com/k8thekat/GatekeeperV2), and to [Leon Breidenbach](https://github.com/leonbreidenbach-pc), whose [GatekeeperV3](https://github.com/leonbreidenbach-pc/GatekeeperV3) fork this project builds on. See [Why use this fork?](#why-use-this-fork) for what this fork adds on top of their work.

From k8thekat, the original author: "**Thank You**" to everyone at CubeCoders Discord Server, especially *IceofWrath, Mike, Greelan* and everyone else in their discord.

From k8thekat, the original author: "**Thank You**" to everyone over at Discord.py Discord Server, especially *SolsticeShard and sgtlaggy* for all the silly questions I kept asking about embed's and Hybrid messages!
