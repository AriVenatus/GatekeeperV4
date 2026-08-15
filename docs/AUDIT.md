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

- [ ] 10 unused packages in `requirements.txt`: `docopt`, `ffmpeg-python`, `future`, `GitPython`,
      `gitdb`, `smmap`, `nbtlib`, `pipreqs`, `yarg`, `imageio-ffmpeg` — none imported anywhere.
      (High confidence; looks like this file was generated via `pipreqs`/`pip freeze` from a dev
      venv.)
- [ ] Stale commented-out code in `core/AMP.py`: old `result['result'][...]`-wrapped return
      variants at lines ~784, 588-598, 915, and leftover `# print(...)` debug lines at ~546/558.
- [ ] Commented-out, non-functional call in `cogs/amp_tasks_cog.py:52` (references a method
      that isn't defined on that class).
- [ ] Three commented-out `DB_Update.py` migration helper calls, one of which references a
      method that doesn't exist anywhere (`user_MC_IngameName_unique_constraint`).
- [ ] `core/DB.py`'s `GetLog()` — unused **and** broken (selects `IngameName`/`UUID` columns
      that don't exist; actual columns are `MC_IngameName`/`MC_UUID`). Also unused:
      `dbServerConsoleSetup`, `GetAllUsers`.

### Doc fixes

- [ ] `core/discordBot.py:22` — `Version = 'beta-4.7.5'` is 4 changelog entries stale and is
      user-facing (surfaced via `/bot utils status`, and support workflows tell users to quote
      it).
- [ ] `docs/PERMISSIONS.md:164-166` — the "Full Permission Node List" is missing
      `server.console.interact`, even though the prose above it references that node as real and
      required.
- [ ] `core/AMP.py:894` — `getAMPUserInfo()` docstring references an `IdOnly` param that doesn't
      exist on the method.
- [ ] Update CLAUDE.md's dead-code note about `Banner_Editor_View` in `core/utils_ui.py` — that
      class no longer exists there at all (confirmed by direct read); the live banner editor is
      solely `utils_dev/banner_editor/`. The documentation itself is now stale.

### Small correctness-adjacent fixes (harmless today, worth tightening)

- [ ] `core/AMP.py:561` `_ADScheck()` and `:272` `check_GatekeeperRole_Permissions()` fall off
      the end returning implicit `None` in a failure branch instead of the `False` their own
      docstrings promise. Currently harmless (falsy in an `if`), but worth an explicit
      `return False`.
- [ ] `start.py:78` — `Setup.python_ver_check` is defined but **never called**. Not a delete
      candidate — looks like a startup guard that was wired up and then the call site got
      dropped. Decide: wire it back in, or remove if intentionally abandoned.

### Flag, don't auto-delete (needs judgment)

- [ ] `core/utils.py:135` — the entire `discordBot` helper class (`self.dBot`, 7 methods:
      `userAddRole`, `delMessage`, `sendMessage`, etc.) is instantiated in ~14 places but
      `self.dBot.<method>` has zero call sites anywhere. Big if true — worth a second look before
      deleting a whole class.
- [ ] 13 unused `AMPInstance` API-wrapper methods in `core/AMP.py` (`copyFile`, `getPermissions`,
      `getRole`, `trashFile`, ...) — medium confidence only, since a thin API wrapper class
      plausibly keeps a full surface on purpose.

## Structural Concerns (need a real decision, not a mechanical fix)

- [ ] **1. `AMPInstance.__init__` is a ~170-line god-constructor that calls `sys.exit(1)`
      directly, three times** (`core/AMP.py:54`). Mixes credential setup, dynamic `setattr()`
      injection from the API response, DB lookups, and a permission-bootstrap state machine.
      Constructing an object can kill the whole process as a side effect — an error-propagation
      redesign question, not a quick patch.
- [ ] **2. `async_rolecheck()` conflates three unrelated concerns** — caller-type sniffing, three
      separate permission backends, and sending the Discord error message itself
      (`core/utils.py:28`). Also carries an unresolved
      `#!TODO! Not sure which one triggers this` in security-relevant code.
- [ ] **3. The `/bot` command group bypasses the cog/loader pattern entirely** — ~15
      subcommands live as module-level functions on the global client
      (`core/discordBot.py:125`) instead of going through `core/loader.py` like every other
      command surface, so they're invisible to the bot's own `bot cog load/unload/reload`.
- [ ] **4. Business logic (DB writes, AMP calls, role assignment) lives directly inside Discord
      UI Button/View callbacks** in `core/utils_ui.py:145` (`Whitelist_view`,
      `Accept_Whitelist_Button`, `DB_Instance_ID_Swap`'s `Approve_Button`) — untestable without
      simulating a full Discord interaction.
- [ ] **5. Webhook get-or-create logic is duplicated near-identically across 3 task loops** in
      `cogs/amp_tasks_cog.py:98` — a contained, mechanical extraction if wanted.
- [ ] **6. `core/utils.py` bundles four unrelated systems** in one 694-line module: role-check
      decorators, Discord plumbing, a Mojang/Steam-API grab-bag, and the custom-permissions
      engine.

## Conflicts / Notes Between Subagents

- **CLAUDE.md's own documentation is now stale.** CLAUDE.md documents a `Banner_Editor_View`-
  related dead-code class living in `core/utils_ui.py`. The dead-code agent read the current
  file and confirmed that class **no longer exists there at all** — the live banner editor is
  solely `utils_dev/banner_editor/`. Not a codebase bug, but CLAUDE.md should be updated (see
  quick-wins doc fixes above).
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

Recommended starting order: Critical #2, #3, #4, #5 (concrete, high-confidence, isolated fixes),
then the `requirements.txt`/dead-code quick wins, before touching anything under Structural
Concerns.
