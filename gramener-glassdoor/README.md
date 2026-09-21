# Gramener Glassdoor dossier

This directory contains a small, evidence-preserving data story about Gramener on Glassdoor:

- [`index.html`](index.html) renders the dossier in the browser.
- [`glassdoor.json`](glassdoor.json) is the generated data consumed by the page.
- [`cache/`](cache/) stores authenticated HTML and first-party API responses used to build the JSON.
- [`prompts.md`](prompts.md) records the original extraction and page-building requirements.

The data is employee-submitted and self-reported. It is not an audited company dataset.

## View the page

Because the page uses `fetch("glassdoor.json")`, serve this directory over HTTP rather than opening `index.html` directly:

```bash
uv run --with lxml python -m http.server 8000
```

Then open <http://localhost:8000/>.

The page is data-driven: rebuilding `glassdoor.json` updates the displayed content without changing `index.html`.

## Update the data

The normal updater is [`update_glassdoor.py`](update_glassdoor.py). It uses the authenticated browser already exposed through CDP at `localhost:9222`.

1. Start the browser with remote debugging on port 9222.
2. Log in to Glassdoor in that browser. Employer Centre access is needed for the employer-side review fields.
3. From this directory, run:

   ```bash
   uv run update_glassdoor.py
   ```

The updater captures overview, pay/benefits, review, and interview pages; refreshes review and salary API responses; and atomically rebuilds `glassdoor.json` from the cache.

Each capture/API request is checkpointed in `cache/update-state.json`. If the process stops, resume the run using the printed run ID:

```bash
uv run update_glassdoor.py --resume RUN_ID
```

Useful options:

```bash
# Show planned work without opening the browser or writing files
uv run update_glassdoor.py --dry-run

# Rebuild glassdoor.json from the existing cache only
uv run update_glassdoor.py --skip-capture --skip-api

# Refresh browser pages but keep the existing API cache
uv run update_glassdoor.py --skip-api

# Refresh APIs but keep the existing page cache
uv run update_glassdoor.py --skip-capture
```

The updater writes temporary files and renames them into place, so an interrupted write should leave the previous cache file or `glassdoor.json` intact. It also keeps older cache inputs when Glassdoor returns a page shell without the structured payload required by the extractor.

## How the pipeline works

The stages can also be run individually when debugging:

- [`capture_glassdoor.py`](capture_glassdoor.py) opens a CDP tab, visits authenticated Glassdoor pages, expands relevant content, and saves HTML plus capture metadata.
- [`fetch_glassdoor_api.py`](fetch_glassdoor_api.py) calls the public first-party review and salary endpoints through the logged-in browser and saves JSON responses.
- [`extract_glassdoor.py`](extract_glassdoor.py) merges cached sources into the stable `glassdoor.json` schema.

The updater is preferred because it coordinates these stages, records checkpoints, supports resume, and performs the final atomic rebuild.

Some historical inputs are deliberately retained in the cache:

- `cache/interviews-recon/` contains the reconciled interview API data currently used for interview records.
- `cache/pages/benefit-details/` contains the per-benefit pages currently used for detailed benefit records.
- `cache/recon-review-api/` contains request/query samples and the public review summary fallback.

Do not delete or replace these inputs casually. The extractor may still depend on them even after a new browser capture succeeds.

## Test and validate

Run the focused test suite after changing the extractor or updater:

```bash
uv run --with lxml pytest -q
```

The tests check record counts and uniqueness, representative merged fields, serializability, and absence of authentication material. A useful manual check after an update is:

```bash
uv run --with lxml python - <<'PY'
import json
from pathlib import Path

data = json.loads(Path("glassdoor.json").read_text())
reviews = data["reviews"]["items"]
print("extracted_at:", data["extraction_metadata"]["extracted_at"])
print("reviews:", len(reviews), "unique IDs:", len({r["reviewId"] for r in reviews}))
print("interviews:", len(data["interviews"]["items"]))
print("salary estimates:", len(data["pay_and_benefits"]["salary_estimates"]))
PY
```

Repeated rebuilds should not duplicate records. The extraction timestamp is expected to change on each successful rebuild; the underlying records should remain stable when the cache has not changed.

## Maintenance notes

- Treat `glassdoor.json` as generated output. Change the extractor or its cached sources rather than hand-editing it.
- Preserve existing cache files when a live page is blocked, partially hydrated, or changes markup. Inspect the raw capture before changing selectors.
- Glassdoor selectors, endpoints, page limits, and response shapes can change. Update the capture/API code and regression tests together.
- If the employer portal is unavailable, the updater can still refresh public reviews and salaries, but it preserves the previous employer-side API cache.
- Avoid committing credentials, browser debugging URLs, cookies, CSRF tokens, or other session material. The extractor test explicitly checks for several common secrets.
- `screenshot.avif` is a compressed preview asset for the surrounding datastories site; regenerate it only when the page design changes.
