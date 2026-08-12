# Copyright (C) 2021-2022 Katelynn Cadwallader
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations
import json
import logging
import pathlib

from discord import app_commands

from core import DB

Handler = None

# Language codes only -- never numeric. `DBConfig.__getattribute__` auto-coerces any
# numeric-string config value to `int` on read, which would silently break an int-coded setting.
_SUPPORTED_LANGUAGES = ('en', 'de')
_LOCALES_DIR = pathlib.Path(__file__).parent.parent / 'locales'


class I18nHandler():
    """Loads locale files and resolves translation keys for the currently active global language."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        self.DBHandler = DB.getDBHandler()
        self.DBConfig = self.DBHandler.DBConfig

        self._locales: dict[str, dict[str, str]] = {lang: self._load_locale_file(lang) for lang in _SUPPORTED_LANGUAGES}

        stored = self.DBConfig.GetSetting('Language')
        if stored is not None and stored not in _SUPPORTED_LANGUAGES:
            self.logger.error(f'i18n: DBConfig "Language" setting was "{stored}", which is not a supported language; forcing "en".')
        self._language = stored if stored in _SUPPORTED_LANGUAGES else 'en'

    def _load_locale_file(self, lang: str) -> dict[str, str]:
        path = _LOCALES_DIR / f'{lang}.json'
        try:
            return json.loads(path.read_text(encoding='utf-8'))
        except FileNotFoundError:
            self.logger.error(f'i18n: locale file missing: {path}')
            return {}
        except json.JSONDecodeError as e:
            self.logger.error(f'i18n: locale file {path} is malformed JSON: {e}')
            return {}

    def get_language(self) -> str:
        return self._language

    def set_language(self, lang: str) -> None:
        if lang not in _SUPPORTED_LANGUAGES:
            raise ValueError(f'Unsupported language "{lang}", must be one of {_SUPPORTED_LANGUAGES}')
        self._language = lang
        self.DBConfig.SetSetting('Language', lang)

    def t(self, key: str, **kwargs) -> str:
        value = self._locales.get(self._language, {}).get(key)
        if value is None:
            value = self._locales.get('en', {}).get(key)
            if value is not None and self._language != 'en':
                self.logger.warning(f'i18n: key "{key}" missing for "{self._language}", falling back to English.')
        if value is None:
            self.logger.warning(f'i18n: key "{key}" missing from every locale file; returning the raw key.')
            return key

        if not kwargs:
            return value

        try:
            return value.format(**kwargs)
        except (KeyError, IndexError, ValueError) as e:
            self.logger.error(f'i18n: key "{key}" failed to .format(**{kwargs!r}): {e}; returning it unformatted.')
            return value

    def t_plural(self, key_base: str, count: int, **kwargs) -> str:
        suffix = 'one' if count == 1 else 'other'
        return self.t(f'{key_base}.{suffix}', count=count, **kwargs)

    def _command_key_base(self, cmd) -> str:
        return 'commands.' + cmd.qualified_name.replace(' ', '.')

    def _apply(self, current: str, key: str, max_len: int, stats: dict) -> str:
        target = self._locales.get(self._language, {}).get(key)
        if target is None:
            en = self._locales.get('en', {}).get(key)
            if en is None:
                # Not migrated to i18n at all yet -- expected/normal during the phased rollout.
                return current
            self.logger.warning(f'i18n resync: "{key}" missing for "{self._language}"; using English.')
            target = en
            stats['skipped'] += 1

        if not (1 <= len(target) <= max_len):
            self.logger.error(
                f'i18n resync: "{key}" is {len(target)} chars (Discord limit {max_len}); '
                f'ignoring it and keeping the previous text so tree.sync() does not fail entirely.'
            )
            stats['skipped'] += 1
            return current

        stats['updated'] += 1
        return target

    def retranslate_command_tree(self, client) -> tuple[int, int]:
        """Re-derives each command/param/choice's locale key from its live `qualified_name` and
        re-applies the CURRENT language's text in place. Call AFTER set_language() and BEFORE
        `tree.copy_global_to()` + `tree.sync()` -- those read straight off the objects mutated here.

        Walks two trees since every command in this repo is a hybrid command: `client.tree` (the
        app_commands tree Discord's UI reads and `tree.sync()` publishes) and `client` itself
        (the bot's own prefix-command tree, read by `$help`) -- for hybrid commands the two share
        the same `qualified_name`, so the same derived key applies to both.
        """
        stats = {'updated': 0, 'skipped': 0}

        for cmd in client.tree.walk_commands():
            base = self._command_key_base(cmd)
            cmd.description = self._apply(cmd.description, f'{base}.description', 100, stats)

            # Groups (e.g. the `user` in `/user info`) don't take parameters -- only leaf
            # Commands do. Nothing to translate here, and nothing to warn about.
            if isinstance(cmd, app_commands.Group):
                continue

            # NOTE: `Command._params` is a private/undocumented discord.py attribute (verified
            # against discord.py==2.4.0's actual source -- `to_dict()` reads it fresh, so mutating
            # it here before `tree.sync()` takes effect). Re-verify this still exists and is still
            # a Dict[str, CommandParameter] with a mutable `.description` before bumping discord.py
            # past 2.4.0. Guarded defensively so a rename/removal only skips retranslating this
            # command's params/choices (logged) instead of crashing the whole switch.
            params = getattr(cmd, '_params', None)
            if params is None:
                self.logger.warning(f'i18n resync: {base} has no `_params`; skipping its params/choices.')
                continue

            for pname, pobj in params.items():
                pobj.description = self._apply(pobj.description, f'{base}.params.{pname}.description', 100, stats)
                for choice in (pobj.choices or []):
                    # Only ever mutate `.name` (the display label). NEVER `.value` -- it's a
                    # program-logic sentinel compared elsewhere (`if permission.value == 0`, etc.);
                    # translating it would silently break every such comparison downstream.
                    choice.name = self._apply(choice.name, f'{base}.params.{pname}.choices.{choice.value}', 100, stats)

        for cmd in client.walk_commands():
            base = self._command_key_base(cmd)
            cmd.description = self._apply(cmd.description, f'{base}.description', 100, stats)

        return stats['updated'], stats['skipped']


def getI18nHandler() -> I18nHandler:
    global Handler
    if Handler == None:
        Handler = I18nHandler()
    return Handler


# Module-level convenience wrappers so call sites can just `import i18n; i18n.t(...)`.
def t(key: str, **kwargs) -> str:
    return getI18nHandler().t(key, **kwargs)


def t_plural(key_base: str, count: int, **kwargs) -> str:
    return getI18nHandler().t_plural(key_base, count, **kwargs)


def set_language(lang: str) -> None:
    getI18nHandler().set_language(lang)


def get_language() -> str:
    return getI18nHandler().get_language()


def retranslate_command_tree(client) -> tuple[int, int]:
    return getI18nHandler().retranslate_command_tree(client)
