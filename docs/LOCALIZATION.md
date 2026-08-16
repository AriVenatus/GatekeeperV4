# **Adding a Language**

Gatekeeper's localization (`core/i18n.py`) is a flat key -> text lookup, so adding a new language
is mostly translation work, not code work.

## How it works

- `locales/en.json` and `locales/de.json` are flat `"dotted.key": "text"` maps (no nesting).
- `i18n.t(key, **kwargs)` looks up `key` in the active language, falls back to English, then
  falls back to the raw key — it never raises, so a missing translation degrades gracefully.
- The active language is a single **global** setting (not per-user), switchable at runtime via
  `/bot language`, and persisted in the database.

## Steps

1. **Copy the template.** Duplicate `locales/en.json` as `locales/<code>.json` (e.g.
   `locales/fr.json`), using a two-letter language code.
2. **Translate every value, keep every key identical.** Only touch the text on the right-hand
   side of each `"key": "text"` pair — the keys themselves must stay byte-identical to
   `en.json`, and every key that exists in `en.json` should exist in your new file too (a
   missing key just silently falls back to English, but that's not what you want for a
   complete translation).
3. **Register the language code** by adding it to `_SUPPORTED_LANGUAGES` in `core/i18n.py`:
   ```python
   _SUPPORTED_LANGUAGES = ('en', 'de', 'fr')
   ```
4. **Add it to the `/bot language` command** in `cogs/bot_cog.py`, so admins can actually
   pick it:
   ```python
   @app_commands.choices(language=[Choice(name='English', value='en'), Choice(name='Deutsch', value='de'), Choice(name='Français', value='fr')])
   ```
5. **Restart the bot**, then switch to the new language with `/bot language` and click through
   the commands/messages you translated to sanity-check them in context.

## Things to watch for

- **Discord's 100-character limit**: command/parameter descriptions and choice names can't
  exceed 100 characters. `retranslate_command_tree()` skips (logs a warning, keeps the old
  text) any translated string over that limit rather than letting it break `tree.sync()` —
  keep translated command/param text under 100 characters.
- **Never translate a `Choice.value`, only its `.name`.** Values are compared in business
  logic (e.g. `if permission.value == 0`) and must stay identical across every language.
- **Language codes must stay letters, never digits** (`en`/`de`/`fr`, not `1`/`2`) — numeric
  strings stored in the database's generic settings table get auto-coerced to `int` on read,
  which would silently break the stored `Language` setting.
- **A key-by-key translation pass alone won't catch everything.** Length/key-parity checks
  are automated, but grammar, natural phrasing, and sentences built by interpolating one
  translated fragment into another (e.g. a composed confirmation message) need a manual
  read-through — it's easy for a technically-correct translation to still read stiff, or for
  a composed sentence to not agree in number/case even when each fragment is fine on its own.

## Key naming (for anything you add later, not for translating existing keys)

If you ever add brand-new translatable strings (not just translating this guide's existing
`en.json`/`de.json` keys into a third language), keys follow one of two schemes:
- **Command metadata** is derived mechanically from the command's own `qualified_name`:
  `commands.<qualified_name with spaces→dots>.description`,
  `...params.<name>.description`, `...params.<name>.choices.<choice.value>`.
- **Everything else** is hand-namespaced: `common.*` (shared across multiple files),
  `messages.<area>.*`, `embeds.<function>.*`, `ui.<component>.*`.

One nuance worth keeping in mind for `common.*`: a key only belongs there if it's genuinely
shared across ≥2 files, verified by grep before merging — don't blindly dedupe two strings that
merely happen to read the same today.

---

# Implementation history & lessons learned

Moved here from `CLAUDE.md` on 2026-08-15 to keep that always-loaded file focused on guidance
that applies to every session — the same treatment the deployment history got in
[`DEPLOYMENT_LOG.md`](DEPLOYMENT_LOG.md). Read this before starting new localization work; it's
a record of what previous passes found, not something you need loaded to write ordinary code.

## Coverage — what is and isn't translated

`core/discordBot.py`, `core/utils_permissions.py`, `core/utils_embeds.py`, `core/utils_ui.py`,
`utils_dev/banner_editor/*` (the **only** banner editor UI — `Banner_Editor_View` lives in
`utils_dev/banner_editor/ui/view.py` and is imported live by `cogs/banner_cog.py`. An earlier
note claimed `core/utils_ui.py` held a parallel dead-code copy; verified 2026-08-15 that it does
not — `core/utils_ui.py` contains only the server-control/whitelist/link/instance-swap views, no
banner-editor classes at all), and all of `cogs/*.py` except `amp_tasks_cog.py`.

Deliberately **not** translated:
- `amp_tasks_cog.py`'s console/chat/event webhook relay — raw AMP/game text, not authored UI
  copy. Also its webhook display names are a stored identity key matched by exact string
  equality across restarts, so translating them would orphan/duplicate webhooks.
- Admin-authored custom whitelist-reply templates stored in the DB
  (`DB.GetAllWhitelistReplies()`) — user content, not source strings.

