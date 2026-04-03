#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "httpx>=0.28",
#   "orjson>=3.10",
#   "rich>=14.0",
#   "tenacity>=9.1",
#   "typer>=0.16",
# ]
# ///

from __future__ import annotations

from pathlib import Path
import shutil

import httpx
from rich.traceback import install
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential
import typer

from tds_p1_common import (
    HISTORY_PAGES_DIR,
    HISTORY_URL,
    LOCAL_DUMP_PATH,
    QUIZ_ID,
    RAW_DIR,
    ensure_dir,
    load_rows_from_payload,
    read_json,
    write_json,
)

install(show_locals=True)

app = typer.Typer(add_completion=False)


@retry(
    retry=retry_if_exception_type(httpx.HTTPError),
    stop=stop_after_attempt(4),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    reraise=True,
)
def fetch_page(client: httpx.Client, page: int, *, limit: int, history: bool, positives: bool = False) -> dict:
    params = {
        "quiz": QUIZ_ID,
        "email": "",
        "until": "",
        "limit": limit,
        "page": page,
    }
    if history:
        params["history"] = 1
    if positives:
        params["positives"] = 1
    response = client.get(
        HISTORY_URL,
        params=params,
    )
    response.raise_for_status()
    return response.json()


def save_local_snapshot(force: bool) -> dict[str, int | bool]:
    destination = RAW_DIR / "local-dump.json"
    if LOCAL_DUMP_PATH.exists() and (force or not destination.exists()):
        ensure_dir(destination.parent)
        shutil.copy2(LOCAL_DUMP_PATH, destination)
    if not destination.exists():
        return {"exists": False, "rows": 0}
    rows = load_rows_from_payload(read_json(destination))
    return {"exists": True, "rows": len(rows)}


@app.command()
def main(limit: int = 2000, force: bool = False) -> None:
    """Download the canonical paginated history feed and supporting snapshots."""

    ensure_dir(HISTORY_PAGES_DIR)
    ensure_dir(RAW_DIR)
    total_rows = 0
    pages = 0

    with httpx.Client(timeout=60, follow_redirects=True, headers={"User-Agent": "tds-p1-analysis"}) as client:
        page = 0
        while True:
            path = HISTORY_PAGES_DIR / f"page-{page:04d}.json"
            if path.exists() and not force:
                payload = read_json(path)
            else:
                typer.echo(f"[history] fetching page {page}")
                payload = fetch_page(client, page, limit=limit, history=True)
                write_json(path, payload)
            rows = load_rows_from_payload(payload)
            row_count = len(rows)
            typer.echo(f"[history] page {page}: {row_count} rows")
            total_rows += row_count
            pages += 1
            if row_count < limit:
                break
            page += 1

        latest_all = fetch_page(client, 0, limit=2000, history=False)
        latest_positive = fetch_page(client, 0, limit=2000, history=False, positives=True)
        write_json(RAW_DIR / "latest-all.json", latest_all)
        write_json(RAW_DIR / "latest-positive.json", latest_positive)

    local_snapshot = save_local_snapshot(force)
    manifest = {
        "history_pages": pages,
        "history_rows": total_rows,
        "latest_all_rows": len(load_rows_from_payload(latest_all)),
        "latest_positive_rows": len(load_rows_from_payload(latest_positive)),
        "local_dump_exists": local_snapshot["exists"],
        "local_dump_rows": local_snapshot["rows"],
        "limit": limit,
    }
    write_json(RAW_DIR / "download-manifest.json", manifest)
    typer.echo(f"[history] done: {manifest}")


if __name__ == "__main__":
    app()
