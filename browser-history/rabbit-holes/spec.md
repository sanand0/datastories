Claude, tell an intimate story about focus: how a single spark becomes a journey. Make readers feel the momentum of a rabbit hole — curiosity tightening into flow — and the tenderness of losing it. Celebrate deep dives, avoid shaming detours.

Effect/mood to evoke
- Momentum: chains that gather force and coherence.
- Texture: some journeys are tight spirals, others are branching explorations.
- Reflection: name the themes without reducing them to productivity.

Using/redoing the analysis
- Prefer Edge’s on-device “Journeys” clusters (`clusters`, `clusters_and_visits`) when populated; otherwise fall back to pure graph walks over `visits.from_visit`.
- Re-run SQL on a read-only copy of the History DB (or `file:$HOME/.config/microsoft-edge/Default/History?mode=ro&immutable=1`). If your environment restricts temp files, set `SQLITE_TMPDIR` to a writable folder.
- Foreground time from `context_annotations.total_foreground_duration` (µs). Time bounds via min/max timestamps per journey/chain.

What each CSV contains and how it was generated
- chains_summary.csv — one row per root `from_visit` chain with visit_count, distinct_domains, start/end timestamps (UTC), duration_sec, total_foreground_sec; built via a recursive CTE that walks `from_visit` from roots.
- chain_depths.csv — per chain, maximum depth (longest branch) and total_nodes; useful to pick the most “rabbit‑hole‑ish” journeys.
- If `clusters*` tables are non-empty, you can also compute the cluster-level summaries (`clusters_summary.csv`, `cluster_depths.csv`).

You choose how to let the journeys breathe — highlight 3–5 archetypes with short captions drawn from titles/domains.
