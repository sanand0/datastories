# The Story Of Your Codex Sessions

Imagine two versions of the same power user.

- Version A works fast, writes a lot of code, and gets things done.
- Version B does all of that too, but also uses Codex’s newest workflow features to save hours each week.

This project is about the gap between A and B, using your own session history as evidence.

## What We Did (In Plain English)

We took your historical Codex sessions, read them, and asked:

1. Which Codex features are you already using?
2. Which newer features did you not use, even when they were available?
3. Where are the biggest missed opportunities?

To do that, we built and ran an analyzer:

- Main script: [`analyze_codex_sessions.py`](./analyze_codex_sessions.py)
- Session gap report: [`CODEX_SESSION_GAP_ANALYSIS.md`](./CODEX_SESSION_GAP_ANALYSIS.md)
- Feature catalog: [`CODEX_FEATURE_CATALOG.md`](./CODEX_FEATURE_CATALOG.md)

## What We Found

### The headline

You are excellent at adopting new **models** quickly, but you are under-using new **workflow commands/tools**.

### The evidence

- Sessions analyzed: **903**
- Time span: **April 17, 2025 to March 1, 2026**
- Missed-feature opportunities detected: **847**

Strong adoption:

- `gpt-5.3-codex` after release: **72 / 95 sessions** (75.8%)
- Manual shell parallelism (`&`, `xargs -P`): **65 / 95 sessions** (68.4%)

Low or zero adoption (despite eligibility):

- `parallel` orchestration tool: **0 / 95**
- `spawn_agents_on_csv`: **0 / 28**
- `request_user_input` in Default mode: **0 / 25**
- `/permissions`, `/debug-config`, `/statusline`, `/agent`, `/resume`: effectively **0** in eligible windows

Top missed opportunities:

- Parallel tool calls: **457 sessions**
- `request_user_input` for approval friction: **138 sessions**
- Plan tracking in complex sessions: **131 sessions**

You can see these numbers directly in:

- JSON output: [`session_analysis.json`](./session_analysis.json)
- Recent-feature table: [`recent_feature_coverage.csv`](./recent_feature_coverage.csv)
- Full opportunities list: [`opportunities.csv`](./opportunities.csv)

## Why This Matters

The pattern is clear:

- You already think in parallel.
- You already handle large, complex coding work.
- You already keep up with model upgrades.

So the easiest wins now are not “work harder” wins. They are “use the right Codex knobs” wins:

- `parallel` for independent checks
- `spawn_agents_on_csv` for repeat/batch tasks
- `request_user_input` when blocked by approvals/ambiguity
- `/permissions` + `/debug-config` early when environment friction appears

That is exactly where the current gap lives.

## How To Use This Repo

### 1) Re-run the analysis

```bash
uv run analyze_codex_sessions.py \
  --session-root /path/to/sessions \
  --changelog-txt /path/to/codex-changelog.txt \
  --out-dir .
```

### 2) Read the narrative reports

- Main recommendations: [`CODEX_SESSION_GAP_ANALYSIS.md`](./CODEX_SESSION_GAP_ANALYSIS.md)
- Full feature inventory: [`CODEX_FEATURE_CATALOG.md`](./CODEX_FEATURE_CATALOG.md)

### 3) Drill into raw outputs only if needed

- Machine-readable summary: [`session_analysis.json`](./session_analysis.json)
- Recent feature adoption matrix: [`recent_feature_coverage.csv`](./recent_feature_coverage.csv)
- Opportunity list: [`opportunities.csv`](./opportunities.csv)

## If You Only Do Three Things Next

1. Start asking Codex explicitly for `parallel` tool orchestration on independent checks.
2. Use `spawn_agents_on_csv` for repeatable row-by-row work.
3. In blocked sessions, tell Codex to use `request_user_input` instead of stalling.

That combination closes the biggest measured gaps with the least behavior change.
