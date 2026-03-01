# Codex Session Gap Analysis and Usage Recommendations

## Dataset analyzed

- Sessions scanned: **903**
- Time range: **2025-04-17** to **2026-03-01**
- File formats: legacy rollout JSON + modern JSONL
- Generated artifacts: `analysis_output/session_analysis.json`, `analysis_output/*.csv`

Method: tool calls, command patterns, durations, prompt text, model/context metadata, and release-date-aware feature checks.

## Release-note sources (refreshed 2026-03-01)

- OpenAI Codex changelog RSS: <https://developers.openai.com/codex/changelog/rss.xml>
- OpenAI Codex GitHub releases: <https://github.com/openai/codex/releases>
- OpenAI Codex CLI slash commands: <https://developers.openai.com/codex/cli/slash-commands/>
- Local snapshots: `analysis_sources/codex-changelog-rss.xml`, `analysis_sources/github-releases.json`, `analysis_sources/codex-cli-slash-command-list.txt`

## Core adoption snapshot

| Feature                                              | Sessions used | Adoption |
| ---------------------------------------------------- | ------------: | -------: |
| `skills` signal (skill prompts / SKILL.md workflows) |     468 / 903 |    51.8% |
| `update_plan` / plan mode                            |     302 / 903 |    33.4% |
| `apply_patch`                                        |     253 / 903 |    28.0% |
| `web_search` events                                  |      19 / 903 |     2.1% |
| `view_image` / image input                           |      10 / 903 |     1.1% |
| sub-agents (`spawn_agent`/`wait`)                    |       9 / 903 |     1.0% |
| `parallel` orchestration tool                        |       0 / 903 |     0.0% |
| `request_user_input`                                 |       0 / 903 |     0.0% |

## Recent feature coverage (release-aware)

This section focuses on newer Codex capabilities and checks usage after their release windows.

| Recent feature                                              | Release date | Used after release | Eligible sessions | Post-release adoption |
| ----------------------------------------------------------- | -----------: | -----------------: | ----------------: | --------------------: |
| `request_user_input` in Default mode                        |   2026-02-26 |                  0 |                25 |                  0.0% |
| `spawn_agents_on_csv`                                       |   2026-02-25 |                  0 |                28 |                  0.0% |
| Sub-agent workflows (spawn/wait/send_input/close)           |   2026-02-25 |                  3 |                28 |                 10.7% |
| `parallel` tool orchestration                               |   2026-02-04 |                  0 |                95 |                  0.0% |
| Manual shell parallelism (`&`, `xargs -P`)                  |   2026-02-04 |                 65 |                95 |                 68.4% |
| Built-in web search default behavior                        |   2026-01-28 |                 19 |               103 |                 18.5% |
| Memory slash commands (`/m_update`, `/m_drop`)              |   2026-02-12 |                  0 |                74 |                  0.0% |
| `/statusline` slash command                                 |   2026-02-11 |                  0 |                75 |                  0.0% |
| `/debug-config` slash command                               |   2026-02-05 |                  0 |                95 |                  0.0% |
| `/permissions` slash command                                |   2026-02-17 |                  0 |                65 |                  0.0% |
| `/clear` and `/copy` commands                               |   2026-02-25 |                  0 |                28 |                  0.0% |
| `/theme` slash command                                      |   2026-02-25 |                  0 |                28 |                  0.0% |
| `/experimental` slash command                               |   2026-02-26 |                  0 |                25 |                  0.0% |
| `/agent` slash command                                      |   2026-02-25 |                  0 |                28 |                  0.0% |
| `/resume` slash command                                     |   2025-09-15 |                  0 |               687 |                  0.0% |
| Voice transcription config (`features.voice_transcription`) |   2026-02-25 |                  0 |                28 |                  0.0% |
| `js_repl` experimental usage signal                         |   2026-02-26 |                  0 |                25 |                  0.0% |
| Escalated sandbox permission requests                       |   2026-02-25 |                  0 |                28 |                  0.0% |
| `gpt-5.3-codex` model usage                                 |   2026-02-05 |                 72 |                95 |                 75.8% |
| Plan mode/update_plan (as a behavior)                       |   2026-02-02 |                 13 |               100 |                 13.0% |
| Model switching commands (`--model` / `/model`)             |   2025-09-15 |                  9 |               687 |                  1.3% |
| `codex resume`                                              |   2025-09-15 |                  0 |               687 |                  0.0% |

### Additional recent signal

- You are already using **manual shell parallelism** heavily: **65 / 95** sessions after 2026-02-04.
- You adopted **`gpt-5.3-codex` quickly and heavily**: **72 / 95** sessions after its rollout window.
- This reinforces that model adoption is strong; the remaining gap is primarily workflow/interaction features.

## Recent model transition coverage

From session metadata, your recent model adoption is active and timely.

| Model                | Sessions | First seen | Last seen  |
| -------------------- | -------: | ---------- | ---------- |
| `gpt-5.2-codex`      |       79 | 2025-12-19 | 2026-02-03 |
| `gpt-5.3-codex`      |       72 | 2026-02-07 | 2026-03-01 |
| `gpt-5.1-codex-mini` |       19 | 2026-02-18 | 2026-02-23 |

Interpretation: model upgrades are not your bottleneck. Workflow features are.

## Missed-feature opportunity counts

| Opportunity                                          | Sessions flagged |
| ---------------------------------------------------- | ---------------: |
| Parallel tool calls                                  |              457 |
| `request_user_input` for approval friction           |              138 |
| Plan tracking (`update_plan`) in complex sessions    |              131 |
| Batch fan-out via sub-agents / `spawn_agents_on_csv` |               39 |
| Image workflows without image tools                  |               32 |
| Long-running work without awaiter-style delegation   |               32 |
| Structured patching (`apply_patch`) opportunity      |               17 |
| Web-search lookup opportunity (strict filter)        |                1 |

