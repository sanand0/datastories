#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEFAULT_ASSET_DIR="$ROOT_DIR/data/release-assets"
DEFAULT_QUESTIONS=(
  q-generate-affective-chart
  q-generate-concept-incarnation
  q-generate-style-transplant
  q-generate-paradox-portrait
)

usage() {
  cat <<'EOF'
Usage: scripts/upload_question_releases.sh [options]

Create per-question GitHub releases and upload only missing JSON/PNG assets.

Options:
  --question-id QUESTION   Restrict to one or more q-generate-* questions
  --repo OWNER/REPO        GitHub repository for releases (default: current gh repo or GH_REPO)
  --asset-dir PATH         Directory containing prepared release assets
  --skip-build             Skip local asset preparation
  --force-build            Rebuild local release assets before uploading
  --dry-run                Print planned actions without creating releases or uploading assets
  --format text|json       Output format (default: json for non-TTY, text for TTY)
  --describe               Print machine-readable CLI description
  -h, --help               Show this help
EOF
}

describe() {
  cat <<'EOF'
{
  "name": "upload_question_releases.sh",
  "description": "Create q-generate GitHub releases and upload only unreleased JSON/PNG assets.",
  "options": {
    "--question-id": {"type": "array[string]", "default": ["q-generate-affective-chart", "q-generate-concept-incarnation", "q-generate-style-transplant", "q-generate-paradox-portrait"]},
    "--repo": {"type": "string", "default": "current gh repo or GH_REPO"},
    "--asset-dir": {"type": "path", "default": "data/release-assets"},
    "--skip-build": {"type": "boolean", "default": false},
    "--force-build": {"type": "boolean", "default": false},
    "--dry-run": {"type": "boolean", "default": false},
    "--format": {"type": "string", "enum": ["text", "json"], "default": "json for non-TTY, text for TTY"}
  }
}
EOF
}

log() {
  if [[ "$FORMAT" == "text" ]]; then
    printf '%s\n' "$*"
  else
    printf '%s\n' "$*" >&2
  fi
}

