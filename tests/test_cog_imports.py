#!/usr/bin/env python3
"""Import-time smoke test for every cog `core/loader.py` would load.

WHY THIS EXISTS
---------------
Python only raises a whole class of error when a module is *executed*, not when
it is compiled. `python -m py_compile` builds bytecode without running the class
body, so it cannot see any of this. Two production outages on 2026-08-15 were
exactly this shape:

  * `TypeError: Commands or listeners must not start with cog_ or bot_` --
    discord.py's `CogMeta.__new__` rejects reserved method-name prefixes. Raised
    at class creation, i.e. at import.
  * `AttributeError: 'AMPInstance' object has no attribute 'Initialized'` --
    an attribute read that happened before __init__ had set it up.

This test executes each cog's class body for real, with the heavy `core.*`
dependencies stubbed, so discord.py's decorators and metaclass run exactly as
they do at startup. It additionally validates command metadata against Discord's
hard limits using the REAL `locales/en.json` strings, so an over-long
description fails here rather than at `tree.sync()`. It separately checks
EVERY `locales/*.json` file's `commands.*` strings against the same limit --
a translation can overrun 100 chars even when the English source doesn't (a
German `whitelist_sync.channel.description` did exactly this on 2026-08-26,
only surfacing as a `CommandSyncFailure` in production since only en.json
was checked at import time).

Run:  python3 tests/test_cog_imports.py     (needs discord.py importable)
Exit: 0 on success, 1 on any failure.
"""
from __future__ import annotations

import importlib.abc
import importlib.util
import json
import pathlib
import sys
import types

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

DISCORD_DESC_MAX = 100  # Discord's limit for command/param descriptions and choice names.


class _Any:
    """Stands in for any object a cog pulls off a stubbed `core.*` module."""

    def __init__(self, *a, **k) -> None: ...
    def __getattr__(self, _name): return _Any()
    def __call__(self, *a, **k): return _Any()
    def __iter__(self): return iter(())
    def __getitem__(self, _item): return _Any()      # e.g. SomeStub[int]
    def __class_getitem__(cls, _item): return _Any()  # e.g. Union[..., StubType]


def _real_translate():
    """Use the actual en.json so description-length checks test real strings."""
    with open(REPO / 'locales' / 'en.json', encoding='utf-8') as fh:
        table = json.load(fh)

    def t(key: str, **kwargs) -> str:
        text = table.get(key, key)
        try:
            return text.format(**kwargs)
        except (KeyError, IndexError):
            return text
    return t


class _StubFinder(importlib.abc.MetaPathFinder, importlib.abc.Loader):
    """Fabricates any first-party module a cog imports, so only the cog itself is real."""

    ROOTS = ('core', 'modules', 'utils_dev')

    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] not in self.ROOTS:
            return None
        return importlib.util.spec_from_loader(fullname, self)

    def create_module(self, spec):
        mod = types.ModuleType(spec.name)
        if self._is_package(spec.name):
            # A package must resolve `from core import utils_permissions` by actually
            # importing the submodule (so its overrides below apply). A catch-all
            # __getattr__ here would hand back an _Any instead, and the cog would then
            # decorate with a non-callable -- which surfaces as a confusing
            # "Callback must be a coroutine" far from the real cause.
            mod.__path__ = []
            mod.__getattr__ = lambda name, _pkg=spec.name: importlib.import_module(f'{_pkg}.{name}')
        else:
            mod.__getattr__ = lambda _n: _Any()
        return mod

    @staticmethod
    def _is_package(fullname: str) -> bool:
        return (REPO / pathlib.Path(*fullname.split('.'))).is_dir()

    def exec_module(self, module) -> None:
        from discord.ext import commands
        name = module.__name__
        if name == 'core.i18n':
            module.t = _real_translate()
            module.t_plural = lambda base, count, **kw: module.t(f'{base}.other', **kw)
        elif name == 'core.utils_permissions':
            module.role_check = lambda: commands.check(lambda ctx: True)
            module.guild_check = lambda *a, **k: commands.check(lambda ctx: True)
        elif name == 'core.utils_discord':
            # Must be genuine coroutines with exactly 2 params: discord.py's
            # validate_auto_complete_callback enforces both at decoration time.
            async def _autocomplete(interaction, current):
                return []
            module.autocomplete_servers = _autocomplete
            module.autocomplete_servers_public = _autocomplete
        elif name == 'core.discordBot':
            module.Version = 'test'

        parent, _, child = name.rpartition('.')
        if parent and parent in sys.modules:
            setattr(sys.modules[parent], child, module)


