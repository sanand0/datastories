# Browser History Story Ideas — Spec (merged)

Source docs: `plan.md` (2025-10-04) + `plan-b.md`. Data: Edge History SQLite at `~/.config/microsoft-edge/Default/History` (read-only via `file:...?immutable=1&mode=ro`).

—

**Scoring rubric (1–5)**
- Novelty • Visual Impact • Usefulness • Reliability

—

## Revised Idea List (merged + rescored)

- 1) Context Switching: Inbox vs Maker vs AI — 4 • 4 • 5 • 4
  - Daily/weekly shares of time across modes: communication (Gmail/Meet/Calendar), building (GitHub/localhost), AI assistants (ChatGPT/Gemini) and research.

- 2) Flow Sprints & Rabbit Holes — 5 • 5 • 4 • 4
  - Long, intense sequences (Journeys/clusters + visit graph) and how branches deepen a task.

- 3) Curiosity Atlas → Answers — 4 • 4 • 5 • 4
  - Cluster search terms, then track first downstream destinations and time-to-answer.

- 4) Attention Clock (Circadian Stack) — 4 • 5 • 4 • 5
  - Foreground time by hour and weekday/weekend to reveal circadian rhythm.

- 5) AI Co‑Pilot Reliance Tracker — 5 • 5 • 5 • 4
  - Share and cadence of AI tools vs traditional resources; how AI threads interleave with builds.

- 6) News Diet, Quantified — 4 • 4 • 5 • 3
  - Outlet mix + diversity indices; disclose labeling assumptions.

- 7) Intent vs Serendipity — 4 • 4 • 4 • 5
  - Time split by `transition` type (typed/bookmark/link/reload) to separate intention from drift.

- 8) Tab Sprawl Anatomy — 5 • 5 • 4 • 4
  - Concurrency, ancestry, branch factor; when tabs explode and why.

- 9) Long Read Index — 3 • 4 • 5 • 4
  - Pages/domains ranked by median foreground time per visit (stickiness).

- 10) Download Footprints — 3 • 4 • 4 • 5
  - What you saved, from where, and completion/open rates.

- 11) Languages of Your Web — 3 • 4 • 4 • 5
  - Time by `page_language` and day-level code‑switching.

- 12) Favicon Loom (Mosaic) — 3 • 5 • 3 • 3
  - Aesthetic favicon tapestry anchored by domain entropy.

- 13) Sessions That Stick — 4 • 3 • 4 • 4
  - Compare inactivity-gap sessions to History “Journeys” clusters.

- 14) From Question to Craft (Learning Paths) — 5 • 5 • 5 • 4
  - Case studies: search → docs → examples → implementation, stitched via clusters and attention.

—

## Top 3 Picks

1) AI Co‑Pilot Reliance Tracker (5 • 5 • 5 • 4)
2) Flow Sprints & Rabbit Holes (5 • 5 • 4 • 4)
3) Attention Clock (Circadian Stack) (4 • 5 • 4 • 5)

—

## Claude Code Prompts (for the Top 3)

### 1) AI Co‑Pilot Reliance Tracker

