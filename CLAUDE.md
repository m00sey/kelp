# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

KELP (Key Event Log Parser) — a FastAPI web UI for browsing KERI Key Event Logs. Loads events from OOBI endpoints or CESR files, parses them with keripy, and displays them in a multi-tab browser interface.

## Commands

```bash
uv sync                  # Install dependencies
make run                 # Dev server with auto-reload on 0.0.0.0:8000
uv run kelp              # Run server on 127.0.0.1:8000
uv run ruff check src    # Lint
uv run ruff format src   # Format
make build               # Docker image
```

Ruff config: line-length 100, double quotes, Python 3.11+ target.

## Architecture

Three modules under `src/kelp/`:

- **cesr/** — CESR stream parsing. `CESRParser` uses keripy (`Serder`, `Counter`, `Siger`, `Matter`) to parse binary CESR streams into `Event` and `Attachment` dataclasses.
- **sources/** — Data source abstraction. `DataSource` base class with `OOBISource` (HTTP via httpx) and `FileSource` (local CESR files). `LMDBSource` is a placeholder.
- **web/** — FastAPI app created via `create_app()` factory in `main.py`. All state is in-memory (`AppState`/`TabState` dataclasses). Uses Jinja2 templates with HTMX for interactivity.

Data flow: Source → `CESRParser.parse()` → `Event` objects → `TabState` → Jinja2 templates via HTMX partial swaps.

## Web app details

- `web/main.py` contains all endpoints and app state — it's the central file.
- HTMX OOB swaps update the tab bar when loading data. The partial `main_content_with_tab_bar.html` includes an OOB-swapped `#tab-bar` alongside `main_content.html`.
- `tab_content.html` is used for full `#tab-content` replacements (tab switch/close); it includes `tab_bar.html`.
- Share links use `?kel=<encoded_url>` query params (repeatable for multi-tab witness pools).
- jq filtering shells out to the `jq` binary — it must be installed on the system.
- Static assets use cache-busting via git commit hash (`cache_version` template var).

## External dependencies

- **keri** (keripy) — KERI cryptographic library, provides Serder/Counter/Siger/Matter for CESR parsing
- **jq** binary — required at runtime for event filtering (not a Python package)
- **libsodium** — required by keri (system library)
