# Codebase Audit — 2026-08-14

Full-repo correctness/dead-code/docs/architecture/security/style audit, done via 6 parallel
subagents (one per track) + synthesis. Nothing here has been fixed yet — check items off as
they're tackled. Re-run/update this file rather than creating a new dated one for follow-up
passes on the same items.

## Critical Issues (ranked by severity)

- [x] **1. Console command injection via game-chat relay.** Discord chat messages are forwarded
      verbatim into AMP console commands (`Chat_Message()`) across every game module, with no
      escaping — unlike the AMP→Discord direction, which does strip newlines. The bot's AMP role
      has broad `Core.*`/game permissions, so an embedded newline/quote in a chat message is a
      plausible path to injected console commands. Any Discord user in the linked chat channel can
      attempt this — no staff role needed.
      `cogs/amp_tasks_cog.py:84-94`, `modules/Minecraft/amp_minecraft.py:147-165`,
      `modules/ProjectZomboid/amp_projectzomboid.py:28-39`,
      `modules/SevenDaystoDie/amp_sevendays.py:26-37`, `modules/Terraria/amp_terraria.py:25-39`,
      `modules/Factorio/amp_factorio.py:38-40`
      Confidence: Med-High
      **Fixed 2026-08-14**: newline-stripped `message.content` once at the cog call site
      (`cogs/amp_tasks_cog.py:94`, matching the existing AMP→Discord precedent) so an embedded
      `\n` can no longer smuggle a second console command. Per-game escaping added at the point
      each `Chat_Message()` builds its console command: Minecraft now uses `json.dumps()` for its
      `tellraw` JSON text fields instead of hand-rolled string interpolation; ProjectZomboid and
      SevenDaysToDie replace `"`→`'` (both build double-quote-delimited commands); Terraria and
      Factorio replace `[`→`(` and `]`→`)` (both use bracket-delimited rich-text tags). Verified
      independently (not just the implementing subagent's word): all 6 files parse, and a
      simulated `tellraw` payload with hostile quotes/backslashes in every field (author,
      author_prefix, server_prefix, message) round-trips through `json.loads()` to the exact
      original text with no JSON-structure break. `modules/CounterStrikeGo`, `StarBound`,
      `Valheim`, `Generic` don't override `Chat_Message` (inherit the harmless no-op base) so
      needed no change.
      **Bonus fix found while in this code, unrelated to the injection issue**: Factorio's
      `Chat_Message` took a `prefix` param instead of `author_prefix` like every sibling module
      and the base class — the cog always calls it with `author_prefix=`, so every Discord→
      Factorio chat message was raising `TypeError` and silently failing before this fix. Renamed
      the param and wired `author_prefix`/`server_prefix` into the output the same way the other
      3 modules do. Confirmed both real call sites (`cogs/amp_tasks_cog.py:97` and `:309`) use
      keyword args only, so the signature change is safe.

- [x] **2. Dict-mutation-during-iteration kills the whitelist wait-list feature.**
      `whitelist_waitlist_handler` iterates `self._client.Whitelist_wait_list` directly (not a
      copy) and `.pop()`s from it mid-loop. First trigger raises `RuntimeError`, which permanently
      stops the `tasks.loop` (discord.py loops self-terminate on unhandled exceptions) until bot
      restart. Same bug independently in `on_member_remove`.
      `cogs/whitelist_cog.py:401-446` and `:104-114`
      Confidence: High

- [x] **3. Privilege escalation via `/user role`.** Accepts a free-text role string with no
      server-side validation against `bPerms.get_roles()` and writes it straight to
      `db_user.Role`. A Moderator-tier user can grant themselves/others a higher custom role.
      `cogs/permissions_cog.py:45-56`
      Confidence: High

- [x] **4. Linked-account identity silently discarded in chat relay.** An `if`/`if` pair that
      should be `if`/`elif` means whenever the chat author *is* a linked Discord account (the
      common case), the computed name/avatar gets immediately overwritten by the raw AMP username
      + generic avatar. A `#!TODO! Test these changes.` comment sits right above it.
      `cogs/amp_tasks_cog.py:265-284`
      Confidence: High

- [x] **5. `_serverCheck()` crashes on a stale/unresolved server ID.** `serverparse()` can return
      `None`; the caller (used by nearly every cog) does `amp_server.Running` unconditionally,
      raising `AttributeError` instead of an "offline" message.
      `core/utils.py:550-561`
      Confidence: High

- [x] **6. `check_SessionPermissions()` can report success despite a missing permission.** Returns
      the *last*-checked node's result on failure instead of `False`, so a mix of granted/missing
      nodes where the last one happens to be granted returns `True`. Gates the untested
      `-whitelist-only` startup path flagged in CLAUDE.md.
      `core/AMP.py:358-391`
      Confidence: Medium
      **Fixed 2026-08-14**: changed `return check` to `return False` in the `if failed:` branch —
      one-line fix, loop/logging untouched. Only caller is `AMPInstance.__init__` (`core/AMP.py:175`),
      which gates the role/permission-repair branch on this return value; no caller changes needed.

- [x] **7. AMP session-cache logic looks inverted, with no cleanup on instance removal.**
      `Login()`'s early-return branch overwrites the cached session with `0` instead of reusing
      it; `_instanceValidation` never purges `SessionIDlist` when an instance disappears, so a
      reappearing instance (restart/hiccup) can get stuck unable to authenticate until the bot
      restarts.
      `core/AMP.py:424-428`, `core/AMP_Handler.py:302-307`
      Confidence: Medium
      **Fixed 2026-08-14**: `Login()`'s cache-hit branch now reads the cached session ID *into*
      `self.SessionID` (was backwards — it overwrote the cache with `self.SessionID`, which is `0`
      at that point), sets `self.Running = True` to match the fresh-login-success branch, and
      returns `True` instead of bare `return` (the method is typed `-> bool`). Verified this is
      safe by reading `CallAPI`'s existing `"Unauthorized Access"` handling (`core/AMP.py:~550`),
      which already pops the stale entry from `SessionIDlist` and resets `SessionID = 0` on a bad
      session — so a reused-but-actually-stale session self-heals on the next API call via the
      existing mechanism; this fix only had to correct the backwards read/write direction, not add
      new invalidation logic. Also added `self.SessionIDlist.pop(instanceID, None)` to
      `_instanceValidation`'s instance-removal loop (`core/AMP_Handler.py:313`) as defense in
      depth for the instance-disappears-and-reappears case specifically.

- [x] **8. Unguarded `getInstances()` failure can hang startup.** `_instanceValidation` subscripts
      the API result with no null-check; on a transient/permission failure at startup this throws
      inside the un-caught AMP init thread, and `start.py` blocks forever waiting for
      `AMP_setup == True` with no diagnostic. Directly relevant to the still-unverified
      `-whitelist-only` mode.
      `core/AMP_Handler.py:259`
      Confidence: Medium-High
      **Fixed 2026-08-14**: added a guard right after `result = AMP.getInstances()` —
      `if not result or not isinstance(result, list):` logs critical, sleeps 30s, and returns,
      mirroring the exact style of the pre-existing sibling "zero instances found" branch one line
      below it. Traced both callers: the 30s poller (`amp_server_instance_check`) already had a
      surrounding `try/except` so this just avoids an ugly traceback there; the startup path
      (`AMP_init` → `setup_AMPInstances` → `_instanceValidation`, no try/except anywhere in that
      chain) is the one that actually mattered — it can no longer raise here, so `AMP_setup = True`
      always gets set and `start.py` can't hang on this path anymore.

- [x] **9. Console sender-filter doesn't actually suppress anything.** `console_chat()` `return`s
      (falsy `None`) instead of `True` when a sender matches the filter list; the caller's
      `if self.console_chat(entry): continue` never fires, so filtered messages leak through.
      `core/AMP_Console.py:243-247`
      Confidence: Medium
      **Fixed 2026-08-14**: changed `return` to `return True` in the filtered-sender branch;
      updated the method's return-type annotation from `-> None | bool` to `-> bool` since every
      path now returns an actual bool. One-line behavior fix.

- [x] **10. Unlocked cross-thread mutation of `AMP_Instances`.** The AMP background thread
      adds/removes instances every 30s while several asyncio task loops iterate the same dict —
      no lock. Narrow window, but structurally real.
      `core/AMP_Handler.py` (`_instanceValidation`) vs. `cogs/amp_tasks_cog.py`,
      `whitelist_sync_cog.py`
      Confidence: Medium
      **Fixed 2026-08-14, in two passes.** Pass 1 wrapped every live iteration in the two
      originally-cited files in `list(...)` — 5 sites in `cogs/amp_tasks_cog.py`, 1 in
      `cogs/whitelist_sync_cog.py` (a 2nd site there, line 223, was already correctly wrapped and
      became the precedent this fix followed). No `threading.Lock` introduced — CPython's GIL
      makes the `list(...)` snapshot itself atomic, sufficient to prevent the `RuntimeError` crash
      from a concurrent add/remove. While verifying pass 1, a repo-wide grep found the original
      citation understated the blast radius: 9 more unguarded live-iteration sites of the same
      dict existed outside the two cited files. Pass 2 fixed all 9, same `list(...)` pattern:
      `core/utils.py:510` (`serverparse()` — called by `_serverCheck`, hit by nearly every
      server-related Discord command, the highest-traffic site of all), `cogs/amp_server_cog.py:96`
      (`amp_server_broadcast`), `cogs/whitelist_cog.py:116` and `modules/Minecraft/cog_minecraft.py:52`
      (both `on_member_remove` listeners), `core/AMP_Handler.py:70` (shutdown-time console-thread
      stop) and `:134` (`get_AMP_instance_names`, used by autocomplete), `core/AMP.py:597`
      (`_updateInstanceAttributes`, reachable from the Discord thread via `__getattribute__`) and
      `:610` (`_instance_ThreadManager` — same-thread as the mutator so lower risk, fixed anyway
      for consistency), `core/loader.py:64` (one-time startup-only, same reasoning). Final
      repo-wide grep (run independently, not just taking the implementing subagent's word)
      confirms zero remaining unwrapped iterations of `AMP_Instances`/`AMPInstances` anywhere in
      the codebase — all 16 total sites now snapshot before iterating.

- [x] **11. `banner_cog.py`'s two reconciliation state machines have already diverged.**
      `_embed_generator`/`_banner_generator` duplicate the same ~80-line delete/edit/resend logic,
      and only one wraps `message.delete()` in try/except — evidence a bug fix in one path was
      missed in the other.
      `cogs/banner_cog.py:158` (both methods)
      Confidence: Medium-High
      **Fixed 2026-08-14**: found 4 total `await message.delete()` call sites across both methods
      (2 per method), not just the 1 divergent pair — the "remove extra messages" branch was
      unguarded in *both* methods (not a divergence, but the same risk twice), and only
      `_banner_generator`'s "remove all + resend" branch had the try/except. Brought all 3
      unguarded sites to parity with the one that was already correct: wrap `await message.delete()`
      in `try: ... except: self.logger.error(...)`, keeping the DB-side `Remove_Message_from_BannerGroup`
      call unconditional either way. Pure parity fix, no extraction/refactor of the duplicated logic
      (that remains a separate Structural Concern, not attempted here).

- [x] **12. Whitelist add/remove uses the raw input name, not the Mojang-verified canonical
      name**, after verification already resolved it. Same unescaped-interpolation pattern as #1,
      lower exposure (staff-gated).
      `cogs/whitelist_cog.py:207/229` → `modules/Minecraft/amp_minecraft.py:70-78`
      Confidence: Low-Medium
      **Fixed 2026-08-14**: added `resolve_canonical_IGN(name)` — a base no-op-passthrough stub on
      `AMPInstance` (`core/AMP.py`, matching the existing `name_History` base-stub precedent) plus
      a Minecraft override (`modules/Minecraft/amp_minecraft.py`) that mirrors `name_Conversion`'s
      exact Mojang API call but returns the canonical `name` field instead of `id` (which
      `name_Conversion` already receives but discards). `name_Conversion` itself and its 3 existing
      call sites were left untouched to avoid destabilizing `check_Whitelist`'s branching — this
      was an additive, isolated fix. Both `whitelist_cog.py` call sites now resolve the canonical
      name once and use it for both the AMP console command and the confirmation message shown to
      staff.

- [x] **13. (Found during #5 verification, fixed 2026-08-14) `server_settings_whitelist_set`
      crashes on a not-found/offline server.** `amp_server = await self.uBot._serverCheck(context,
      server, False)` returns `None`/`False` without sending any message (that's the
      `online_only=False` contract). The two lines building `server_name` and sending the
      confirmation were sitting *outside* the `if amp_server:` guard, so a falsy `amp_server`
      still hit `amp_server.FriendlyName` unconditionally — `AttributeError`. Its two sibling
      commands (`server_settings_whitelist_auto`, `server_settings_whitelist_wait_time`) already
      kept everything inside the guard; fixed by re-indenting the two lines to match.
      `cogs/whitelist_cog.py:148-149`
      Confidence: High

## Quick Wins (safe, low-risk cleanup)

### Delete/remove

- [x] 10 unused packages in `requirements.txt`: `docopt`, `ffmpeg-python`, `future`, `GitPython`,
      `gitdb`, `smmap`, `nbtlib`, `pipreqs`, `yarg`, `imageio-ffmpeg` — none imported anywhere.
      (High confidence; looks like this file was generated via `pipreqs`/`pip freeze` from a dev
      venv.)
      **Fixed 2026-08-15**: all 10 removed, 23 remain. Verified independently that no `.py` file
      imports any of them. The only near-miss was `from __future__ import annotations` (~25 files)
      — that's Python's builtin `__future__`, not the PyPI `future` compat package. Transitive
      chain also confirmed: `GitPython→gitdb→smmap` and `pipreqs→{docopt,yarg}`, and since both
      parents were themselves unused, the children had no remaining reason to stay; no kept package
      depends on any of the 10. Note `start.py` hashes this file to decide whether to re-run
      `pip install`, so the next startup will re-install once.
- [x] Stale commented-out code in `core/AMP.py`: old `result['result'][...]`-wrapped return
      variants at lines ~784, 588-598, 915, and leftover `# print(...)` debug lines at ~546/558.
      **Fixed 2026-08-15**: 7 pieces removed — both `CallAPI()` debug prints, the two commented
      alternate-shape lines in `_updateInstanceAttributes()`, and the stale `# return result['result']`
      variants in `getSchedule()`, `CurrentSessionHasPermission()`, and `getRoleIds()` (the last two
      weren't all in the audit's line list but are the identical dead pattern). In
      `CurrentSessionHasPermission()` the dead comment sat inside an `if result != False: return result`
      / `return result` pair that returned the same value on both branches — collapsed to a single
      `return result`, behavior-identical. Real explanatory comments and `#!TODO!` markers untouched.
- [x] Commented-out, non-functional call in `cogs/amp_tasks_cog.py:52` (references a method
      that isn't defined on that class).
      **Fixed 2026-08-15**: deleted. Confirmed dead — `amp_server_instance_check` exists only as a
      **module-level function** in `core/AMP_Handler.py:37` (called at `:34` by the AMP polling
      thread). The commented code invoked it as `self.amp_server_instance_check.start()`, i.e. as a
      `tasks.Loop` attribute on the `AMP_Tasks` cog, which it never was — the cog has exactly three
      `@tasks.loop` methods and this isn't one of them.
- [x] Three commented-out `DB_Update.py` migration helper calls, one of which references a
      method that doesn't exist anywhere (`user_MC_IngameName_unique_constraint`).
      **Partially fixed 2026-08-15 — deliberately did *not* delete all of them.** There are actually
      **four** such commented calls, not three. Only `#self.user_MC_IngameName_unique_constraint()`
      (in the `2.6 > Version` block) was deleted: grep confirms no such method exists anywhere, so
      it could never run even if uncommented. The other three — `#self.nicknames_unique()` (1.3
      block), `#self.server_ip_constraint_update()` and `#self.server_display_name_constraint_update()`
      (both 1.8) — **were kept**: all three methods still exist in the same file, and two carry
      docstrings explicitly recording *why* they're disabled ("SQLITE does not support dropping/adding
      UNIQUE constraint"). The third (`nicknames_unique`) runs the same unsupported
      `ALTER TABLE ... ADD CONSTRAINT ... UNIQUE` and `sys.exit(-1)`s on failure, so enabling it
      would hard-kill the bot mid-migration. These are intentionally-disabled migration history, not
      dead code. Added a short comment at each of the three call sites explaining this, so future
      audits stop re-flagging them.
- [x] `core/DB.py`'s `GetLog()` — unused **and** broken (selects `IngameName`/`UUID` columns
      that don't exist; actual columns are `MC_IngameName`/`MC_UUID`). Also unused:
      `dbServerConsoleSetup`, `GetAllUsers`.
      **Fixed 2026-08-15**: all three deleted (140 lines). Repo-wide grep for all three names now
      returns zero hits. The `GetLog()` breakage claim was accurate — it selected `IngameName`/`UUID`
      from `Users`, whose real columns are `MC_IngameName`/`MC_UUID` (per `_InitializeDatabase` and
      `_USERS_ALLOWED_COLUMNS`), with no migration ever renaming them, so it would have raised
      `sqlite3.OperationalError`. `dbServerConsoleSetup`'s job is superseded by direct field writes
      in `cogs/amp_server_cog.py`; `GetAllUsers` had no bulk-fetch replacement to worry about —
      `whitelist_sync_cog.py` iterates Discord guild members and looks up users individually.

### Doc fixes

- [x] `core/discordBot.py:22` — `Version = 'beta-4.7.5'` is 4 changelog entries stale and is
      user-facing (surfaced via `/bot utils status`, and support workflows tell users to quote
      it).
      **Fixed 2026-08-15**: bumped to `beta-4.11.0`, matching `docs/changelog.md`'s topmost heading
      `__**Update 4.11.0**__` (no "Unreleased" heading exists, so no ambiguity). The `beta-X.Y.Z`
      code value ↔ `Update X.Y.Z` changelog heading mapping is consistent. Every read site is a
      string-equality check or an f-string/`i18n.t()` interpolation — nothing parses it numerically.
      **Side effect to expect on next start**: `setup_hook()` compares `self.Bot_Version != Version`
      and, on mismatch, fires `update_loop`, which writes the new value to `DBConfig` and does a
      one-time `tree.copy_global_to()` + `tree.sync()`. That's the intended behavior of a version
      bump, but it means the first startup after this change re-syncs the command tree.
- [x] `docs/PERMISSIONS.md:164-166` — the "Full Permission Node List" is missing
      `server.console.interact`, even though the prose above it references that node as real and
      required.
      **Fixed 2026-08-15**: added under the `server.console.*` group. Ground truth re-derived from
      code rather than trusting the audit: `async_rolecheck()` auto-derives a node from
      `str(context.command).replace(" ", ".")` for every `@utils.role_check()`-decorated command,
      and exactly **three** nodes are instead passed explicitly via `perm_node=` — `'staff'`
      (`core/utils.py:123`), `'whitelist_buttons'` (`core/utils_ui.py:173,193`), and
      `'server.console.interact'` (`cogs/amp_tasks_cog.py:71`, gating message sends in a linked
      Discord Console Channel). Verified the first two were already documented (lines 94/96) — so
      `server.console.interact` really was the only omission. No node is listed in the doc that the
      code never checks.
- [x] `core/AMP.py:894` — `getAMPUserInfo()` docstring references an `IdOnly` param that doesn't
      exist on the method.
      **Fixed 2026-08-15**: rewritten to describe the real signature/return, derived from the body
      and both callers (`getAMPUserID()` reads `result["ID"]`; `check_GatekeeperRole_Permissions()`
      reads `.get("ID")`/`.get("Roles", [])`). Now also warns that the failure path returns whatever
      `CallAPI()` yields (typically `False`), so callers should type-check before use.
- [x] Update CLAUDE.md's dead-code note about `Banner_Editor_View` in `core/utils_ui.py` — that
      class no longer exists there at all (confirmed by direct read); the live banner editor is
      solely `utils_dev/banner_editor/`. The documentation itself is now stale.
      **Fixed 2026-08-15**: re-verified before editing — `Banner_Editor_View` exists only in
      `utils_dev/banner_editor/ui/view.py:21` and is imported live by `cogs/banner_cog.py:27`;
      `core/utils_ui.py` defines 15 classes, none banner-editor-related (they're the server-control,
      whitelist, link-confirm, and instance-ID-swap views). CLAUDE.md's i18n Coverage bullet now says
      `utils_dev/banner_editor/*` is the *only* banner editor, and explicitly records that the old
      "parallel dead copy in `core/utils_ui.py`" claim was checked and is false — so the correction
      doesn't get re-reverted by a future reader.

### Small correctness-adjacent fixes (harmless today, worth tightening)

- [x] `core/AMP.py:561` `_ADScheck()` and `:272` `check_GatekeeperRole_Permissions()` fall off
      the end returning implicit `None` in a failure branch instead of the `False` their own
      docstrings promise. Currently harmless (falsy in an `if`), but worth an explicit
      `return False`.
      **Fixed 2026-08-15**: explicit `return False` added to both. `_ADScheck()` — the `if Success:`
      branch was the only return path, so a failed `Login()` fell through. `check_GatekeeperRole_Permissions()`
      — when the role exists but the permission loop sets `failed = True`, execution fell past
      `if not failed: return True`; the nearby `else: return False` belongs to the *outer*
      `if self._AMP_botRole_exists` and never caught it. Verified `failed` is initialized at the top
      of the function, so the new path can't `NameError`. All 11 `_ADScheck` call sites and the single
      `check_GatekeeperRole_Permissions` caller (`core/AMP.py:192`, used as `if not role_perms:`) use
      the result only in truthy/falsy context, so `None`→`False` is behavior-identical everywhere.
- [x] `start.py:78` — `Setup.python_ver_check` is defined but **never called**. Not a delete
      candidate — looks like a startup guard that was wired up and then the call site got
      dropped. Decide: wire it back in, or remove if intentionally abandoned.
      **Decision: wired in (2026-08-15)** — called as the first statement of `Setup.__init__`
      after `parse_args()`, before `pip_install()`/DB/AMP/Discord, so it fails fast.
      **Correction to the audit's premise**: it was *not* "wired up and then the call site got
      dropped". Scanning `start.py` at every commit in history for `self.python_ver_check()` returns
      **zero hits** — it was added in `b4c1744` ("Regex Support") already unwired and never called
      once. The two bugs below corroborate that: neither would have survived a single real run.
      **The guard itself turned out to be doubly broken**, which is why nobody noticed it was
      unwired — both bugs fixed:
      1. **The condition never fired.** `not sys.version_info.major >= 3 and not sys.version_info.minor >= 10`
         parses as `(major < 3) and (minor < 10)`, not the intended `NOT(major >= 3 AND minor >= 10)`
         — De Morgan was never applied. It could only trigger on Python 1.x/2.x; every Python 3.0–3.9
         sailed through despite the stated 3.10 minimum. Replaced with `sys.version_info < (3, 10)`.
      2. **The error message would itself crash.** `sys.version_info.major + "." + sys.version_info.minor`
         adds `int` to `str` → `TypeError` on the exact path meant to print a clean error. Replaced
         with an f-string.
      Also switched `self.logger.critical(...)` → `print(...)`: `self.logger` doesn't exist yet this
      early in `__init__`, and `pip_install()`'s own pre-logger version guard already uses `print()`.
      **Version-declaration mismatch — RESOLVED 2026-08-15, standardized on 3.13.** The repo had
      declared four different minimums. All now agree:
      | Where | Was | Now |
      |---|---|---|
      | `start.py:84` runtime guard | `3.10` | `3.13` |
      | `pyproject.toml:16` `requires-python` | `>=3.13.0` | unchanged |
      | `pyproject.toml:42` ruff `target-version` | `py311` | `py313` |
      | `pyproject.toml:96` pyright `pythonVersion` | `3.11` | `3.13` |
      3.13 is the right target: production runs it (`DEPLOYMENT_LOG.md`), `docs/INSTALL.md` already
      documents "Python 3.13 or greater" throughout, `core/logger.py:9` carries a 3.13-specific
      workaround, and `requirements.txt` pins 3.13-compatible versions plus
      `audioop-lts; python_version >= "3.13"`.
      **Behavior change worth knowing**: the bot now *refuses to start* on 3.10–3.12. It would
      previously have run there (audioop was still in the stdlib below 3.13), so this is a
      deliberate tightening, not just a doc sync.

### Flag, don't auto-delete (needs judgment)

- [x] `core/utils.py:135` — the entire `discordBot` helper class (`self.dBot`, 7 methods:
      `userAddRole`, `delMessage`, `sendMessage`, etc.) is instantiated in ~14 places but
      `self.dBot.<method>` has zero call sites anywhere. Big if true — worth a second look before
      deleting a whole class.
      **Investigated, then DELETED 2026-08-15** (investigation first, human go/no-go given, then
      executed — see the evidence below for why it was safe).
      **Verdict: the claim is TRUE.** `core/utils.py:135-195`, class `discordBot`, 7 async methods
      (`userAddRole`, `userRemoveRole`, `delMessage`, `channelHistory`, `editMessage`, `sendMessage`,
      `messageAddReaction`), each a thin wrapper around a discord.py call plus a `dev` log line.
      Repo-wide grep for `self.dBot.` → **zero hits**; grep for each of the 7 bare method names →
      the only hit is each method's own `def` line. No other class in the repo defines a same-named
      method, so there are no false positives to disambiguate. Not subclassed, no
      `getattr`/dispatch-table/`partial` usage.
      **Correction to the count: 16 instantiation sites, not ~14 — and the 16th matters.**
      6 in `cogs/`, 9 in `modules/*/cog_*.py`, and — missed by the investigating subagent —
      **`resources/templates/cog_template.py:35`**, the template new game-module cogs are copied
      from. Deleting the class without also fixing that template would ship a broken scaffold that
      silently reintroduces the reference in every future module.
      Cost of keeping it is near-zero at runtime (`__init__` is two assignments + a debug log; no
      I/O). The real cost is misleading surface: 5 module cogs carry a comment claiming
      `utils.discordBot` "provides access to utility functions such as sending/deleting messages,
      kicking/ban users" — aspirational, never true.
      **What was actually removed**: the class body (`core/utils.py`, 61 lines), all 16
      `self.dBot = utils.discordBot(client)` lines, and **6** stale comments (not 5 — the template
      carries one too). One orphaned import fell out as predicted: `from datetime import datetime`
      in `core/utils.py` was used *only* by the deleted `channelHistory()`, so it went as well
      (verified `datetime` had no other occurrence in the file). 17 files touched; all compile.
      Post-delete grep for `dBot` / `discordBot(client)` returns only unrelated hits — the live
      `core/discordBot.py` module (`Gatekeeper` bot class) and the `discordBot.db` SQLite filename
      in `core/DB.py`. Note `resources/templates/cog_template.py` was included, so newly scaffolded
      game-module cogs no longer reintroduce the dead attribute.
- [x] 13 unused `AMPInstance` API-wrapper methods in `core/AMP.py` (`copyFile`, `getPermissions`,
      `getRole`, `trashFile`, ...) — medium confidence only, since a thin API wrapper class
      plausibly keeps a full surface on purpose.
      **Investigated 2026-08-15 → DECISION: keep the 14 API wrappers, delete the 4 chat/name
      methods. Item closed.** The audit's own hypothesis was right *for the wrappers*:
      `AMPInstance` is a thin wrapper over AMP's HTTP API, and a complete endpoint surface is worth
      keeping — that inventory is recorded below so a future audit doesn't re-derive it or re-flag
      them. The other 4 turned out not to be that case at all; see (b). The real count is
      **18**, not 13; the audit's own estimate was flagged medium-confidence and undercounted. All
      four named examples are confirmed zero-call-site. Full list, with the two categories kept
      distinct because they warrant *different* decisions:
      **(a) Thin AMP API wrappers (14) — KEPT** — `ConsoleMessage_withUpdate`, `getSchedule`,
      `setFriendlyName`, `getAPItest`, `copyFile`, `renameFile`, `writeFileChunk`, `endUserSession`,
      `getActiveAMPSessions`, `getInstanceStatus`, `trashDirectory`, `trashFile`, `emptyTrash`,
      `getPermissions`, `getRole`, `getUpdateInfo`. These are exactly the "complete API surface kept
      on purpose" case — note `getFileChunk` **is** used (`modules/Minecraft/amp_minecraft.py:100`)
      while its sibling `writeFileChunk` isn't, and `getRoleIds`/`setRoleIDs` are used while `getRole`
      isn't. Keeping them is defensible.
      **(b) `name_History` and `Chat_Message_Formatter` (4 methods) — DELETED 2026-08-15 after a
      git-history investigation.** This item went through two wrong readings before the right one;
      recording all three so the reasoning isn't repeated:
      1. The investigating subagent called them bare base-class stubs — wrong, both have Minecraft
         overrides (`modules/Minecraft/amp_minecraft.py:64`/`:181`) beside the base declarations
         (`core/AMP.py:1019`/`:1042`), so it was 4 dead methods, not 2.
      2. They were then kept on the theory that those overrides were *working code that had lost its
         call site* — **also wrong**, and the reason this needed a third look. Neither override does
         anything useful:
      - **`name_History`** was added in `1c537eb` **already unwired**, with the docstring
        *"WTF Does this even return? Possible a Dictionary List?"* — exploratory scaffolding, not a
        lost feature. Decisively, its endpoint no longer exists: Mojang removed the name-history API
        in 2022. Verified live 2026-08-15 —
        `GET https://api.mojang.com/user/profiles/{uuid}/names` → **HTTP 404**, while the sibling
        `POST https://api.mojang.com/profiles/minecraft` that `name_Conversion`/`resolve_canonical_IGN`
        depend on → **HTTP 200**. Rewiring it would guarantee an `IndexError`/`JSONDecodeError` on
        `post_req.json()[-1]`.
      - **`Chat_Message_Formatter`** genuinely *was* wired — `ac8eb75` ("Refactored Server Chat to
        Discord") removed the call
        `Server.Chat_Message(message=Server.Chat_Message_Formatter(message['Contents']), ...)` from
        the cross-server relay. But **both** base and Minecraft override are `return message`, a pure
        identity function, so restoring the call would change nothing. The refactor replaced it with
        `message_contents = message['Contents'].replace('\n', ' ')` — strictly more behavior (that
        newline strip is the AMP→Discord sanitization referenced in Critical #1).
      **General lesson**: "an override exists" is not evidence that real work would be lost — read
      the override *body* and `git log -S` the call site before deciding. A no-op override and a
      never-called stub look identical to a call-graph query.

## Structural Concerns (need a real decision, not a mechanical fix)

- [x] **1. `AMPInstance.__init__` is a ~170-line god-constructor that calls `sys.exit(1)`
      directly, three times** (`core/AMP.py:54`). Mixes credential setup, dynamic `setattr()`
      injection from the API response, DB lookups, and a permission-bootstrap state machine.
      Constructing an object can kill the whole process as a side effect — an error-propagation
      redesign question, not a quick patch.
      **Done 2026-08-15** (full redesign chosen over pure code motion). Split into
      `_init_handles()` / `_init_credentials()` / `_init_instance_data()` /
      `_bootstrap_permissions()`; new `AMPInitError` replaces both `sys.exit(1)` calls, caught in
      `AMP_Handler.setup_AMPInstances()` (main instance → log critical + `sys.exit(1)`, preserving
      today's effective behavior) and in `_instanceValidation()`'s per-instance loop (game instance
      → log + `continue`). **Three behavior changes, all deliberate:**
      1. A misconfigured game instance no longer takes the whole bot down — it's skipped and
         retried on the next 30s poll. It is *not* added to `AMP_Instances` (so it retries) but
         *is* appended to `available_instances` before the `try` (so the missing-instance cleanup
         below doesn't mistake it for a deleted server).
      2. **Bug fix**: `permission = self.check_SessionPermissions()` sat in a `try` whose `except`
         only exited for `InstanceID == 0`; a game instance fell through to `if permission:` with
         `permission` unbound → `UnboundLocalError`. Now always raises `AMPInitError`.
      3. A malformed `GATEKEEPER_AMP_AUTH` 2FA code used to log critical and bare-`return`, leaving
         a half-built object with `Initialized == False` that nothing checked. Now raises, so
         startup fails loudly instead of limping.
      **Verified**: `Initialized` is still set in exactly the same cases (both early returns set it
      before returning, plus the unconditional set at the bottom covering the fall-through and the
      "game instance not Running" skip); subclass ordering still holds — `modules/*/amp_*.py` set
      `self.perms`/`self.APIModule` before `super().__init__()`, and `_init_credentials()`'s
      `hasattr` checks still run after that.
- [x] **2. `async_rolecheck()` conflates three unrelated concerns** — caller-type sniffing, three
      separate permission backends, and sending the Discord error message itself
      (`core/utils.py:28`). Also carries an unresolved
      `#!TODO! Not sure which one triggers this` in security-relevant code.
      **Done 2026-08-15.** Split into `_resolve_rolecheck_author()` (raises `TypeError` on an
      unexpected type instead of falling through with unbound locals), `_rolecheck_permission()`
      (pure decision, no Discord I/O), and `_send_rolecheck_denial()`. `async_rolecheck()` remains
      the public entry point with an unchanged name/signature/`bool` return, since it's used as a
      `commands.check` predicate and called directly in four places.
      The decision function returns `(allowed, denial_key)` rather than a bare `bool` — that's what
      preserves the non-obvious original behavior that a *Custom*-backend denial only logs, while
      the two *Default*-path denials also message the user.
      **The `#!TODO!` resolved to three real bugs, all fixed:**
      1. `discord.Member` and `discord.member.Member` are the *same class*, so
         `if type(context) != discord.Member:` / `elif type(context) == discord.member.Member:`
         were exact complements — the trailing `else` (commented "for on_message commands") was
         **unreachable**. The Member branch was also independently broken (`author = context.name`
         assigned a `str`, then `author.guild_permissions` was read off it). No caller ever passed
         a Member; both branches deleted.
      2. **`await context.send(...)` is wrong for `discord.Interaction`** — it has no `.send()`.
         Four of the six call sites pass an Interaction, so a permission denial reaching them
         raised `AttributeError` instead of telling the user. `_send_rolecheck_denial()` now
         dispatches on type and handles the already-responded case via `.followup.send()`.
      3. `botPerms.perm_node_check()` had the same Context-vs-Interaction assumption
         (`context.author.id`/`.roles`); its signature now takes the resolved `discord.Member`.
         Single call site, verified by grep.
- [x] **3. The `/bot` command group bypasses the cog/loader pattern entirely** — ~15
      subcommands live as module-level functions on the global client
      (`core/discordBot.py:125`) instead of going through `core/loader.py` like every other
      command surface, so they're invisible to the bot's own `bot cog load/unload/reload`.
      **Done 2026-08-15.** All 21 commands moved to `cogs/bot_cog.py` (`class Bot(commands.Cog)`,
      `Dependencies = None`); `core/discordBot.py` is down to 117 lines holding only the
      `Gatekeeper` client class, `Version`, `client_run()`, and the i18n startup call.
      Qualified names are byte-identical, which matters because every `commands.bot.*` locale key
      is derived mechanically from `qualified_name` — a rename would have silently degraded the
      whole group to raw-key text. Per-command permission decorators preserved exactly
      (`administrator=True` on `moderator`/`permissions`/`language`, `role_check()` elsewhere).
      **Self-unload footgun guarded**: `bot cog unload` refuses when `cog == self.qualified_name`,
      and `core/loader.py`'s `cog_auto_loader()` skips `bot_cog.py` when `reload=True` only (it
      still auto-loads normally at startup), mirroring the existing `permissions_cog.py` exclusion.
      Two new locale keys in both EN and DE; parity verified at 465 keys each.
      **Non-obvious thing checked**: `autocomplete_loadedcogs` became a cog *method*, so it now
      needs `self`. discord.py 2.4.0 only passes the cog instance when
      `validate_auto_complete_callback()` sets `pass_command_binding`, which it does via
      `is_inside_class()` (qualname-based) — and it then requires exactly 3 params. Confirmed
      against the installed source. Note this is validated at *decoration* time, so a wrong param
      count raises `TypeError` on import and `py_compile` would **not** catch it.
- [x] **4. Business logic (DB writes, AMP calls, role assignment) lives directly inside Discord
      UI Button/View callbacks** in `core/utils_ui.py:145` (`Whitelist_view`,
      `Accept_Whitelist_Button`, `DB_Instance_ID_Swap`'s `Approve_Button`) — untestable without
      simulating a full Discord interaction.
      **Done 2026-08-15.** Four module-level functions extracted —
      `fulfill_whitelist_request()`, `resolve_link_db_user()`, `apply_link()`,
      `swap_db_instance_ids()` — none of which touch `interaction`, `view`, or any `discord.ui`
      object. Side-effect ordering preserved in each case (it's load-bearing: the DB write before
      the AMP call determines the failure mode if the AMP call throws). Two now-dead `self.DB`
      attributes removed from `Whitelist_view`/`LinkConfirmView` afterwards.
      **Verified**: the callback now passes the *button's* `_amp_server` where the old code used
      the *view's* — `Whitelist_view.__init__` passes the same object into both, so it's identical.
      One flagged "suspicious" item was a false alarm and correctly left alone:
      `amp_server.addWhitelist(...)` is called without `await`, but it's a plain `def` in all three
      definitions — awaiting it would break it.
- [x] **5. Webhook get-or-create logic is duplicated near-identically across 3 task loops** in
      `cogs/amp_tasks_cog.py:98` — a contained, mechanical extraction if wanted.
      **Done 2026-08-15.** Extracted `_get_or_create_webhook(channel, friendly_name, webhook_name,
      expected_channel_id, log_prefix)`. Control flow is identical across all three (name match →
      `break`, channel-id comparison, `edit` on mismatch, `create_webhook` on miss); log levels
      (`debug` vs the custom `dev`) preserved per line, and each loop's distinct `*AMP Console/
      Event/Chat Message*` prefix is passed through rather than unified.
      **The three webhook name literals are unchanged and never routed through `i18n.t()`** — they
      are stored identity keys matched by exact string equality across restarts, so translating
      them would orphan/duplicate webhooks (see CLAUDE.md's i18n section).
      Two cosmetic `debug`/`dev`-level log-wording unifications accepted; confirmed these were the
      only webhook get-or-create sites in the repo. Also cleaned up in the same file: two
      commented-out lines trying to start `self.amp_server_instance_check` as a cog task loop — no
      such cog attribute exists, the 30s poll lives in `core/AMP_Handler.py:37` on the background
      AMP thread — and an `AMPServer_Event .DisplayName` stray-space typo.
- [x] **6. `core/utils.py` bundles four unrelated systems** in one 638-line module (was 694 before
      the dead `discordBot` class came out in the Quick Wins pass): role-check
      decorators, Discord plumbing, a Mojang/Steam-API grab-bag, and the custom-permissions
      engine.
      **Done 2026-08-15** (split *with* import-site updates, no re-export shim — deliberate choice
      to avoid leaving an indirection layer behind). 638 lines → four modules:
      | Module | Lines | Holds |
      |---|---|---|
      | `core/utils_permissions.py` | 273 | authorization gate + `bPerms`/`get_botPerms()`/`botPerms` |
      | `core/utils_discord.py` | 225 | `DiscordPlumbingMixin` + `autocomplete_servers[_public]` |
      | `core/utils_api.py` | 129 | `GameAPIMixin` (Mojang/Steam lookups) |
      | `core/utils.py` | 86 | `botUtils` + the small generic helpers |
      **`botUtils` was deliberately NOT split as a class.** It's instantiated as `self.uBot` in
      every cog with ~200 `self.uBot.<method>` call sites; splitting the class would have broken
      all of them for no gain the audit asked for. Instead the two halves became mixins and
      `core/utils.py` declares `class botUtils(GameAPIMixin, DiscordPlumbingMixin)`, so the public
      surface is untouched — verified by AST-diffing the method set against `git show
      HEAD:core/utils.py`: **19 methods before, 19 after, none added or missing.**
      Import sites updated across 13 files (~146 call-site rewrites, `utils.role_check` →
      `utils_permissions.role_check` being the bulk of it); `core/utils_embeds.py` and all 9
      game-module cogs needed no change since they only ever used `utils.botUtils`.
      `resources/templates/cog_template.py` updated too — otherwise every future game module would
      be scaffolded with broken imports.
      **Things checked that could have silently broken:**
      - *Name mangling.* `__AMP_Handler` is a `__`-prefixed module global that moved into a file
        which now also contains a class. Any reference to it from inside a class body would mangle
        to `_DiscordPlumbingMixin__AMP_Handler` → `NameError` at runtime. AST-verified that no
        `__`-prefixed name is referenced inside any class; the only two users are module-level
        functions, where mangling doesn't apply.
      - *Import cycles.* Resulting DAG is acyclic: `utils_permissions → DB, i18n`;
        `utils_api → (nothing from core)`; `utils_discord → AMP_Handler, utils_permissions`;
        `utils → DB, AMP_Handler, utils_api, utils_discord`. Note `core/AMP_Handler.py:22`'s
        `# import utils` is **commented out** — a naive grep lists AMP_Handler as a `utils`
        importer and suggests a cycle that doesn't exist.
      - *Dropped import-time side effect.* The unused `__DB_Handler = DB.getDBHandler()` global was
        removed, which also removes a DB-singleton initialization that happened merely by importing
        `core/utils.py`. Safe only because `start.py:57` calls `DB.getDBHandler()` before
        `from core import discordBot` (line 72) triggers any cog import — verified, not assumed.
      - Repo-wide AST sweep resolving every `utils*.X` reference against its module's real
        top-level symbols: zero unresolved. (Six apparent hits were all false positives — five are
        docstrings naming `core/utils.py`, and `utils_dev/banner_editor/ui/copy_to_select.py`
        imports `utils` from **discord**, not core.)

## Conflicts / Notes Between Subagents

- ~~**CLAUDE.md's own documentation is now stale.**~~ **Resolved 2026-08-15** — CLAUDE.md's i18n
  Coverage bullet claimed a dead-code `Banner_Editor_View` lived in `core/utils_ui.py`. Re-verified
  and corrected: the class exists only in `utils_dev/banner_editor/ui/view.py:21` and is live
  (imported by `cogs/banner_cog.py:27`); `core/utils_ui.py` has no banner-editor class at all.
  CLAUDE.md now records that the old claim was checked and found false, so it doesn't get re-added.
- **Style agent flagged `modules/Factorio/amp_factorio.py` missing `self.perms = []`** before
  `super().__init__()`, unlike all 7 sibling modules — verified directly against the base class:
  `AMPInstance.__init__` sets `self.perms` itself from the permission profile *before* calling
  `setup_Gatekeeper_Permissions()`, so the sibling modules' `self.perms = []` line is actually
  dead/overwritten, and Factorio's omission is **not a runtime bug** — just a harmless style
  inconsistency. Downgraded from "possible bug" to pure style item.
- No other direct contradictions between subagents — the AMP session/permission-check findings
  (Critical #6/#7, and the security track's session-permission finding) all point at the same
  fragile area (`core/AMP.py`'s login/session/permission-check cluster) from different angles
  rather than disagreeing.

## Style/Tooling Ground Truth (reference)

- `ruff check .`: 1076 errors (193 auto-fixable), dominated by missing type annotations
  (`ANN*`, ~57%) and implicit-`Optional` (`RUF013`, 120 — i.e. `x: str = None`).
- `pyright` (basic mode, against a real venv): 1501 errors, mostly downstream of the same
  implicit-`Optional`/missing-annotation root cause ruff already flags — not an independent
  problem class.
- Minor naming/quote-style/log-message-template inconsistencies exist but are low-impact:
  - `cogs/db_server_cog.py:79` — `db_server_changeinstanceid` breaks the underscore-per-word
    naming convention every other multi-word subcommand handler follows.
  - `cogs/db_server_cog.py:58` — one log line breaks the `"{author} used <Feature Name>"`
    template used by ~55 other command-invocation log lines.
  - Quote-style is split: most of the codebase is single-quote-dominant, but `core/AMP.py`,
    `core/DB.py`, `core/AMP_Console.py`, and `core/DB_Update.py` skew double-quoted; ruff has no
    `Q` rule selected to enforce either way.
  - `modules/Minecraft/amp_minecraft.py` mixes bare camelCase and `PascalCase_underscore`
    method naming — inherited from the base `AMPInstance` class, so it's a systemic convention,
    not a Minecraft-specific deviation.

---

**Status as of 2026-08-15**: **every item in this audit is now closed** — all 13 Critical Issues,
all Quick Wins (including the two "Flag, don't auto-delete" items: the dead `utils.discordBot`
class was deleted, the 18 unused `AMPInstance` methods were kept on purpose), and all 6 Structural
Concerns.

**None of it has been run against a live bot yet.** Everything is uncommitted working-tree state.
The Structural Concerns pass in particular is ~1,100 lines of pure refactor across 30+ files with
no test suite behind it, so it needs a real deployment before being trusted.

Behavior changes introduced by the Structural pass (everything else was structure-only):
1. A game instance that fails to initialize is now skipped and retried on the next 30s poll instead
   of calling `sys.exit(1)` and taking the whole bot down (#1).
2. A malformed `GATEKEEPER_AMP_AUTH` now fails startup loudly instead of leaving a half-built
   object with `Initialized == False` (#1).
3. Permission denials arriving via a `discord.Interaction` — whitelist buttons, server autocomplete
   — now actually message the user instead of raising `AttributeError` (#2).
4. `/bot` is registered from a cog rather than the global client (#3). Qualified names are
   byte-identical so the synced command tree should be unchanged, but this is the item most worth
   watching on first deploy.

## Post-refactor code review (2026-08-15)

A `/code-review high` pass over the full uncommitted diff found **four real defects introduced by
the Structural pass**, all since fixed. Recorded here because three of them were invisible to
compile checks and to the per-item verification that preceded them — they are cross-file
interaction bugs, not local mistakes.

1. **Critical — startup hang. `except AMP.AMPInitError` could never match** (`core/AMP_Handler.py`).
   `_instanceValidation(self, AMP: AMP.AMPInstance, ...)` took a parameter named `AMP`, shadowing
   the module-level `from core import AMP` for the entire function body. So the new `except
   AMP.AMPInitError` evaluated `.AMPInitError` on an `AMPInstance` → `AttributeError`. Worse, the
   startup call at `setup_AMPInstances()` is outside any `try`, so it propagated out of the AMP
   thread, `AMP_setup` never flipped to `True`, and `start.py`'s `while AMP_Handler.AMP_setup ==
   False` spun forever — the bot would hang at boot instead of skipping one bad instance.
   **Fixed** by renaming the parameter to `main_amp` (not `amp_instance` — that's already the loop
   variable inside) and updating all three call sites. A comment now records why the name matters.
2. **High — `/bot` subcommands could vanish, silently** (`cogs/banner_cog.py`, `regex_cog.py`,
   `whitelist_cog.py`). `/bot` used to be a module-level group registered at import time, so it
   always existed before any cog loaded. Now it only exists once `bot_cog.py` is loaded, but the
   three cogs calling `sub_command_handler('bot', ...)` declared no dependency on it, and
   `cog_auto_loader()` iterates `pathlib.iterdir()` (unordered — sorted on a fresh checkout,
   hash-ordered on ext4). On an unlucky ordering `get_command('bot')` returns `None`,
   `None.add_command(...)` raises, and `sub_command_handler`'s blanket `except Exception` logs and
   swallows it: the cog reports success while `/bot banner`, `/bot regex`, and `/bot whitelist`
   are missing from the tree. It didn't reproduce locally purely because `iterdir()` happens to
   yield `bot_cog.py` first on this machine. **Fixed** by adding `"bot_cog.py"` to all three
   `Dependencies` lists.
3. **Medium — the fix for #2 would have hung the bot without this** (`core/loader.py`). The
   `reload=True` skip removed `bot_cog.py` from the work list without appending it to
   `loaded_cogs`. The dependency branch `continue`s *without* removing an unsatisfied cog, and the
   enclosing `while len(cur_cog_file_list) > 0` only ends when the list empties — so the moment any
   cog declared `Dependencies = ["bot_cog.py"]`, `/bot cog reload` would spin forever inside
   `cog_auto_loader`, blocking the event loop. **Fixed** by marking it satisfied in the skip branch
   (it *is* still loaded — the skip declines to reload it, it doesn't unload it). Verified by
   simulating the loader against all real `Dependencies` decls over 3000 file orderings × both the
   load and reload paths: no hang, and `bot_cog.py` always precedes its three dependents.
4. **Low — autocomplete denials POSTed the wrong callback type** (`core/utils_permissions.py`).
   `_send_rolecheck_denial` sent every `discord.Interaction` a message (callback type 4), but
   `autocomplete_servers` passes an autocomplete interaction, which only accepts a choice list
   (type 8) → HTTP 400 per keystroke for a non-staff user under Default permissions. Not a
   regression (the old code raised `AttributeError` on the same path), but the fix for #2 in the
   `async_rolecheck` work had claimed to cover every caller shape and this was a third. **Fixed**
   by returning silently for `InteractionType.autocomplete`, so the caller just returns the
   narrowed choice list.

**Lesson for future refactor passes**: per-item verification caught local errors well, but every
one of these four is an *interaction* between a change and something outside the file it touched —
a shadowed module name, an import-time-vs-load-time ordering guarantee that quietly disappeared, a
loop invariant in a different module, and a caller shape nobody enumerated. Reviewing each
concern in isolation, however carefully, structurally cannot surface those; a whole-diff pass can.

What to exercise first on a real deployment, roughly in risk order: `/bot utils status` and
`/bot cog reload` (#3's re-registration and the self-unload guard), a whitelist button accept
(#4's extracted path plus #2's denial rendering), a permission denial as a non-staff user via both
a slash command and a button (#2), and a full restart with a game instance intentionally
misconfigured (#1's skip-and-continue).

Two follow-ups surfaced while clearing the Quick Wins, neither in the original audit — both now
handled:
- ~~Conflicting declared Python minimums~~ — **resolved**, all four declarations standardized on
  3.13 (see the `python_ver_check` item for the table and the resulting behavior change).
- **The next bot start will re-sync the Discord command tree**, as a normal consequence of the
  `Version` bump to `beta-4.11.0`. Informational only — no action needed.
