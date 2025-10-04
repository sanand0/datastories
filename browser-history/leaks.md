Browser‑History Privacy Review

- Scope: Files staged as added in this commit under `browser-history/`.
- Severity scale: High = directly identifies person/org or grants access; Medium = reveals sensitive behavior, internal systems, or detailed patterns; Low = aggregated or benign; None = no issues found.

README

- File: `browser-history/README.md`
- Issues: Mentions local history path; links to visualizations. No direct PII or credentials.
- Severity: Low
- Recommendation: Safe to publish. Screenshots it links to are reviewed separately.

Attention Clock

- File: `browser-history/attention-clock/attention_by_day.csv`
- Issues: Per‑day visit counts and total time; reveals daily activity patterns over months.
- Severity: Medium
- Recommendation: Publish only if comfortable exposing day‑level activity. Consider aggregating to week/month.

- File: `browser-history/attention-clock/attention_by_hour.csv`
- Issues: Day‑of‑week and hour‑level aggregates of visits/time; reveals circadian/work rhythm.
- Severity: Low
- Recommendation: Generally safe; consider bucketing hours (e.g., morning/afternoon/evening) for extra privacy.

- File: `browser-history/attention-clock/domain_top.csv`
- Issues: Lists top domains with counts and foreground time, including personal and corporate/internal hosts (e.g., `mail.google.com`, `calendar.google.com`, `llmfoundry.straive.com`, many `*.straivedemo.com`, `passwordreset.straive.com`, multiple `localhost` ports, `exam.sanand.workers.dev`, etc.). This strongly identifies the user and employer, internal systems, apps, and usage patterns.
- Severity: High
- Recommendation: Do not publish raw. If needed, anonymize or group domains (e.g., “Email”, “Calendar”, “Meetings”, “Internal tools”), remove company/client domains, and strip low‑traffic long tail that may deanonymize.

- File: `browser-history/attention-clock/spec.md`
- Issues: Narrative/spec only. No PII.
- Severity: Low
- Recommendation: Safe to publish.

- File: `browser-history/attention-clock/screenshot.webp`
- Issues: Screenshot may display specific domain names, titles, quantitative stats linked to the individual/org.
- Severity: High (visual PII)
- Recommendation: Publish only after manual review/redaction (blur sensitive labels/values/domains).

Claude (Aggregates + Screens)

- File: `browser-history/claude/categories.json`
- Issues: Aggregated category counts only.
- Severity: Low
- Recommendation: Safe to publish.

- File: `browser-history/claude/daily_pattern.json`
- Issues: Day‑of‑week aggregate counts.
- Severity: Low
- Recommendation: Safe to publish.

- File: `browser-history/claude/hourly_pattern.json`
- Issues: Hour‑level aggregate counts.
- Severity: Low
- Recommendation: Safe to publish.

- File: `browser-history/claude/timeline.json`
- Issues: Per‑date visit counts spanning multiple months; reveals periods of high/low activity (work/vacations/late nights).
- Severity: Medium
- Recommendation: Publish only if comfortable exposing daily activity history. Consider smoothing/weekly aggregation.

- File: `browser-history/claude/top_searches.json`
- Issues: Contains raw search terms (e.g., technical, travel, health‑adjacent queries). Search queries are highly identifying and can reveal sensitive interests/needs.
- Severity: High
- Recommendation: Do not publish raw. If needed, redact sensitive terms; group into broad topics; release only frequency bins without exemplars.

- File: `browser-history/claude/top_sites.json`
- Issues: Direct URLs and titles with personal info and internal links, including:
  - Personal and work email addresses in titles (`root.node@gmail.com`, `s.anand@gramener.com`).
  - Meeting link (`meet.google.com/jct-wrzo-oeq?authuser=2`).
  - Google Drive folder ID (`drive.google.com/drive/folders/1f0AZTgFPvCFlPV4JSwXwMXC8VqhZpxrw`).
  - Org identifiers and systems (Straive, Gramener, `*.straive.com`, `*.straivedemo.com`).
  - Timestamps of last visits per site.
