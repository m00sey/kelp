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

## Brand

Brand tokens come from the shared `@m00sey/gleif-brand` package
(GitLab: `gitlab.vroblok.io/m00sey/gleif-brand`), imported in
`src/main.ts` as `@m00sey/gleif-brand/tokens.css` **before** the
site stylesheet. See `node_modules/@m00sey/gleif-brand/BRAND.md`
for source, status, and usage notes.

**What the package provides:**

- Palette — `--gleif-cyprus`, `--gleif-turquoise`, `--gleif-jade`,
  `--gleif-spring`, `--gleif-fern`, `--gleif-honey`, `--gleif-amber`,
  `--gleif-lava`, `--gleif-azure`, `--gleif-smoke`, and more
- Semantic aliases — `--color-bg`, `--color-surface`, `--color-text`,
  `--color-text-muted`, `--color-text-inverse`, `--color-accent`,
  `--color-accent-deep` (fern), `--color-accent-mid` (jade),
  `--color-link`, `--color-link-hover`
- Typography — `--font-sans` (Facundo → Calibri → system-ui),
  `--font-weight-*`, `--line-height-heading` (110%),
  `--line-height-body` (140%), `--font-size-h1..h4`,
  `--font-size-body`, `--font-size-sm`
- Utility classes — `.bg-gradient-cyprus-turquoise`,
  `.bg-gradient-spring-turquoise`, `.bg-gradient-fern-turquoise`,
  `.bg-gradient-cyprus-spring`, `.surface-inverse`

**Rules for this site (and the rest of the GLEIF mini-site suite):**

1. **No hardcoded hexes or font stacks** in site CSS or in JS that
   styles the DOM (e.g. Cytoscape stylesheets). Read CSS variables
   via `getComputedStyle(document.documentElement).getPropertyValue(name)`
   when you need the value in JS.
2. **Light only.** The GLEIF deck has no dark-mode spec. Do not add
   a dark theme, theme toggle, or `.light`/`.dark` class branching.
3. **Tinted backgrounds** use `color-mix(in srgb, var(--gleif-X) N%,
   transparent)` rather than rgba with duplicated hex values.
4. **Data-viz fills** (node colors, chart series) come from the
   Detail palette — brand explicitly designates it for charts and
   small accents. Credential nodes in this site use a Core pairing:
   turquoise fill, cyprus border.
5. **Saturated brand fills** (toast backgrounds, banners with white
   text) prefer raw brand tokens (`--gleif-fern`, `--gleif-lava`,
   `--gleif-azure`) over AA-contrast neighbours — AA neighbours are
   for colored text on a light surface, not the other way around.
6. **Flag unmapped values** with an inline `FLAG:` comment so future
   brand updates are easy to find. The brand deck does not cover:
   component specs (border radii, shadows), spacing scale, a mono
   stack, surface layering for hover/active states, or a "success
   green" (spring is a mint, not a success signal).

**Site-specific layer** lives in `src/app.css` — it holds `--radius`,
`--font-mono`, `--color-surface-2/3`, `--color-border`, the state
colors (`--color-success/warning/error/info`, with `FLAG:` notes on
the ones that don't map), and component rules for buttons, inputs,
badges, alerts, nav, drawer, etc. Keep this layer thin and flag
anything brand-adjacent.
