# AGENTS.md

## Project

LaraKit — zero-runtime-dependency Python library (>=3.9) of shared components for the Lara translation ecosystem. Published to PyPI with `dependencies = []`.

## Commands

```bash
python tests                      # run full test suite
python -m unittest tests.corpus.tmx  # single module
pylint src                        # lint (max-line-length=120, .pylintrc)
./version [major|minor|patch]     # bump, commit, tag (clean main only)
```

## Architecture & Conventions

- **Private-file, public-symbol pattern**: implementation lives in `_`-prefixed modules (e.g. `_core.py`, `_lang.py`, `_tmx.py`). Symbols are re-exported via `__init__.py` star-imports. Always import from `larakit` or `larakit.corpus`, never from `larakit._core` etc.
- **Version**: single-sourced in `src/larakit/__init__.py` as `__version__`, read dynamically by `pyproject.toml`.
- **Namespace private keys**: use `_set_private(key, value)` for underscore-prefixed attrs; `set()` rejects them.
- **Adding a language**: append to `Language._CODE_TO_NAME` in `src/larakit/_lang.py`.
- **Adding a corpus format**: create `src/larakit/corpus/_<fmt>.py` implementing `MultilingualCorpus`, `TUReader`, `TUWriter` ABCs from `_base.py`, then add `from ._<fmt> import *` in `corpus/__init__.py`.

## Testing

Tests live in `tests/` with discovery via `tests/__main__.py` (pattern `[!_]*.py`, recursive). `src/` is prepended to `sys.path` at runtime — no install needed. Test files mirror source structure (e.g. `tests/corpus/tmx.py` tests `larakit.corpus` TMX support).

## Key Types

| Class | Module | Purpose |
|-------|--------|---------|
| `Namespace` / `StatefulNamespace` | `larakit` | Dict-as-attrs; JSON-backed state with optional autosave |
| `Language` / `LanguageDirection` | `larakit` | BCP-47 parsing (`xx[-Script][-REGION]`); source→target pair |
| `MultilingualCorpus` | `larakit.corpus` | ABC: `reader()` → `TUReader`, `writer()` → `TUWriter` |
| `TranslationUnit` / `Properties` | `larakit.corpus` | TU with language direction + multi-value property map |

## Style

- Max line length: 120 chars.
- No runtime dependencies — stdlib only.
- pylint runs on `src/` only; tests are excluded from lint.

