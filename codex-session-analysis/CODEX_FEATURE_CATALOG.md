# Codex Feature Catalog (from release notes)

_Last updated from sources on 2026-03-01._

## Scope

This catalog is compiled from:

- Official Codex changelog (app + CLI + integrations)
- Official `openai/codex` GitHub releases
- OpenAI Codex announcement pages linked from the changelog

## Latest feature drops (most recent first)

### 2026-02-26 (Codex CLI 0.106.0 / Codex app 26.226)

- `request_user_input` enabled in **Default** mode (not only Plan mode).
- Direct macOS/Linux install script published as release asset.
- App-server v2 thread realtime extensions (`thread/unsubscribe`, thread-scoped realtime notifications).
- `js_repl` promoted to experimental with startup compatibility checks.
- Better memory behavior (diff-based forgetting + usage-aware selection).
- App-side MCP quality-of-life: composer MCP shortcuts and inline skill mentions.

### 2026-02-25 (Codex CLI 0.105.0)

- `spawn_agents_on_csv` for fan-out workloads with progress/ETA.
- Better sub-agent ergonomics in TUI (nicknames, picker, prompts).
- Voice dictation in TUI (feature-flagged).
- New TUI commands: `/copy`, `/clear` (+ `Ctrl-L`).
- More flexible approval controls (extra sandbox permissions, granular auto-reject policies).

### 2026-02-02 to 2026-02-12

- Plan mode defaulted on in CLI.
- Codex app launch wave: multitasking, worktrees, automations, built-in Git tooling, voice dictation.
- GPT-5.3-Codex and GPT-5.3-Codex-Spark support surfaced in app/CLI/IDE.

### 2026-01-28

- Web search defaulted on for CLI/IDE with `cached`/`live`/`disabled` modes.

### 2025-12-19

- Agent skills introduced (folder standard with `SKILL.md`, optional scripts/references/assets).

### 2025-10-06 (GA milestone)

- Codex GA with Slack integration, Codex SDK, and new admin controls.

## Comprehensive capability catalog

### 1) Planning and control

| Capability                           | Surface                |               Introduced | What it enables                                             |
| ------------------------------------ | ---------------------- | -----------------------: | ----------------------------------------------------------- |
| Plan mode (default)                  | CLI                    |               2026-02-02 | Structured multistep execution and plan tracking by default |
| Mid-turn steering                    | App + CLI (steer mode) |               2026-02-05 | Adjust direction while a task is running                    |
| `request_user_input` in Default mode | CLI                    |               2026-02-26 | Ask concise decision questions without switching modes      |
| `/copy`, `/clear`, `Ctrl-L`          | CLI                    |               2026-02-25 | Faster iteration and transcript hygiene                     |
| `/statusline`, `/debug-config`       | CLI                    | 2026-02-05 to 2026-02-11 | Runtime introspection and config debugging                  |

### 2) Multi-agent execution

| Capability                                     | Surface          |       Introduced | What it enables                                   |
| ---------------------------------------------- | ---------------- | ---------------: | ------------------------------------------------- |
| Sub-agents (spawn/wait/close flows)            | CLI + app-server | 2025-2026 series | Delegate scoped tasks while main thread continues |
| `spawn_agents_on_csv`                          | CLI              |       2026-02-25 | Parallel row-wise fan-out jobs with progress/ETA  |
| Customizable multi-agent roles                 | CLI config       |       2026-02-17 | Standardized role behavior for team workflows     |
| Better sub-agent UX (nicknames/picker/prompts) | CLI              |       2026-02-25 | Lower coordination overhead in multi-agent tasks  |

### 3) Tooling and execution runtime

| Capability                                        | Surface              |                       Introduced | What it enables                                      |
| ------------------------------------------------- | -------------------- | -------------------------------: | ---------------------------------------------------- |
| Shell tool parallel execution support             | CLI                  |                       2026-02-04 | Higher throughput for independent command work       |
| Unified exec stabilization                        | CLI                  |                      2026-02-04+ | Better long-running command handling and I/O control |
| `apply_patch` reliability improvements            | Model + CLI behavior |                       2025-11-06 | Safer, less destructive edits                        |
| JS REPL tool (`js_repl`)                          | CLI (experimental)   | 2026-02-12 (promoted 2026-02-26) | Stateful JS runtime across tool calls                |
| Multiple attachment types (incl. GIF/WebP images) | App/CLI              |         2026-02-05 to 2026-02-11 | Richer multimodal debugging and instruction          |

### 4) Memory, context, and session continuity

| Capability                                           | Surface | Introduced | What it enables                         |
| ---------------------------------------------------- | ------- | ---------: | --------------------------------------- |
| `codex resume`                                       | CLI     | 2025-09-15 | Re-open prior sessions quickly          |
| Context compaction                                   | CLI     | 2025-09-15 | Auto-summary near context-window limits |
| Memory slash commands (`/m_update`, `/m_drop`)       | CLI     | 2026-02-12 | Explicit thread memory management       |
| Diff-based forgetting + usage-aware memory selection | CLI     | 2026-02-26 | Better long-horizon memory quality      |

