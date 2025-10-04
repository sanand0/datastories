Claude, craft a visual story that helps a reader feel the calm clarity of seeing where their attention really goes across the day — not as a guilt graph, but as a humane rhythm. The tone should be reflective, restorative, and practical: an invitation to adjust routines, not a judgment.

Effect/mood to evoke
- A gentle, circadian pulse: mornings that ramp, afternoons that ebb, evenings that exhale.
- A sense of agency: “I can shift one hour to do deep work.”
- Relief from overwhelm: the pattern is intelligible, not chaotic.

Using/redoing the analysis
- The data comes from Edge’s History DB (read-only). You can re-run the SQL below on `file:$HOME/.config/microsoft-edge/Default/History?mode=ro&immutable=1`.
- Convert Chromium microseconds to UTC with: `datetime(visit_time/1000000-11644473600,'unixepoch')`; use `localtime` for local clocks.
- Prefer `context_annotations.total_foreground_duration` over `visits.visit_duration`. If null/0, treat as 0 (unknown, not zero attention).
- Exclude subframes: `(visits.transition & 255) NOT IN (3,4)`.

What each CSV contains and how it was generated
- attention_by_hour.csv — rows per weekday (0=Sun..6=Sat) and hour (00–23); columns: dow, hour, visits, seconds (sum of foreground). Generated via a GROUP BY on `strftime('%w', ts, 'localtime'), strftime('%H', ts, 'localtime')`.
- attention_by_day.csv — rows per calendar date (local); columns: date, visits, seconds. Useful to annotate specific days.
- domain_top.csv — top domains across the period with visits, total foreground seconds, unique days; helpful for captions and examples.

Keep the visual choice yours; aim for serenity + legibility over spectacle.