def _check_locale_lengths() -> list[str]:
    """Every `commands.*` key (group/command/param descriptions, choice names) is
    subject to Discord's 100-char limit in EVERY locale, not just en.json -- a
    translation can overrun the limit even when the English source doesn't.
    """
    problems = []
    for locale_path in sorted((REPO / 'locales').glob('*.json')):
        with open(locale_path, encoding='utf-8') as fh:
            table = json.load(fh)
        for key, value in table.items():
            if key.startswith('commands.') and isinstance(value, str) and len(value) > DISCORD_DESC_MAX:
                problems.append(f'{locale_path.name}: {key!r} is {len(value)} chars (max {DISCORD_DESC_MAX})')
    return problems


def _check_metadata(module, path) -> list[str]:
    """Walk the commands the module defined and enforce Discord's limits."""
    from discord.ext import commands as ext_commands

    problems = []
    for cls in vars(module).values():
        if not (isinstance(cls, type) and issubclass(cls, ext_commands.Cog) and cls is not ext_commands.Cog):
            continue
        for attr, value in vars(cls).items():
            desc = getattr(value, 'description', None)
            if isinstance(desc, str) and len(desc) > DISCORD_DESC_MAX:
                problems.append(f'{path.name}:{cls.__name__}.{attr} description is {len(desc)} chars (max {DISCORD_DESC_MAX})')
            # discord.py raises on reserved prefixes itself, but assert it so the
            # rule is documented here rather than only living in a traceback.
            if isinstance(value, ext_commands.Command) and attr.startswith(('cog_', 'bot_')):
                problems.append(f'{path.name}:{cls.__name__}.{attr} uses a reserved cog_/bot_ prefix')
    return problems


def main() -> int:
    sys.meta_path.insert(0, _StubFinder())

    cogs = sorted((REPO / 'cogs').glob('*.py'))
    # core/loader.py loads EVERY .py in cogs/, so a stray copy (e.g. a sync tool's
    # "bot_cog 2.py") gets imported too and can crash startup with stale code.
    strays = [p for p in cogs if ' ' in p.name or p.stem.endswith(('copy', '2'))]

    failures, checked = [], 0
    for path in cogs:
        if path.name.startswith('__'):
            continue
        spec = importlib.util.spec_from_file_location(f'_cogtest_{path.stem}', path)
        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
        except Exception as exc:
            failures.append(f'{path.name}: {type(exc).__name__}: {exc}')
            print(f'  FAIL  {path.name}: {type(exc).__name__}: {exc}')
            continue
        problems = _check_metadata(module, path)
        failures.extend(problems)
        for p in problems:
            print(f'  FAIL  {p}')
        if not problems:
            print(f'  ok    {path.name}')
        checked += 1

    for stray in strays:
        failures.append(f'stray file in cogs/: {stray.name!r} -- loader.py imports every .py here')
        print(f'  FAIL  stray file in cogs/: {stray.name!r}')

    locale_problems = _check_locale_lengths()
    failures.extend(locale_problems)
    for p in locale_problems:
        print(f'  FAIL  {p}')

    print(f'\n{checked} cog(s) imported, {len(failures)} problem(s)')
    return 1 if failures else 0


if __name__ == '__main__':
    raise SystemExit(main())
