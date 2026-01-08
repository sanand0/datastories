#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "httpx>=0.27",
#   "pandas>=2.2",
#   "python-dotenv>=1.0",
#   "rich>=13.7",
# ]
# ///

"""Fetch most depended-upon packages from Libraries.io for PyPI and npm."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

import httpx
import pandas as pd
from dotenv import load_dotenv
from rich.traceback import install

install(show_locals=True)

API_URL = "https://libraries.io/api/search"
CACHE_ROOT = Path(".cache/libraries-io")
FIELDS = [
    "name",
    "dependent_repos_count",
    "dependents_count",
    "forks",
    "stars",
    "rank",
    "contributions_count",
]
MAX_PAGES = 100
PER_PAGE = 100
RATE_LIMIT_SECONDS = 1.05
MAX_RETRIES = 5
RETRY_BACKOFF_BASE = 2.0
RETRY_BACKOFF_CAP = 30.0
REQUEST_TIMEOUT = httpx.Timeout(60.0)


def load_api_key() -> str:
    """Load the Libraries.io API key from the environment or .env file."""
    load_dotenv()
    api_key = os.getenv("LIBRARIES_IO_API_KEY")
    if not api_key:
        raise SystemExit("Missing LIBRARIES_IO_API_KEY in environment or .env")
    return api_key


def rate_limit(last_request_at: float | None) -> None:
    """Sleep long enough to respect the 60 requests/minute API limit."""
    if last_request_at is None:
        return
    elapsed = time.monotonic() - last_request_at
    if elapsed < RATE_LIMIT_SECONDS:
        time.sleep(RATE_LIMIT_SECONDS - elapsed)


def ensure_list(data: object, context: str) -> list[dict[str, object]]:
    """Validate and return an API response list."""
    if not isinstance(data, list):
        raise ValueError(f"Unexpected response for {context}")
    return data


def request_page(
    client: httpx.Client,
    api_key: str,
    platform: str,
    page: int,
    last_request_at: float | None,
) -> tuple[list[dict[str, object]], float]:
    """Request a page with retries, honoring the rate limit."""
    for attempt in range(1, MAX_RETRIES + 1):
        rate_limit(last_request_at)
        last_request_at = time.monotonic()
        try:
            response = client.get(
                API_URL,
                params={
                    "platforms": platform,
                    "sort": "dependents_count",
                    "order": "desc",
                    "page": page,
                    "per_page": PER_PAGE,
                    "api_key": api_key,
                },
            )
            response.raise_for_status()
            data = response.json()
            return ensure_list(data, f"{platform} page {page}"), last_request_at
        except (httpx.HTTPError, ValueError) as exc:
            if attempt == MAX_RETRIES:
                raise
            backoff = min(RETRY_BACKOFF_BASE**attempt, RETRY_BACKOFF_CAP)
            print(
                f"{platform} page {page} attempt {attempt} failed: {exc}. "
                f"Retrying in {backoff:.1f}s..."
            )
            time.sleep(backoff)

    raise RuntimeError(f"Failed to fetch {platform} page {page}")


def fetch_page(
    client: httpx.Client,
    api_key: str,
    platform: str,
    page: int,
    cache_dir: Path,
    last_request_at: float | None,
) -> tuple[list[dict[str, object]], float | None, bool]:
    """Fetch a page of results, reading from cache when available."""
    cache_file = cache_dir / f"page-{page}.json"
    if cache_file.exists():
        data = json.loads(cache_file.read_text(encoding="utf-8"))
        return ensure_list(data, f"{platform} page {page} (cache)"), last_request_at, True

    data, last_request_at = request_page(
        client,
        api_key,
        platform,
        page,
        last_request_at,
    )

    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
    return data, last_request_at, False


def extract_rows(items: list[dict[str, object]]) -> list[dict[str, object]]:
    """Project Libraries.io results to the requested CSV fields."""
    return [{field: item.get(field) for field in FIELDS} for item in items]


def fetch_platform(
    client: httpx.Client,
    api_key: str,
    platform: str,
) -> list[dict[str, object]]:
    """Fetch and cache the top dependents pages for a platform."""
    cache_dir = CACHE_ROOT / platform.lower()
    rows: list[dict[str, object]] = []
    last_request_at: float | None = None

    for page in range(1, MAX_PAGES + 1):
        items, last_request_at, cached = fetch_page(
            client,
            api_key,
            platform,
            page,
            cache_dir,
            last_request_at,
        )
        rows.extend(extract_rows(items))
        status = "cached" if cached else "fetched"
        print(f"{platform} page {page}/{MAX_PAGES}: {status} {len(items)} items")

    return rows


def write_csv(rows: list[dict[str, object]], path: Path) -> None:
    """Write the extracted rows to a CSV file."""
    frame = pd.DataFrame.from_records(rows, columns=FIELDS)
    frame.to_csv(path, index=False)
    print(f"Wrote {len(frame)} rows to {path}")


def main() -> None:
    """Run the Libraries.io export for PyPI and npm."""
    api_key = load_api_key()
    with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
        for platform, output in [
            ("PyPI", Path("pypi-repos.csv")),
            ("npm", Path("npm-repos.csv")),
        ]:
            print(f"Starting {platform} export...")
            rows = fetch_platform(client, api_key, platform)
            write_csv(rows, output)


if __name__ == "__main__":
    main()