- Severity: High (direct PII and internal resource identifiers)
- Recommendation: Do not publish. If necessary, replace with anonymized categories and remove URLs/titles, emails, meeting links, and IDs.

- Files: `browser-history/claude/screenshot.webp`, `browser-history/claude/screenshot1.webp`
- Issues: Screenshots may expose private data, queries, emails, internal tools, timestamps.
- Severity: High (visual PII)
- Recommendation: Publish only after thorough manual review and redaction.

Planning Docs

- Files: `browser-history/plan.md`, `browser-history/plan-b.md`, `browser-history/plan-spec.md`
- Issues: Planning/narrative; include references to public domains (e.g., `mail.google.com`) but no personal data.
- Severity: Low
- Recommendation: Safe to publish.

Rabbit Holes

- File: `browser-history/rabbit-holes/chain_depths.csv`
- Issues: Chain metrics only (ids, depths, counts). No URLs/titles.
- Severity: Low
- Recommendation: Safe to publish.

- File: `browser-history/rabbit-holes/chains_summary.csv`
- Issues: Per‑chain visit counts, distinct domain counts, and start/end timestamps and durations. No URLs, but timestamps provide detailed behavior traces across days.
- Severity: Medium
- Recommendation: Publish only if comfortable exposing session timelines; consider redacting timestamps to date‑only or aggregating.

- Files: `browser-history/rabbit-holes/cluster_depths.csv`, `browser-history/rabbit-holes/clusters_summary.csv`, `browser-history/rabbit-holes/deepest_chains.csv`, `browser-history/rabbit-holes/deepest_clusters.csv`
- Issues: Currently empty.
- Severity: None
- Recommendation: Safe to publish (as is). If populated later, reassess for URLs/titles/identifiers.

- File: `browser-history/rabbit-holes/spec.md`
- Issues: Narrative/spec only.
- Severity: Low
- Recommendation: Safe to publish.

- File: `browser-history/rabbit-holes/screenshot.webp`
- Issues: Screenshot likely shows chain details and labels that can be identifying.
- Severity: High (visual PII)
- Recommendation: Publish only after manual redaction.

- File: `browser-history/rabbit-holes/v2.html`
- Issues: Visualization shell; no inline personal data detected; loads CSV at runtime if present.
- Severity: Low (by itself)
- Recommendation: Safe to publish alone. If publishing with underlying detailed CSVs, follow those files’ recommendations.

Search Funnels

- File: `browser-history/search-funnels/spec.md`
- Issues: Narrative/spec only.
- Severity: Low
- Recommendation: Safe to publish.

- Files: `browser-history/search-funnels/v1.html`, `browser-history/search-funnels/v2.html`, `browser-history/search-funnels/v3.html`
- Issues: Visualization shells. They fetch `search_funnels_terms.csv`/`search_samples.csv` at runtime, and create Google search links for terms. No inline personal data in the HTML itself.
- Severity: Low (by themselves)
- Recommendation: Safe to publish alone. If paired with term datasets, anonymize or categorize terms; avoid raw examples.

- Files: `browser-history/search-funnels/screenshot.webp`, `browser-history/search-funnels/screenshot-landscape.webp`
- Issues: Screenshots may reveal specific search terms or UI states.
- Severity: High (visual PII)
- Recommendation: Publish only after manual redaction.

Summary Recommendations

- Do not publish raw: `claude/top_sites.json`, `claude/top_searches.json`, all `*/screenshot*.webp`, and `attention-clock/domain_top.csv`.
- Publish with aggregation/redaction: `attention-clock/attention_by_day.csv`, `claude/timeline.json`, `rabbit-holes/chains_summary.csv`.
- Generally safe: README/specs, category/hourly patterns, shell HTML files without attached data.

- Redaction tips:
  - Replace personal emails, meeting links, and Google Drive IDs with placeholders or remove fields entirely.
  - Group domains into high‑level categories; drop internal and low‑frequency domains.
  - Coarsen time granularity (weekly/monthly; remove exact timestamps).
  - Manually review and blur sensitive elements in screenshots.
