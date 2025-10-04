# Browser-History Data Stories — Plan B

This plan turns your Microsoft Edge browser history (Chromium SQLite at `~/.config/microsoft-edge/Default/History`) into publishable, privacy‑respecting data stories. It lists concrete analyses, sketches the visuals, and scores each idea on four dimensions: analysis novelty, visual impact, usefulness to readers, and reliability/robustness (1–5 each). It also notes required tables/fields and pitfalls.

Key insight: your History DB is unusually rich. Besides classic `urls`/`visits`, it contains query logs (`keyword_search_terms`), download logs, on‑device topic/language annotations (`content_annotations`), foreground attention time and tab/window IDs (`context_annotations`), and session‑like clusters (“Journeys”: `clusters`, `clusters_and_visits`). We confirmed this by reading your schema read‑only with SQLite’s `immutable=1` URI.

—

## Data Facts (so methods are robust)

- Timestamps: Chromium stores times as microseconds since 1601‑01‑01 UTC (“WebKit/Chrome time”). Convert via `datetime(visit_time/1e6-11644473600, 'unixepoch')`.
- Transitions: `visits.transition` encodes how a page was reached (typed, link, reload, auto‑subframe, etc.; bitmask). Useful to separate intent vs serendipity.
- Attention: `context_annotations.total_foreground_duration` records foreground time on a page (µs); `page_end_reason` helps filter auto‑closures.
- Topics/language: `content_annotations` includes `categories`, `entities`, `page_language`, and `search_terms` extracted on‑device. Useful for topic mixes without scraping.
- Journeys/Clusters: `clusters` and `clusters_and_visits` group related visits with labels, reflecting user tasks (“Journeys”). Great for story structure.
- Queries: `keyword_search_terms(term, normalized_term)` maps search terms to `urls`. Good for “question → answer” narratives.
- Sessions: For fallback sessionization, a 30–60 min inactivity gap is common in analytics (GA defaults to 30m; research often uses 1h).
- Diversity metrics to quantify variety/concentration: Shannon index, Simpson index, and HHI.

—

## Scoring Rubric (1–5)

- Novelty: How fresh/uncommon for personal data stories.
- Visual Impact: Potential to “wow” in a single view.
- Usefulness: Actionable/relatable insight for readers (not just you).
- Reliability: How robustly the DB supports it (few fragile steps).

—

## 12 Story Ideas (with methods, visuals, and scores)

1. The Attention Clock: Where your waking hours go

- What: Circular 24h “attention clock” showing share of total foreground time by hour, split weekday/weekend; annotate daily peaks (work, leisure). Uses `context_annotations.total_foreground_duration` and `visits.visit_time`.
- Visual: Polar stacked/radial heat map + weekday/weekend small multiples. Optional: rolling 4‑week animation.
- SQL sketch:
  ```sql
  WITH v AS (
    SELECT datetime((visit_time/1000000)-11644473600,'unixepoch') AS ts,
           total_foreground_duration/1000000.0 AS sec
    FROM visits
    JOIN context_annotations USING (id)
    WHERE total_foreground_duration IS NOT NULL AND total_foreground_duration>0
  )
  SELECT strftime('%w', ts) AS dow, strftime('%H', ts) AS hour, SUM(sec) AS seconds
  FROM v GROUP BY dow, hour;
  ```
- Scores: Novelty 4, Visual 5, Usefulness 4, Reliability 5.

2. Rabbit Holes, Mapped: How a single click becomes a journey

- What: Reconstruct clusters/threads that start from a typed URL or search and blossom via `from_visit`/`opener_visit`, quantified by depth/branching and time sinks.
- Visual: Storyline or Sankey from seed → branches; highlight the longest/most branched journeys.
- Fields: `clusters_and_visits`, `visits(from_visit, opener_visit, transition)`, `context_annotations.total_foreground_duration`.
- Scores: Novelty 5, Visual 5, Usefulness 4, Reliability 4.

3. Queries → Answers: Did searches actually end in satisfaction?

- What: For each `keyword_search_terms.normalized_term`, find the first non‑search domain reached within N minutes and total attention there. Show “query→destination” funnels and median time‑to‑answer.
- Visual: Alluvial (search term → site), with hover for time‑to‑answer stats.
- Scores: Novelty 4, Visual 4, Usefulness 5, Reliability 4.

4. Your News Diet, Quantified (and de‑biased)

- What: Categorize news visits by outlet and leaning (optional: AllSides/Ad Fontes), then compute variety using Shannon/Simpson and concentration via HHI. Present change over months.
- Visual: Stacked area by leaning; gauge dials for Shannon/HHI; dot plot of outlets by share.
- Caution: Labeling bias; disclose methodology and offer opt‑out for classification.
- Scores: Novelty 4, Visual 4, Usefulness 5, Reliability 3.

5. Languages of Your Web

