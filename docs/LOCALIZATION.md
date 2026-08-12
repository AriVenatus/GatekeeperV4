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
4. **Add it to the `/bot language` command** in `core/discordBot.py`, so admins can actually
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
