Empirically evaluate OpenAI’s prompt caching behavior on the Chat Completions API by varying prompt length from just over 1,024 tokens up to ~2,048 tokens, using two prompting strategies, while logging headers, timestamps, and usage for reproducibility and later analysis.

## Questions To Answer

- Is every eligible request cached, or only some?
- Is there a lag before caching starts working? Roughly how long (in requests and/or seconds)?
- Does extending the prompt via a single user message vs. multiple user messages both work? Does one perform better?
- Do the documentation statements (threshold ≥1,024, 128‑token increments, TTL 5–10 min, etc.) hold in practice? Any caveats?
- Any other notable observations (latency deltas, variability, routing edge cases, rate effects)?

## Scope And Assumptions

- Endpoint: `POST /v1/chat/completions` (per provided example).
- Model: `gpt-5-nano`.
- Auth: `OPENAI_API_KEY` env var.
- Caching per docs: kicks in at ≥1,024 tokens; cached prefix grows in 128‑token increments; caches persist ~5–10 minutes (sometimes up to ~1 hour); exact prefix match across the prompt (messages array) required.
- We will not include unsupported parameters (e.g., `prompt_cache_key` appears in the Responses API, but this plan targets Chat Completions for parity with the user’s request).

## High‑Level Design

- Two strategies to extend prompts:
  1. Single user message: append content to the same user message across lengths.
  2. Multiple user messages: add new `{ role: "user" }` entries to extend the messages array while keeping the prior array unchanged as a strict prefix.
- For each strategy, probe at prompt lengths ~1,040 and 2,060 (just over the 1K and 2K boundaries), verifying that `usage.prompt_tokens_details.cached_tokens` latency/cost reflect cache hits.
- Keep completion size tiny to control costs.
- Perform “warm → hit” pairs per length to detect caching activation and lag. Add TTL checks with waits of ~1, 7, and 12 minutes to observe eviction windows.
- Maintain request rate safely below ~15 req/min per shared prefix to avoid cache overflow routing.

## Prompt Structure

- Constant system message: `"Summarize into one sentence."` (as provided).
- For the long content, use deterministic, neutral tokens (e.g., "word0001 word0002 …") to avoid moderation triggers and to make length control predictable.
- Place static, repeated content first; append variable filler at the end to achieve target token counts without altering the prefix.

## Measurements To Collect (Per Request)

- Timestamps: start, end, and elapsed milliseconds.
- Request metadata: endpoint, model, messages, any other params.
- Request headers: all headers sent (minus redaction of secrets).
- Response: HTTP status, body JSON, response headers, and especially the `usage` block including `prompt_tokens_details.cached_tokens`.
- Derived: inferred cache status (hit/miss) from `cached_tokens`, cached proportion, tokens saved, and latency deltas across warm→hit.

## Logging & Artifacts

- Cache: `cache-<id>.jsonl` with all recorded fields (request/response, headers, timings, payloads, bodies, metrics), one row per line
- Notebooks or scripts producing charts
- `REPORT.md`: final report summarizing findings, answering questions, and including visualizations

## Request Shape (Curl Template)

```bash
curl -X POST https://api.openai.com/v1/chat/completions \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
  "model": "gpt-5-nano",
  "messages": [
    { "role": "system", "content": "Summarize into one sentence." },
    { "role": "user", "content": " ..." }
  ]
}'
```

Payload fields (frozen per run): `model`, `messages`.

## Success Criteria & Expected Patterns

- First request for a new prefix: `cached_tokens ≈ 0` (miss). Immediate repeat: `cached_tokens` jumps to the nearest documented increment ≤ prompt length (1024 / 2048).
- Latency should drop on cache hits vs. warm misses (magnitude varies; we record deltas, not enforce a threshold).
- Strategy A and B should both produce cache hits, provided the prefix remains identical; any differences in `cached_tokens` or latency are noted.
- TTL behavior: after ~5–10 minutes idle, a repeat likely shows reduced or zero `cached_tokens` (evicted). During quiet windows, cache might persist longer (up to ~1 hour).
