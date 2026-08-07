# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

Gatekeeper is a Python/discord.py Discord bot that integrates with CubeCoders AMP (a game-server control panel) over AMP's JSON/POST HTTP API. It lets Discord users manage AMP-hosted game servers (console access, chat bridging, whitelist sync, banners, etc.) from Discord. This repo (`GatekeeperV3.1`, `AriVenatus/GatekeeperV3.1`) is a fork of `leonbreidenbach-pc/GatekeeperV3`, itself a fork of the original `k8thekat/GatekeeperV2` — it's in **maintenance mode**, not active feature development, aside from the specific fork deltas listed in `README.md`'s "Why use this fork?" section.

## Commands

- **Run**: `python start.py` from the repo root. Requires either `tokens.py` (copy `tokenstemplate.py` and fill it in) or a `.env`/environment variables based on `.env.template` — see `AMP_Handler.py::val_settings()`.
  - Useful flags (full list in `README.md` "Launch Args"): `-dev` (dev-mode logging, uses `tokens_dev.py` if present), `-super` (skip downgrading the bot's AMP account from Super Admin), `-whitelist-only` (restrict the bot's own AMP role to the minimum needed for whitelist sync), `-debug`, `-discord` (disable Discord connection, useful for testing AMP/DB in isolation).
  - On startup, `start.py` runs `pip install -r requirements.txt` automatically (skipped if `requirements.txt`'s hash hasn't changed since the last install — see `Setup.pip_install()`).
- **Lint**: `ruff check .` (config in `pyproject.toml` under `[tool.ruff]`; not pinned in `requirements.txt`, install separately if needed).
- **Type-check**: `pyright` (config in `pyproject.toml` under `[tool.pyright]`, basic mode).
- **Tests**: there is no test suite in this repo.

## Architecture

### Startup sequence
`start.py` (`Setup.__init__`) parses CLI args, runs the conditional `pip install`, initializes logging (`logger.py`), opens the SQLite DB (`DB.getDBHandler()`), then starts `AMP_Handler.AMP_init` in a background thread and blocks until `AMP_Handler.AMP_setup` is `True` before launching the Discord client (`discordBot.client_run`). The AMP thread keeps polling for instance changes every 30s via `AMP_Handler.amp_server_instance_check()` for the life of the process.

