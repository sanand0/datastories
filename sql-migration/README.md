# SQL Migration Narrative Demo (MSSQL -> MySQL)

This repo is a client-facing interactive demo that explains how LLMs + coding agents can migrate SQL Server workloads to MySQL with traceability, verification, and business context.

The demo is a single-page app (`index.html`) with:

- an animated workload map of 100 scripts (Act 1)
- migration risk/problem framing (Act 2)
- a six-step conversion pipeline with animated SVG cards (Act 3)
- script-level source/target examples with mappings and highlights (Act 4)
- a business-impact simulator (Act 5)
- caveats and controls (Act 6)

## What Dataset Is Included

The live story uses only these runtime files:

- `index.html`
- `styles.css`
- `app.js`
- `demo-data.js`
- `script-sql-data.js`

All non-runtime generation/reference assets were archived (max compression) to keep the repo lightweight.

Archive file:

- `data.tar.xz` (created with `XZ_OPT='-9e'`)

Archived content includes:

- `docs/`
- `harness/`
- `logs/`
- `schema/`
- `scripts/`
- `demo-data.json`
- `manifest.json`
- `prompts.md`

## How It Was Generated (from `prompts.md`)

The generation happened in two phases:

1. **Synthetic data generation prompt**
   - Requested ~100 MSSQL scripts of varying complexity
   - Requested MySQL conversions for each script
   - Requested month-long realistic telemetry (execution frequency, runtime, actors, metadata)
   - Requested migration-related supporting files for demo storytelling

2. **Interactive visualization/build prompt**
   - Used the generated dataset to build this SPA narrative demo
   - Added iterative edits: click-through script modal with source/target/diff, syntax highlighting, mapping-driven code highlighting, additional examples, and Act flow adjustments

In short: the dataset is synthetic; the demo app is built on top of it to communicate migration process, risks, and business impact. The raw generation/reference artifacts are now in the archive file above.

## How The Demo Functions

The app is static (no backend):

- `index.html` + `styles.css` + `app.js` render the experience.
- `demo-data.js` contains precomputed structured data used by visualizations/simulator.
- `script-sql-data.js` contains full source/target SQL text used by Act 1 modal (metadata + code + side-by-side diff).
- Highlighting/fonts are loaded via CDN.

## Restoring Archived Assets (optional)

If you need the generation logs, schema, or raw script pack back in place:

```bash
cd /home/sanand/code/datastories/sql-migration
tar -xJf data.tar.xz
```

User interactions drive most of the narrative:

- Act 1 mode toggles redraw groupings and update query/hotspot summaries.
- Clicking any script node opens a rich modal (metadata, MSSQL, MySQL, diff).
- Act 4 mapping hover highlights relevant lines in source/target snippets.
- Act 5 sliders recompute modeled business outcomes live.

## Setup

### Prerequisites

- Modern browser
- Internet access (for CDN font + highlight assets)
- Node.js (for easy local static hosting via `npx`)

### Run

```bash
cd /home/vscode/code/sql-migration
npx --yes serve . --listen 4173
```

Then open:

```text
http://localhost:4173
```

Stop the server with `Ctrl+C`.

## Key Files

- App entry: `index.html`
- Interaction logic: `app.js`
- Styling: `styles.css`
- Aggregated demo payload: `demo-data.js`
- Full per-script SQL payload: `script-sql-data.js`
- Archived generation/reference pack: `data.tar.xz`

Generated dataset timestamp: `2026-02-27T07:59:59Z`