json_escape() {
  local value="$1"
  value=${value//\\/\\\\}
  value=${value//\"/\\\"}
  value=${value//$'\n'/\\n}
  value=${value//$'\r'/\\r}
  value=${value//$'\t'/\\t}
  printf '%s' "$value"
}

question_allowed() {
  local value="$1"
  case "$value" in
    q-generate-affective-chart|q-generate-concept-incarnation|q-generate-style-transplant|q-generate-paradox-portrait) return 0 ;;
    *) return 1 ;;
  esac
}

rate_limit_reset_iso() {
  local reset_epoch="$1"
  date -u -d "@$reset_epoch" +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || printf '%s' "$reset_epoch"
}

report_rate_limit_and_exit() {
  local remaining reset
  remaining="$(gh api rate_limit --jq '.rate.remaining' 2>/dev/null || printf '')"
  reset="$(gh api rate_limit --jq '.rate.reset' 2>/dev/null || printf '')"
  if [[ "$remaining" == "0" && -n "$reset" ]]; then
    printf 'GitHub API rate limit exhausted. Safe to rerun after %s.\n' "$(rate_limit_reset_iso "$reset")" >&2
    exit 75
  fi
  exit 1
}

abort_if_rate_limited() {
  local remaining
  remaining="$(gh api rate_limit --jq '.rate.remaining' 2>/dev/null || printf '')"
  if [[ "$remaining" == "0" ]]; then
    report_rate_limit_and_exit
  fi
}

build_assets() {
  local -a cmd=(uv run "$ROOT_DIR/scripts/build_question_release_assets.py" --output-dir "$ASSET_DIR" --format text)
  local question
  for question in "${QUESTIONS[@]}"; do
    cmd+=(--question-id "$question")
  done
  if [[ "$FORCE_BUILD" == "1" ]]; then
    cmd+=(--force)
  fi
  if [[ "$DRY_RUN" == "1" ]]; then
    cmd+=(--dry-run)
  fi
  log "[release-upload] preparing local assets"
  (cd "$ROOT_DIR" && "${cmd[@]}")
}

release_exists() {
  if gh release view "$1" --repo "$REPO" >/dev/null 2>&1; then
    return 0
  fi
  abort_if_rate_limited
  return 1
}

create_release_if_needed() {
  local tag="$1"
  local question="$2"
  if release_exists "$tag"; then
    RELEASE_CREATED=0
    return 0
  fi
  RELEASE_CREATED=1
  local notes="TDS Jan 2026 Project 1 assets for ${question}. Asset filenames use anonymized user hashes plus submission IDs. See gallery/summary.json for full status and metadata."
  if [[ "$DRY_RUN" == "1" ]]; then
    log "[dry-run] gh release create $tag --repo $REPO"
    return 0
  fi
  if ! gh release create "$tag" --repo "$REPO" --title "$tag" --notes "$notes" >/dev/null; then
    report_rate_limit_and_exit
  fi
  log "[release-upload] created release $tag"
}

load_existing_assets() {
  local tag="$1"
  if [[ "$DRY_RUN" == "1" ]] && ! release_exists "$tag"; then
    EXISTING_ASSETS=()
    return 0
  fi
  if ! mapfile -t EXISTING_ASSETS < <(gh release view "$tag" --repo "$REPO" --json assets --jq '.assets[].name'); then
    report_rate_limit_and_exit
  fi
}

has_existing_asset() {
  local needle="$1"
  local name
  for name in "${EXISTING_ASSETS[@]:-}"; do
    if [[ "$name" == "$needle" ]]; then
      return 0
    fi
  done
  return 1
}

upload_missing_assets() {
  local tag="$1"
  shift
  local -a files=("$@")
  local batch_size=100
  local start=0
  local end=0
  local total="${#files[@]}"
  while (( start < total )); do
    end=$(( start + batch_size ))
    if (( end > total )); then
      end=$total
    fi
    local -a batch=("${files[@]:start:end-start}")
    if [[ "$DRY_RUN" == "1" ]]; then
      log "[dry-run] gh release upload $tag --repo $REPO (${#batch[@]} assets)"
    else
      if ! gh release upload "$tag" --repo "$REPO" "${batch[@]}" >/dev/null; then
        report_rate_limit_and_exit
      fi
      log "[release-upload] uploaded ${#batch[@]} assets to $tag"
    fi
    start=$end
  done
}

QUESTIONS=()
REPO="${GH_REPO:-}"
ASSET_DIR="$DEFAULT_ASSET_DIR"
SKIP_BUILD=0
FORCE_BUILD=0
DRY_RUN=0
FORMAT=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --question-id)
      [[ $# -ge 2 ]] || { echo "Missing value for --question-id" >&2; exit 2; }
      question_allowed "$2" || { echo "Unsupported question ID: $2" >&2; exit 2; }
      QUESTIONS+=("$2")
      shift 2
      ;;
    --repo)
      [[ $# -ge 2 ]] || { echo "Missing value for --repo" >&2; exit 2; }
      REPO="$2"
      shift 2
      ;;
    --asset-dir)
      [[ $# -ge 2 ]] || { echo "Missing value for --asset-dir" >&2; exit 2; }
      ASSET_DIR="$2"
      shift 2
      ;;
    --skip-build)
      SKIP_BUILD=1
      shift
      ;;
    --force-build)
      FORCE_BUILD=1
      shift
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    --format)
      [[ $# -ge 2 ]] || { echo "Missing value for --format" >&2; exit 2; }
      FORMAT="$2"
      shift 2
      ;;
    --describe)
      describe
      exit 0
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ -z "$FORMAT" ]]; then
  if [[ -t 1 ]]; then
    FORMAT="text"
  else
    FORMAT="json"
  fi
fi

if [[ "$FORMAT" != "text" && "$FORMAT" != "json" ]]; then
  echo "--format must be text or json" >&2
  exit 2
fi

if [[ "${#QUESTIONS[@]}" -eq 0 ]]; then
  QUESTIONS=("${DEFAULT_QUESTIONS[@]}")
fi

if [[ -z "$REPO" ]]; then
  REPO="$(gh repo view --json nameWithOwner --jq .nameWithOwner)"
fi

abort_if_rate_limited

if [[ "$SKIP_BUILD" != "1" ]]; then
  build_assets
fi

ASSET_DIR="$(cd "$ROOT_DIR" && mkdir -p "$ASSET_DIR" && cd "$ASSET_DIR" && pwd)"
QUESTION_SUMMARIES=()

for question in "${QUESTIONS[@]}"; do
  tag="tds-2026-01-p1_${question}"
  question_dir="$ASSET_DIR/$question"
  mkdir -p "$question_dir"
  RELEASE_CREATED=0
  create_release_if_needed "$tag" "$question"
  load_existing_assets "$tag"

  mapfile -d '' -t local_files < <(find "$question_dir" -maxdepth 1 -type f \( -name '*.json' -o -name '*.png' \) -print0 | sort -z)
  missing_files=()
  skipped_existing=0
  for file in "${local_files[@]}"; do
    base_name="$(basename "$file")"
    if has_existing_asset "$base_name"; then
      skipped_existing=$(( skipped_existing + 1 ))
      continue
    fi
    missing_files+=("$file")
  done

  uploaded_count=0
  if [[ "${#missing_files[@]}" -gt 0 ]]; then
    upload_missing_assets "$tag" "${missing_files[@]}"
    uploaded_count="${#missing_files[@]}"
  else
    log "[release-upload] $tag already has all ${#local_files[@]} local assets"
  fi

  QUESTION_SUMMARIES+=(
    "{\"question_id\":\"$(json_escape "$question")\",\"tag\":\"$(json_escape "$tag")\",\"release_created\":$RELEASE_CREATED,\"local_asset_count\":${#local_files[@]},\"uploaded_count\":$uploaded_count,\"skipped_existing_count\":$skipped_existing}"
  )
done

if [[ "$FORMAT" == "json" ]]; then
  printf '{"repo":"%s","asset_dir":"%s","dry_run":%s,"questions":[%s]}\n' \
    "$(json_escape "$REPO")" \
    "$(json_escape "$ASSET_DIR")" \
    "$([[ "$DRY_RUN" == "1" ]] && echo true || echo false)" \
    "$(IFS=,; echo "${QUESTION_SUMMARIES[*]}")"
fi