`modules/*/cog_<game>.py` currently register zero commands (pure boilerplate), so there was
nothing to translate there — if a future game module gains real slash commands, they need the
same `i18n.t()` treatment as `cogs/*.py`.

## Bugs surfaced while translating

Translating text surfaced a few real (non-translation) bugs, fixed in the same pass:
- `context.sned(...)` typo in `core/discordBot.py`.
- `amp_server_cog.py`'s `/server status` referenced `amp_server.InstanceName` on a variable just
  checked `== None`.
- `core/utils_ui.py`'s `ServerButton` derived its AMP permission node (`server.start`/`.stop`/
  etc., checked against `bot_perms.json`) from the *display label* — translating "Start" to
  "Starten" would have silently broken that permission check. Now decoupled via an explicit
  `action` param.

## Full text-quality audit (2026-08-09)

Beyond translation coverage, a line-by-line pass over all 457 keys in both `locales/en.json` and
`locales/de.json`, checking grammar/accuracy rather than just presence. Recurring bug classes
found and fixed:
- Missing English possessive apostrophes (`a Users...` → `a User's...`).
- An anglicism verb wrongly inflected as English past tense instead of German
  (`Synced` → `Synchronisiert`).
- Missing hyphens in German compounds
  (`Gatekeeper Neustart-Funktion` → `Gatekeeper-Neustart-Funktion`).
- A wrong German noun gender/case (`das Server-Avatar` → `den Server-Avatar` — `Avatar` is
  masculine).
- An untranslated phrase left mid-German-sentence (`Server Console` → `Server-Konsole`).
- Comma splices rewritten in both languages, plus plain typos/formatting slips (`seperator`, a
  missing space before a parenthesis, a wrong preposition).

None of this is caught by length/key-parity validation alone — worth an occasional manual
read-through, not just automated checks, especially after adding a batch of new keys.

## German naturalness pass (2026-08-09)

The audit above checked grammar/accuracy; this pass instead targeted *phrasing that reads as a
stiff, calque-y translation* even though each sentence was individually grammatical — flagged by
a user screenshot of `/bot bannergroup remove`'s confirmation ending mid-sentence ("Sieht so aus,
als hätten wir gerade entfernt"). Two classes of fix:

**1. Systemic phrasing.** German has ~20 messages translating English's "Looks like X" via
`"Es sieht so aus, als [Konjunktiv II]..."` — grammatically valid but reads as hedging/uncertain
in German (unlike the casual-idiomatic English source) and gets clunkier the longer the sentence.
Replaced with the idiomatic patterns already used correctly elsewhere in the same file:
`anscheinend`/`scheint … zu` instead of the full subordinate clause. Same principle applied to a
few sibling English-source constructs where a direct statement read more naturally than a hedge
paired with an exclamation mark (e.g. `messages.banner.settings.type.images`).

**2. Composition bugs** (the actual root causes, not just wording):
- `and_part` in `cogs/banner_cog.py`'s three banner-group message builders was hardcoded to the
  **English literal** `' and '` regardless of active language — a stray English word bleeding
  into German sentences. Moved to a new shared key `common.and_joiner` (`" and "` EN /
  `" und "` DE), added to both locale files.
- `/bot bannergroup remove` had no `need_selection` guard (unlike `/bot bannergroup add`, which
  has one) — calling it with neither `server` nor `channel` silently "succeeded" with all three
  interpolated parts empty, which is exactly the screenshot's cause. Added the missing guard
  (new key `messages.banner.group.remove.need_selection`, mirroring `add`'s).
- `messages.bot.utils.message_timeout.result`'s German fragments composed into a broken
  sentence — `{content_str}` (`"wird nach {time} Sekunden gelöscht"`) plus the wrapper's own
  trailing `" nach dem Senden."` produced a duplicated
  `"... nach {time} Sekunden gelöscht nach dem Senden."`, and `wird` didn't agree in number with
  the plural `Ephemere Nachrichten`. Moved `"nach dem Senden"` fully into the two `content_str`
  variants (now `werden …`) and simplified the wrapper to just `"{content_str}."`.
- `messages.whitelist_request.need_ign_reason` is only ever consumed as a lowercase mid-sentence
  fragment of `cannot_handle` (`"Ich kann deine Anfrage nicht bearbeiten, {reason}"`), but was
  itself a full capitalized sentence (`"Ich brauche deinen **IGN**, ..."`) — producing a
  mid-sentence capital "Ich" and a redundant repeated clause. Rewritten as a proper lowercase
  fragment (`"mir fehlt noch dein **IGN**."`).

**General lesson**: whenever a locale string is built by interpolating one `i18n.t(...)` result
into another (`content_str`, `reason`, `and_part`, etc.), check the *composed* sentence, not each
fragment in isolation — grammar/casing/agreement bugs only show up in the concatenation, and a
hardcoded literal in the composing Python code silently defeats localization even when both JSON
files are correct.
