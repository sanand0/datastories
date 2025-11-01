---
sources:
  plan: /home/sanand/.codex/sessions/2025/10/31/rollout-2025-10-31T11-48-32-019a38ea-f27e-7760-a70b-d9a6a5694bae.jsonl
  execute: ~/.codex/sessions/2025/10/31/rollout-2025-10-31T13-10-21-019a3935-d960-7183-b797-3b6d93bdec80.jsonl
---

# Does OpenAI Cache Prompts as documented?

When manually exploring [prompt caching](https://platform.openai.com/docs/guides/prompt-caching) I was surprised when my prompt wasn't cached immediately. So I had Codex run an experiment to verify the caching behavior.

[I gave it a detailed prompt](prompt.md) to create a plan.

The plan was too verbose and I realized I didn't want to waste tokens testing every 128 token step. So I [revised it to this plan](plan.md).

Then I had Codex execute the experiment. Here is the final report.

> Summary: Caching has variable lag and expiry, but works with single as well as multi-message prompts. Documentation is mostly accurate.

I find this powerful as a means of creating repeatable experiments.

## Prompt Caching Experiment Summary

- **Run ID:** `third`
- **Log file:** [`data/cache-third.jsonl`](data/cache-third.jsonl)
- **Summary table:** [`data/cache-third-summary.md`](data/cache-third-summary.md)
- **Model:** `gpt-5-nano`
- **Endpoint:** `POST /v1/chat/completions`
- **Prompt scaffolding:** constant system message `"Summarize into one sentence."` plus deterministic `wordNNNN` filler.
- **Tested lengths (total prompt tokens):**
  - `approx_1040`: ~1,170 tokens
  - `approx_2048`: ~2,130 tokens

### Key Findings

1. **Eligibility and hit rate**
   - Warm requests show `cached_tokens = 0` as expected.
   - Both strategies surpassed the 1,024-token threshold and produced cache hits, but not uniformly:
     - Single-message, ~1.17k tokens: immediate repeat cached 1,024 tokens.
     - Multi-message, ~1.17k tokens: immediate repeat cached 1,152 tokens.
     - Single-message, ~2.13k tokens: immediate repeat did **not** show cached tokens; the first probe 60s later cached 1,024 tokens.
     - Multi-message, ~2.13k tokens: immediate repeat cached 2,176 tokens.
   - **Conclusion:** not every eligible request yields an immediate hit. Larger single-message prompts exhibited a short-lived miss before cache usability.

2. **Lag before cache availability**
   - Single-message ~2.13k prompt required ~60 seconds before cached tokens appeared (immediate repeat miss, `ttl_probe_1` hit).
   - Multi-message prompts hit the cache on the first repeat, suggesting the lag is scenario-dependent.

3. **Prompt construction strategies**
   - **Single message extension:** Works above threshold; hit size rounded down to 128-token step (1,024 tokens returned for a 1,170-token prompt).
   - **Multiple user messages:** Also works and cached more tokens (1,152 and 2,176) because the prefix comprises more 128-token segments. Cached totals remained multiples of 128.
   - No consistent latency savings observed—cached calls sometimes took similar or longer wall-clock time (network variance dominates, ranges 1.1–2.3 s).

4. **Documentation validation**
   - **Threshold ≥ 1,024 tokens:** confirmed—hits only appear for prompts above 1,024 (our 1,170-token prompt hit).
   - **128-token increments:** confirmed—`cached_tokens` values were 1,024, 1,152, and 2,176.
   - **TTL 5–10 minutes:** cache entries expired between 60 s and 360 s in these runs. Both strategies lost their cache by the 6-minute probe (`ttl_probe_2`). Cache persistence beyond ~1 minute but under 6 minutes matches “5–10 minute” guidance in spirit, though the earliest expiry was closer to 60 s.
   - **Exact prefix match requirement:** met by construction; hits only occurred when reusing the identical prefix.

5. **Other observations**
   - `prompt_tokens_details.audio_tokens` always 0, confirming no audio contribution.
   - `completion_tokens_details.reasoning_tokens` consistently 16 (matching `max_completion_tokens`), demonstrating completions were stable and minimal.
   - `x-ratelimit` headers remained high; no evidence of throttling at the exercised rate (≤ 8 req/hour).
   - Occasional higher latency for cached repeats suggests backend routing variance; caching doesn’t guarantee faster replies in absolute terms.

### Answers to Guiding Questions

- **Is every eligible request cached?**
  No. The single-message ~2k-token prompt missed on the immediate repeat and only became cacheable ~60 s later.

- **Is there a lag before caching starts working?**
  Sometimes. For single-message ~2k prompt a lag of roughly one minute was observed. Multi-message prompts hit immediately.

- **Single vs multiple user messages?**
  Both strategies produce cache hits when over threshold. Multi-message prompts returned larger cached slices (2,176 vs. 1,024) because they align better with 128-token chunking, but they did not consistently reduce latency.

- **Do documentation statements hold?**
  - Threshold ≥1,024 and 128-token increments: yes.
  - TTL: cache survived past 60 seconds but cleared by 6 minutes here—shorter than the 5–10 minute range on one run, so expect variability.
  - Exact prefix match: required; confirmed by experiment design.
  - TTL variability and short initial lag are caveats to note.

- **Other notable observations?**
  - Latency remained variable (1.1–2.3 s) even on cache hits.
  - Cached token counts differ by strategy due to message segmentation.
  - Some cache entries appear asynchronously—plan for a brief delay before assuming cache availability after the first warm request.

### Reproduction Notes

- Run [`scripts/run_cache_eval.py`](scripts/run_cache_eval.py) with an `OPENAI_API_KEY` in the environment to regenerate logs.
- Use `scripts/analyze_cache_data.py data/cache-third.jsonl --output-path data/cache-third-summary.md` to rebuild the Markdown tables.
- Logs capture request/response headers, timestamps, response bodies, and inferred cache status for each API call.