### 5) Web and external retrieval

| Capability                                | Surface              | Introduced | What it enables                                    |
| ----------------------------------------- | -------------------- | ---------: | -------------------------------------------------- |
| Built-in web search (`cached` / `live`)   | CLI/IDE              | 2026-01-28 | Up-to-date lookups without manual `curl` flows     |
| Cloud internet access controls            | Codex cloud/app      | 2025-06-03 | Controlled dependency install and external fetches |
| Team/admin network constraints via config | CLI enterprise/admin | 2026-02-11 | Governance over web/search/network usage           |

### 6) Skills and reusable workflows

| Capability                                         | Surface   |               Introduced | What it enables                               |
| -------------------------------------------------- | --------- | -----------------------: | --------------------------------------------- |
| Agent skills (`SKILL.md` standard)                 | CLI + IDE |               2025-12-19 | Reusable domain workflows with scripts/assets |
| Skills from `.agents/skills` + compatibility paths | CLI       | 2026-02-02 to 2026-02-04 | Better portability and local skill discovery  |
| Live skill file change pickup                      | CLI       |               2026-02-05 | Iterating on skills without restarting Codex  |

### 7) Configuration and governance

| Capability                                                 | Surface     |         Introduced | What it enables                                        |
| ---------------------------------------------------------- | ----------- | -----------------: | ------------------------------------------------------ |
| Team Config layering (`.codex/` hierarchy)                 | CLI         |         2026-01-23 | Shared defaults/rules/skills across repos and machines |
| Managed requirements and provenance-aware constraints      | Admin + CLI | 2026-01 to 2026-02 | Central governance with debuggable source priority     |
| Granular approval policies (including auto-reject classes) | CLI         |         2026-02-25 | Safer command execution controls                       |
| Permission UX improvements + history                       | CLI/app     |      2026-02 cycle | Lower approval friction and clearer auditability       |

### 8) App / IDE / integration surface

| Capability                                            | Surface            |  Introduced | What it enables                             |
| ----------------------------------------------------- | ------------------ | ----------: | ------------------------------------------- |
| IDE extension (VS Code/Cursor/Windsurf compatibility) | IDE                |  2025-08-27 | In-editor Codex workflows                   |
| Local ↔ cloud handoff                                 | IDE + web app      |  2025-08-27 | Shift work between environments             |
| Codex code review workflows                           | App + GitHub       | 2025-08-27+ | Intent-aware, executable reviews            |
| `@codex` in GitHub Issues/PRs                         | GitHub integration |  2025-10-22 | Trigger/follow-up tasks in repo workflow    |
| `@codex` in Slack                                     | Slack integration  |  2025-10-06 | Team tasking from chat                      |
| Linear integration                                    | Codex integration  |  2025-12-04 | Start and track cloud tasks from Linear     |
| Codex SDK + GitHub Action                             | Automation         |  2025-10-06 | Embed Codex agent runs in apps/CI pipelines |

### 9) Model-line features relevant to usage

| Model milestone      | Introduced | Practical impact                                                         |
| -------------------- | ---------: | ------------------------------------------------------------------------ |
| GPT-5-Codex          | 2025-09-15 | Stronger agentic coding baseline + image outputs in cloud frontend tasks |
| GPT-5-Codex-Mini     | 2025-11-07 | Cost/throughput fallback option                                          |
| GPT-5.1-Codex + Mini | 2025-11-13 | Updated long-horizon coding capability                                   |
| GPT-5.1-Codex-Max    | 2025-11-18 | Higher reasoning ceiling (`xhigh`)                                       |
| GPT-5.2-Codex        | 2025-12-18 | Better long-horizon/refactor/cyber performance                           |
| GPT-5.3-Codex        | 2026-02-05 | New generation model option in app/IDE/CLI                               |
| GPT-5.3-Codex-Spark  | 2026-02-12 | Additional model variant for coding workflows                            |

## Notes for practical use

- Not all release-note items map directly to local-session logs (for example, app UI improvements, enterprise admin dashboards, and cloud-only behaviors).
- For session optimization, the highest leverage features are generally: `update_plan`, sub-agents (`spawn_agent`, `spawn_agents_on_csv`), `request_user_input`, `view_image`, and web search mode control.

## Sources

- Codex changelog: https://developers.openai.com/codex/changelog
- Codex GitHub releases: https://github.com/openai/codex/releases
- Introducing Codex: https://openai.com/index/introducing-codex/
- Introducing upgrades to Codex: https://openai.com/index/introducing-upgrades-to-codex/
- Codex GA: https://openai.com/index/codex-now-generally-available/
- Introducing the Codex app: https://openai.com/index/introducing-the-codex-app/
- Introducing GPT-5.2-Codex: https://openai.com/index/introducing-gpt-5-2-codex/
- Introducing GPT-5.3-Codex: https://openai.com/index/introducing-gpt-5-3-codex/
- Introducing GPT-5.3-Codex-Spark: https://openai.com/index/introducing-gpt-5-3-codex-spark/
