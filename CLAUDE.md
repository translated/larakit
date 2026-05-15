# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

LaraKit is a zero-runtime-dependency Python library (Python >= 3.9) of shared components used across the Lara translation ecosystem. It is published to PyPI; production runtime deps are intentionally empty (`pyproject.toml` `dependencies = []`). `requirements.txt` contains only dev/build tooling.

## Common commands

```bash
pip install -r requirements.txt   # dev/build tooling (pre-commit, pylint, build, twine)
pre-commit install                # set up lint hook
pylint src                        # lint (max-line-length=120, see .pylintrc)
python tests                      # run full test suite (invokes tests/__main__.py)
python -m unittest tests.corpus.tmx           # run a single test module
python -m unittest tests.corpus.tmx.TestClass # single class/test
./version [major|minor|patch]     # bump __version__, commit, tag (must be clean main)
```

`tests/__main__.py` prepends `src/` to `sys.path` and discovers test files matching `[!_]*.py` recursively. The pre-commit hook runs pylint on `src/` only (tests excluded).

## Architecture

Public API is exposed via star-imports in `src/larakit/__init__.py` (re-exports `_core` + `_lang`) and `src/larakit/corpus/__init__.py` (re-exports all `_*` submodules). Files prefixed with `_` are implementation modules; the convention is "private filename, public symbols via star-import." Don't import from `larakit._core` etc. directly in new code — import from `larakit` / `larakit.corpus`.

Key modules:

- `_core.py` — `Namespace` (dict-as-attrs with recursive dict/list parsing; private keys must start with `_` and use `_set_private`) and `StatefulNamespace` (JSON-backed, optional autosave on every `set`).
- `_lang.py` — `Language` (BCP-47-ish parser: code/script/region from `xx[-Script][-REGION]`) and `LanguageDirection` (source→target pair, with lazy `reversed`). `Language._CODE_TO_NAME` is the canonical code→display-name table — extend it when adding language support.
- `corpus/_base.py` — abstract `MultilingualCorpus` with `reader()`/`writer()`/`__len__`/`properties`, plus `TranslationUnit`, `Properties` (multi-value map: `put` upgrades scalar→list on collision), `TUReader`/`TUWriter` context-manager ABCs. `_jtm.py`, `_tmx.py`, `_parallel.py` are concrete corpus formats — new formats follow the same pattern and must be re-exported from `corpus/__init__.py`.
- `pipeline.py` — `mp_apply` / `mp_stream` multiprocessing helpers (queue-fed pool, ordered or streaming), plus pipeline scaffolding using `StatefulNamespace` for checkpointing.
- `shell.py` — `shexec` subprocess wrapper raising `ShellError` on non-zero exit.
- `progressbar.py` — terminal progress bar; uses a daemon Timer (see commit 6837d97 — non-daemon Timer previously blocked interpreter shutdown).
- `math.py` — `Sequence` running mean/variance accumulator.

Version is single-sourced in `src/larakit/__init__.py` as `__version__` and consumed dynamically by `pyproject.toml` via `[tool.setuptools.dynamic]`. The `./version` script enforces clean tree + main branch before bumping and tagging.