### AMP integration layer
- `AMP_Handler.py` — process-wide singleton (`AMP_Handler.getAMPHandler()` / global `Handler`). Loads secrets (`val_settings()`: tries `tokens.py`/`tokens_dev.py` first, falls back to env vars/`.env` via `_load_tokens_from_env()`), dynamically discovers per-game-type API modules from `modules/*/amp_*.py` (`moduleHandler()`, keyed by each module's `DisplayImageSources` list), and discovers/tracks live AMP instances as `AMP.AMPInstance` objects (`_instanceValidation()`).
- `AMP.py` — `AMPInstance` is the base wrapper around AMP's API (`CallAPI`, login/session handling). One instance represents the main AMP install (`InstanceID == 0`) and one per game server. On init it ensures the bot's own AMP account has a `Gatekeeper` role with the right permission nodes (`setup_AMPbotrole` / `setup_Gatekeeper_Permissions`), pulling the node list from `amp_permissions.py` (`perms_super()` for full access, `perms_whitelist_only()` for the minimal whitelist-sync-only footprint, selected via the `-whitelist-only` flag). `self.perms` (used to *check* current permissions) is derived from the same profile function as what's actually granted — keep these in sync if you touch either.
- `modules/<Game>/amp_<game>.py` — per-game subclasses of `AMPInstance` (e.g. `AMPMinecraft`) implementing game-specific AMP API calls (whitelist add/remove via console commands, etc.), each with its own `self.perms` permission list and `setup_Gatekeeper_Permissions()` override, independent from the main-instance profile above. `modules/Generic/` is the fallback used when no game-specific module matches.

#### `-whitelist-only` needs live verification before production use
On every startup and every 30s poll, Gatekeeper calls the AMP API `ADSModule/GetInstances` (`AMPInstance.getInstances()`) to discover instances — for both permission profiles. It's undocumented whether this endpoint requires an explicit `ADS.*` permission node, and `perms_whitelist_only()` deliberately grants none. If it turns out `GetInstances` does need one, the bot loses the ability to see any AMP instance after the first restart with `-whitelist-only`.
- **How to test**: start the bot with `-whitelist-only` using a fresh bot account that still has `Super Admins`; let it restart (this is when Super Admin gets removed and the narrowed `Gatekeeper` role/permissions get applied); check the log for `***ATTENTION*** Please ensure the permissions are set correctly, the Bot cannot find any AMP Instances at this time...`; confirm a Minecraft whitelist add/remove still works end-to-end via Discord-Role sync.
- **Expected result**: no "cannot find any AMP Instances" message, and whitelist sync still functions.
- **If it fails**: add an `ADS.*` (or a narrower `ADS.InstanceManagement.*` read-only) node to `perms_whitelist_only()` in `amp_permissions.py` and re-test.

### Discord bot layer
- `discordBot.py` — the `discord.py` `commands.Bot` subclass (`Gatekeeper`). `setup_hook()` delegates to `loader.Handler`.
- `loader.py` — dynamically loads two kinds of extensions at startup: (1) `module_auto_loader()` loads `modules/<Game>/cog_<game>.py` files whose `DisplayImageSources` match a currently-connected AMP instance (plus `modules/Generic/generic.py` always); (2) `cog_auto_loader()` loads every file in `cogs/` as a discord.py extension, resolving load order via each cog's module-level `Dependencies = [...]` list (cogs with unmet dependencies are retried until the list is empty). `Permissions_cog.py` is excluded from auto-load and loaded on-demand instead.
- `cogs/*.py` — the core (non-game-specific) command surface: `AMP_server_cog`, `AMP_tasks_cog`, `DB_server_cog`, `DB_user_cog`, `Permissions_cog`, `banner_cog`, `regex_cog`, `whitelist_cog` (manual whitelist requests), `whitelist_sync_cog` (Discord-Role↔Whitelist sync). See `COMMANDS.md` for the full command reference and `WHITELIST.md`/`PERMISSIONS.md`/`BANNER.md`/`REGEX.md` for feature-specific docs.

### Database layer
`DB.py` wraps a single SQLite DB (`Database` class). Model classes `DBServer`, `DBUser`, `DBBanner`, `DBConfig` override `__setattr__` so a plain `some_db_obj.Field = value` in application code immediately persists to SQLite (via `Database._UpdateServer`/`_UpdateBanner`/`_UpdateUser`, each guarded by a per-table column allowlist) — there's no separate "save"/"commit" call. Schema is created fresh in `Database._InitializeDatabase`; existing databases are migrated incrementally by versioned methods in `DB_Update.py`, gated on `DB_Version`.

### Logging
`logger.py` configures the standard `logging` module plus two custom levels via `haggis.logs.add_logging_level`: `DEV` (15, between DEBUG/INFO; enabled by `-dev`) and `COMMAND` (19; enabled by `-command`, used to log every slash-command invocation). Get the shared logger anywhere with `logging.getLogger()` (no name arg — it's the root logger).

### Secrets
Primary: `tokens.py` (gitignored, copy from `tokenstemplate.py`) or `tokens_dev.py` when `-dev` is set. Fallback when neither exists: environment variables / a `.env` file (see `.env.template`), loaded by `AMP_Handler.AMPHandler._load_tokens_from_env()` via `python-dotenv`. Either path ends up as `AMPHandler.tokens`, read throughout the codebase as `self.AMPHandler.tokens.<Field>` (e.g. `AMPUser`, `AMPPassword`, `AMPurl`, `AMPAuth`, `SteamAPIKey`, `token`).