- What: Use `content_annotations.page_language` to show time spent by language and “code‑switching” within a day.
- Visual: Ribbon/ThemeRiver over time; map of top language‑by‑country domains.
- Scores: Novelty 3, Visual 4, Usefulness 4, Reliability 5.

6. Intent vs Serendipity: Typed, Link, or Redirect?

- What: Split attention by `transition` type to reveal how much browsing is deliberate (typed/bookmark) vs link‑led or passive reloads; exclude subframes.
- Visual: Marimekko of time by transition; small multiples by domain.
- Scores: Novelty 4, Visual 4, Usefulness 4, Reliability 5.

7. Tab Sprawl Anatomy

- What: Use `context_annotations.window_id`, `tab_id`, and `parent_task_id` to estimate concurrent tabs and “tab chains”; compute average branch factor (`opener_visit`) and revisit rates.
- Visual: Beeswarm of concurrent tab counts per session; icicle of tab ancestry.
- Scores: Novelty 5, Visual 5, Usefulness 4, Reliability 4.

8. Sessions That Stick (and those that don’t)

- What: Compare GA‑style 30m gap sessions vs cluster‑based “Journeys.” Which grouping better explains attention and outcomes (downloads, longer reads)?
- Visual: Paired histograms of session lengths; Venn of visits captured by each method.
- Scores: Novelty 4, Visual 3, Usefulness 4, Reliability 4.

9. Download Footprints: What you save tells a story

- What: From `downloads*` tables, classify files by type/site, compute completion rates and “time‑to‑open,” and map chained sources via `downloads_url_chains`.
- Visual: Treemap by MIME type; Sankey of referer → download URL; timeline of big downloads.
- Scores: Novelty 3, Visual 4, Usefulness 4, Reliability 5.

10. Re‑Finds and Habits

- What: Identify domains you type repeatedly (`typed_count`, `incremented_omnibox_typed_score`) vs ones reached via referrals; show “habit backbone” vs exploration fringe.
- Visual: Backbone graph (habits) with faint fringe links (exploration).
- Scores: Novelty 4, Visual 4, Usefulness 4, Reliability 5.

11. The Long Read Index

- What: Rank pages/domains by median foreground time per visit; normalize by article length (optional) for a “stickiness” index; annotate bounce/short reads.
- Visual: Dot plot (median vs IQR of time), color by category.
- Scores: Novelty 3, Visual 4, Usefulness 5, Reliability 4.

12. From Question to Craft: Learning path case studies

- What: Pick a skill (“pandas,” “React”) and stitch a narrative of learning from search terms → docs → examples → forum answers, using clusters/queries and attention.
- Visual: Scrollytelling with step‑by‑step path and quotes from titles; optional anonymized URL slugs.
- Scores: Novelty 5, Visual 5, Usefulness 5, Reliability 4.

—

## Implementation Notes (pervasive techniques)

- Time conversion:
  ```sql
  SELECT datetime((visit_time/1000000)-11644473600,'unixepoch') AS ts FROM visits;
  ```
- Exclude subframes/redirect noise using `transition` masks per Chromium enum; keep `LINK`, `TYPED`, `AUTO_BOOKMARK`; drop `AUTO_SUBFRAME`.
- Attention time: prefer `context_annotations.total_foreground_duration` over `visits.visit_duration` where present. Treat zeros/nulls as unknown; winsorize extreme values.
- Topics/language: leverage `content_annotations.categories` and `page_language` to avoid scraping where possible.
- Sessions: compare “Journeys” clusters vs inactivity‑gap sessions (start with 30–60 min).
- Diversity: compute Shannon, Simpson, and HHI on attention‑weighted domain shares for news stories.

—

## Privacy and Reliability

- De‑identify: show domains and titles only when necessary; hash full URLs; aggregate to the week/day where possible.
- Opt‑outs: for News‑Diet leaning, openly disclose source lists and let readers toggle classifications (e.g., AllSides vs Ad Fontes).
- Edge cases: background tabs inflate counts; prefer foreground time; filter `page_end_reason` for crashes/timeouts when available.
- Reproducibility: include your SQL and a “one‑click” CSV export task; note the Chrome/Edge time epoch and transition semantics for readers.

—

## Inspirations (for tone and form)

- Chrome/Edge “Journeys” (History Clusters) shows how task‑based narratives resonate; use clusters to anchor stories.
- Nicholas Felton’s Annual Reports demonstrate intimate, elegant personal‑data storytelling; emulate the restraint and typography.

—

## What I’d publish first (quick wins)

1. The Attention Clock (Idea #1) — fast, impactful, highly robust.
2. Rabbit Holes, Mapped (Idea #2) — vivid and personal; great scrollytelling.
3. News Diet, Quantified (Idea #4) — high reader value; be transparent about labeling.

If you want, I can scaffold a tiny `uv run` script to export the necessary CSVs (read‑only, `immutable=1`) and a lightweight Lit‑HTML page with a Sankey/ThemeRiver to prototype 1–2 of these quickly.
