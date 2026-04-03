#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

echo "[1/10] Downloading canonical history"
uv run scripts/download_history.py

echo "[2/10] Normalizing submissions"
uv run scripts/normalize_submissions.py

echo "[3/10] Analyzing q-share-secret-server"
uv run scripts/analyze_share_secret.py

echo "[4/10] Fetching PR enrichment cache"
uv run scripts/fetch_pr_details.py

echo "[5/10] Deriving wow-pattern analyses"
uv run scripts/analyze_wow_patterns.py

echo "[6/10] Fetching image assets and thumbnails"
uv run scripts/fetch_image_assets.py

echo "[7/10] Exporting image submission CSVs"
uv run scripts/export_image_submission_csvs.py

echo "[8/10] Deepening image analysis"
uv run scripts/analyze_image_cohort.py

echo "[9/10] Analyzing skill transfer"
uv run scripts/analyze_skill_transfer.py

echo "[10/10] Writing reports"
uv run scripts/write_reports.py