## What to use more (expanded, with recent features)

### 1) `parallel` orchestration (newer feature) instead of ad-hoc shell parallelism

**Why:** Post-release adoption is **0.0%** even though manual parallel shell patterns are high.

**Benefit:** Better controllability than raw `&` chains, cleaner failure handling, easier reproducibility.

**How:** Ask Codex to use the `parallel` tool for independent reads/checks.

**Examples where this would have helped (recent):**

- `sessions/2026/02/28/rollout-2026-02-28T11-23-34-019ca245-e0dc-7932-be83-05f3cb4ef1f1.jsonl`
- `sessions/2026/03/01/rollout-2026-03-01T10-58-58-019ca755-b66d-73a2-a19f-0603ff37f93e.jsonl`

Prompt pattern:

```txt
Run these independent checks with the parallel tool, then merge the results.
```

### 2) `spawn_agents_on_csv` for row/batch fan-out (new in Feb 2026)

**Why:** Post-release adoption is **0.0%**.

**Benefit:** Native per-row concurrency with progress/ETA; cleaner than custom batching scripts.

**How:** Convert repeated unit tasks into CSV rows and fan them out.

**Examples where this would have helped (recent):**

- `sessions/2026/02/25/rollout-2026-02-25T11-42-41-019c92e4-4e79-7b90-abd7-dbb893e21a43.jsonl`
- `sessions/2026/02/28/rollout-2026-02-28T11-23-34-019ca245-e0dc-7932-be83-05f3cb4ef1f1.jsonl`

Prompt pattern:

```txt
Create a CSV of units, use spawn_agents_on_csv per row, then aggregate into one report.
```

### 3) `request_user_input` in Default mode (new in Feb 2026)

**Why:** Post-release adoption is **0.0%**.

**Benefit:** Faster decision capture during ambiguity/approval bottlenecks without mode switching.

**How:** Ask Codex to present concise options when blocked by environment or policy constraints.

**Historical friction examples this now addresses:**

- `sessions/2025/09/07/rollout-2025-09-07T14-49-06-cd716422-2521-47e9-8cb4-9c82d94f3eb9.jsonl`
- `sessions/2025/08/26/rollout-2025-08-26T10-48-25-c42db016-0383-4985-a9a6-08fe400dd46f.jsonl`

Prompt pattern:

```txt
If you hit approval/policy ambiguity, use request_user_input with concise options and continue.
```

### 4) Memory slash commands (`/m_update`, `/m_drop`) for long-horizon threads

**Why:** Post-release adoption is **0.0%**.

**Benefit:** More controllable memory state in large, multi-phase investigations.

**How:** Explicitly update/drop memory chunks when thread scope shifts.

**Good fit sessions:** long investigative runs in Feb 2026 with very high call counts.

### 5) `/permissions` + `/debug-config` + `/statusline` for setup/debug hygiene

**Why:** All show **0.0%** post-release adoption in eligible sessions.

**Benefit:** Faster recovery from blocked directories, config precedence issues, and environment-specific behavior.

**How:** Use these early in sessions with approval friction or unexpected sandbox/config behavior.

### 6) `/agent` and `/resume` for multi-thread continuity

**Why:** Both are at **0.0%** usage despite active sub-agent workflows in a subset of recent sessions.

**Benefit:** Faster branch/return workflows without losing context.

**How:** Use `/agent` to move between active threads and `/resume` to continue prior threads directly in the CLI.

### 7) `codex resume` for repeated short retries

**Why:** Observed usage is **0**.

**Benefit:** Keeps thread context instead of restarting from scratch.

**How:** Prefer resume when retrying near-identical command loops.

**Example pattern:** repeated one-command sessions on 2026-03-01 around `annotate_images_gemini.py` runs.

### 8) `/experimental` and voice/js_repl toggles (optional, niche)

**Why:** No observed usage after release windows.

**Benefit:** Useful for advanced interactive workflows where experimental tooling is needed.

**How:** Opt in deliberately for sessions that would benefit from these capabilities; keep them off for normal tasks.

## Existing high-leverage recommendations (still valid)

### A) Parallel read calls for context collection

- Largest repeated pattern overall (457 sessions).
- Ask for parallel reads explicitly when no dependency chain exists.

### B) Keep `update_plan` active for complex tasks

- 131 sessions crossed complexity threshold without plan tracking.
- Use a short persistent plan for 20+ tool-call tasks.

### C) Delegate long-running commands to sub-agent/awaiter flows

- 32 sessions had 60s+ runs inline on main thread.
- Delegation keeps main thread responsive and reduces interruption risk.

### D) Use `view_image` more in UI/screenshot-heavy work

- Only 10 sessions used image tooling; 32 looked image/UI-heavy.
- Add a mandatory visual inspection step before finalizing UI work.

## Suggested default instruction snippet (updated)

```txt
For independent checks/reads, use parallel tool orchestration.
For batch row-wise work, prefer spawn_agents_on_csv over ad-hoc loops.
For >20 tool-call tasks, maintain update_plan continuously.
For long-running commands, delegate via sub-agent/awaiter.
If blocked by approvals/ambiguity, use request_user_input and continue.
If sandbox/config gets in the way, use /permissions and /debug-config early.
For UI/image tasks, capture screenshots and inspect with view_image.
Use /statusline for a persistent session footer that surfaces key metadata.
Use /agent and /resume when switching between active threads.
For repeated retries, prefer codex resume instead of starting fresh threads.
```

## Notes on detectability

- Some app/UI features from release notes (for example theme picker, command palette UX, drag/drop queue UX) are not fully inferable from raw session logs.
- This report marks gaps only where signals are observable in session content/tool events.
