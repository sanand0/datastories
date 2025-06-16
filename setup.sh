#!/usr/bin/env bash

# Convert README.md files to HTML using markdown-to-html-cli
npx -y --package markdown-to-html-cli markdown-to-html --source code-vs-domain/README.md --output code-vs-domain/index.html
npx -y --package markdown-to-html-cli markdown-to-html --source employment-trends/README.md --output employment-trends/index.html
npx -y --package markdown-to-html-cli markdown-to-html --source horoscope-2025-06-16/README.md --output horoscope-2025-06-16/index.html