Prompt
```
Goal: Reveal how much of daily work routes through AI assistants versus traditional resources, and how AI time interleaves with building and research.

Effect/Mood: Feel the momentum and pragmatism of modern craft—calm, candid, and grounded in evidence—so readers sense how AI augments (not replaces) real work.

Data Access: SQLite at ~/.config/microsoft-edge/Default/History via URI 'file:{ABS_PATH}?immutable=1&mode=ro'. Use read-only connections only.

Domain Buckets:
  AI = chatgpt.com, gemini.google.com, aistudio.google.com, claude.ai, perplexity.ai
  Build = github.com, localhost, gist.github.com, codesandbox.io, stackoverflow.com
  Search/Ref = google.com, duckduckgo.com, bing.com
  Comm = mail.google.com, calendar.google.com, meet.google.com, slack.com

SQL (time + visits by domain + bucket):
WITH url_hosts AS (
  SELECT u.id AS url_id,
         lower(substr(u.url, instr(u.url,'://')+3,
           CASE WHEN instr(substr(u.url, instr(u.url,'://')+3),'/')=0
                THEN length(u.url)
                ELSE instr(substr(u.url, instr(u.url,'://')+3),'/')-1 END)) AS host
  FROM urls u
), base AS (
  SELECT v.id AS visit_id, v.visit_time, uh.host,
         COALESCE(ca.total_foreground_duration, v.visit_duration) AS fg_us
  FROM visits v
  JOIN url_hosts uh ON uh.url_id = v.url
  LEFT JOIN context_annotations ca ON ca.visit_id = v.id
), tagged AS (
  SELECT *,
    CASE
      WHEN host LIKE '%chatgpt.com' OR host LIKE '%claude.ai' OR host LIKE '%perplexity.ai'
        OR host LIKE '%gemini.google.com' OR host LIKE '%aistudio.google.com' THEN 'AI'
      WHEN host LIKE '%github.com' OR host LIKE 'localhost%' OR host LIKE '%gist.github.com%'
        OR host LIKE '%codesandbox.io' OR host LIKE '%stackoverflow.com' THEN 'Build'
      WHEN host LIKE '%google.com' OR host LIKE '%duckduckgo.com' OR host LIKE '%bing.com' THEN 'Search/Ref'
      WHEN host LIKE '%mail.google.com' OR host LIKE '%calendar.google.com' OR host LIKE '%meet.google.com' OR host LIKE '%slack.com' THEN 'Comm'
      ELSE 'Other' END AS bucket
  FROM base
)
SELECT
  date(datetime((visit_time/1000000)-11644473600,'unixepoch')) AS d,
  bucket,
  SUM(COALESCE(fg_us,0))/1000000.0 AS seconds,
  COUNT(*) AS visits
FROM tagged
GROUP BY d, bucket
ORDER BY d, bucket;

SQL (search → AI follow-through within 10 minutes):
WITH url_hosts AS (
  SELECT id, url,
         lower(substr(url, instr(url,'://')+3,
           CASE WHEN instr(substr(url, instr(url,'://')+3),'/')=0
                THEN length(url)
                ELSE instr(substr(url, instr(url,'://')+3),'/')-1 END)) AS host
  FROM urls
), searches AS (
  SELECT v.id AS visit_id, v.visit_time, k.normalized_term AS term
  FROM keyword_search_terms k
  JOIN visits v ON v.url = k.url_id
), ai_visits AS (
  SELECT v.id AS visit_id, v.visit_time
  FROM visits v JOIN url_hosts u ON u.id = v.url
  WHERE u.host LIKE '%chatgpt.com' OR u.host LIKE '%claude.ai' OR u.host LIKE '%gemini.google.com'
     OR u.host LIKE '%aistudio.google.com' OR u.host LIKE '%perplexity.ai'
)
SELECT s.term,
       COUNT(*) AS searches,
       SUM(CASE WHEN EXISTS (
         SELECT 1 FROM ai_visits a
         WHERE a.visit_time BETWEEN s.visit_time AND s.visit_time + (10*60*1000000)
       ) THEN 1 ELSE 0 END) AS searches_followed_by_ai
FROM searches s
GROUP BY s.term
ORDER BY searches DESC
LIMIT 200;

Analysis Steps:
1) Export daily bucketed seconds + visits; compute shares and rolling 7‑day means.
2) Quantify “search→AI” propensity per term; surface top rising terms.
3) Correlate AI share with Build share by day; annotate extremes.
4) Anonymize full URLs; publish only aggregates and selected hosts.
```

—

### 2) Flow Sprints & Rabbit Holes

