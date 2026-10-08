#!/usr/bin/env bash
set -euo pipefail

# Install once with `npm ci`; use the pinned local CLI for every page.
CONVERTER="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/node_modules/.bin/markdown-to-html"
if [[ ! -x "$CONVERTER" ]]; then
  echo "Missing markdown-to-html: run npm ci first" >&2
  exit 1
fi

"$CONVERTER" --source anthropic-work/README.md --output anthropic-work/index.html
"$CONVERTER" --source code-vs-domain/README.md --output code-vs-domain/index.html
"$CONVERTER" --source employment-trends/README.md --output employment-trends/index.html
"$CONVERTER" --source horoscope-2025-06-16/README.md --output horoscope-2025-06-16/index.html
"$CONVERTER" --source chatgpt-topics/README.md --output chatgpt-topics/index.html
"$CONVERTER" --source vipassana/README.md --output vipassana/index.html
"$CONVERTER" --source chatgpt-vs-google/README.md --output chatgpt-vs-google/index.html
"$CONVERTER" --source google-searches/README.md --output google-searches/index.html
"$CONVERTER" --source browser-history/README.md --output browser-history/index.html
"$CONVERTER" --source tds-improvements/README.md --output tds-improvements/index.html
"$CONVERTER" --source tds-improvements/summary.md --output tds-improvements/summary.html
"$CONVERTER" --source tds-improvements/learnings.md --output tds-improvements/learnings.html