Prompt
```
Goal: Surface the longest, most absorbing browsing episodes and how they branch from a single seed into deep research/build flows.

Effect/Mood: Evoke immersion and narrative propulsion—let readers feel the pull of a task turning into a journey, equal parts focus and discovery.

Data Access: SQLite at ~/.config/microsoft-edge/Default/History via URI 'file:{ABS_PATH}?immutable=1&mode=ro'.

SQL (top clusters by engagement):
SELECT c.cluster_id,
       c.label,
       COUNT(*) AS visits,
       SUM(COALESCE(ca.total_foreground_duration, v.visit_duration))/1000000.0 AS seconds,
       MIN(v.visit_time) AS start_us,
       MAX(v.visit_time) AS end_us
FROM clusters_and_visits cav
JOIN clusters c ON c.cluster_id = cav.cluster_id
JOIN visits v ON v.id = cav.visit_id
LEFT JOIN context_annotations ca ON ca.visit_id = v.id
GROUP BY c.cluster_id, c.label
HAVING visits >= 20 OR seconds >= 1800
ORDER BY seconds DESC
LIMIT 100;

SQL (approximate branching: average out-degree inside clusters):
WITH edges AS (
  SELECT cav.cluster_id, v.from_visit AS parent_id
  FROM visits v JOIN clusters_and_visits cav ON cav.visit_id = v.id
  WHERE v.from_visit IS NOT NULL
), child_counts AS (
  SELECT cluster_id, parent_id, COUNT(*) AS child_cnt
  FROM edges GROUP BY cluster_id, parent_id
)
SELECT cluster_id, AVG(child_cnt) AS avg_branch_factor
FROM child_counts GROUP BY cluster_id
ORDER BY avg_branch_factor DESC;

SQL (session fallback using 5‑minute gap):
WITH ordered AS (
  SELECT v.id, v.visit_time,
         LAG(v.visit_time) OVER (ORDER BY v.visit_time) AS prev_us,
         COALESCE(ca.total_foreground_duration, v.visit_duration) AS fg_us
  FROM visits v LEFT JOIN context_annotations ca ON ca.visit_id = v.id
), marked AS (
  SELECT *, CASE WHEN prev_us IS NULL OR visit_time - prev_us > 5*60*1000000 THEN 1 ELSE 0 END AS new_flag
  FROM ordered
)
SELECT id,
       SUM(new_flag) OVER (ORDER BY visit_time ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS session_id,
       visit_time, fg_us
FROM marked;

Analysis Steps:
1) Rank clusters by attention seconds and visits; pick exemplars.
2) Compute branch factor per exemplar; extract top root pages (typed/search transitions).
3) If clusters missing, use 5‑minute sessionization fallback; summarize sessions ≥ 60 minutes.
4) Compile anonymized timelines (minute bins) and branch tables for storytelling.
```

—

### 3) Attention Clock (Circadian Stack)

Prompt
```
Goal: Reveal the daily rhythm of attention—when focus concentrates and when it ebbs across weekdays vs weekends.

Effect/Mood: Quiet, reflective, and human—like watching a tide chart of work and life, encouraging readers to notice and protect their own peak hours.

Data Access: SQLite at ~/.config/microsoft-edge/Default/History via URI 'file:{ABS_PATH}?immutable=1&mode=ro'.

SQL (foreground seconds by weekday/hour):
WITH v AS (
  SELECT datetime((visit_time/1000000)-11644473600,'unixepoch') AS ts,
         COALESCE(ca.total_foreground_duration, v.visit_duration)/1000000.0 AS sec
  FROM visits v LEFT JOIN context_annotations ca ON ca.visit_id = v.id
  WHERE COALESCE(ca.total_foreground_duration, v.visit_duration) IS NOT NULL
    AND COALESCE(ca.total_foreground_duration, v.visit_duration) > 0
)
SELECT strftime('%w', ts) AS dow,
       strftime('%H', ts) AS hour,
       SUM(sec) AS seconds
FROM v
GROUP BY dow, hour
ORDER BY dow, hour;

SQL (weekday vs weekend split):
WITH v AS (
  SELECT datetime((visit_time/1000000)-11644473600,'unixepoch') AS ts,
         COALESCE(ca.total_foreground_duration, v.visit_duration)/1000000.0 AS sec
  FROM visits v LEFT JOIN context_annotations ca ON ca.visit_id = v.id
  WHERE COALESCE(ca.total_foreground_duration, v.visit_duration) IS NOT NULL
)
SELECT CASE WHEN strftime('%w', ts) IN ('0','6') THEN 'weekend' ELSE 'weekday' END AS wk,
       strftime('%H', ts) AS hour,
       SUM(sec) AS seconds
FROM v
GROUP BY wk, hour
ORDER BY wk, hour;

Analysis Steps:
1) Export hour×weekday seconds; compute shares per day and Z-scores vs overall mean.
2) Identify peak/trough hours; annotate atypical days with short text labels (no URLs).
3) Provide a simple CSV for replication and a brief methods note (epoch conversion, foreground time choice).
```

—

## Notes

- All queries assume Chrome/Edge epoch (µs since 1601‑01‑01 UTC) and use foreground time when available.
- Keep everything read‑only; publish aggregates only; redact paths and query terms where sensitive.

