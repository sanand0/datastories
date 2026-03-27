# Prompts

## Analyze GitHub activity, 22 Mar 2026 (Copilot Yolo - GPT 5.4 medium)

<!-- https://claude.ai/chat/d79fd3ff-9fb9-4f2a-a226-4ec1256b3c09 -->

Analyse GitHub commit activity to detect whether the release of Opus 4.5 in Nov 2025 caused a measurable increase in developer activity, i.e. are there several GitHub users who were less active before Nov 2025 and then became much more active after?

Using the GitHub REST API (authenticated) using the GitHub token in .env, sample ~1,000 developers and compare their commit activity across two time windows to test whether a structural break exists — and if so, when it occurs.

**Goal**: Determine (a) what fraction of developers became significantly more active after a hypothesised date, and (b) whether the data itself points to a different change-point.

**Data collection**

Seed a user sample via `/search/commits` — bias toward users who were active _before_ the hypothesised break so you're not sampling on the outcome. For each user, get commit counts for two equal-length windows (pre and post) using the `per_page=1` + `Link` header trick to avoid fetching full commit lists. Filter out bots (`type: User`), forks of tutorial repos, and accounts with no pre-window activity.

Rate limit budget: 5,000 req/hr with one authenticated token. Design the collection to stay comfortably within this.

**Analysis**

- Classify users into cohorts: dormant returners, newly active, consistently active, declining
- Aggregate weekly/monthly commit counts across the cohort over ~12 months
- Run change-point detection (e.g. `ruptures` with PELT) on the aggregate time series — don't assume the break date, let the data find it
- Report what % of developers showed a meaningful increase, and the detected break date(s)

Use your judgement on repo quality filters, statistical thresholds for "meaningful increase", and how to handle users with sparse histories. Output should be a clear summary with the key numbers, plus the underlying data saved for further analysis.

Document your findings in `results.md`.

---

I modified .env to be in a KEY=VALUE format. Simplify code accordingly.
Is there a way to be more time and API efficient? Experiment.
There may be a MEANINGFUL DECREASES as well for some users - so measure this symmetrically.
Extend the analysis to another batch of <1,000 users.
Update results.md.

---

To conclude whether there was a surge in activity (or a decline), is the way we select users biased? How can we (efficiently) de-bias this? Is the size of data collected large enough?

Revise and re-run as required.

Apply the data-analysis skill - specifically the verification and stress-test mechanisms. Based on such rigor, what CAN we conclude with confidence from our analysis?

---

Rewrite results.md as if writing for the first time, rather than as a revision.
Document the entire final process - what you did, how, what you found, and what that implies.
In clear language, write enough detail for a journalist or researcher to replicate and document the analysis.

Then, run a blameless post-mortem on this entire conversation to improve future performance.

1. Document the entire process so far (what you did, how, what you found, next steps, etc.).
2. List successes: techniques / approaches you discovered that worked well. Examples: tools, code snippets, prompt structures, planning techniques. Share what change to the environment / prompts will make it easier to repeat these successes in the future.
3. List problems faced: failures, inefficiencies and mis-alignments. E.g. commands that failed or behaved unexpectedly, corrections, more steps than necessary, where you adhered to the letter not spirit, took shortcuts that compromised quality, etc. Dig deep for root causes. Mention the PRACTICAL impact. Suggest pragmatic & safe fixes (if any) to prompts, skills, or environment (e.g. tools, .env) at a root cause level - preferably that resolve **entire classes/patterns of failures**, not just a specific instance.

Create or append to `notes.md` as `## Post mortem (%d %b %Y)` with today's date.

<!-- copilot --resume=b0452c27-504c-426c-a5bf-f72fa3298a9c -->

## Data Story

Generate a beautiful narrative story using the analysis in this folder (read files as required beginning with prompts.md) as a self-contained single-page index.html.

There was a lot of discussion online about how, around November 2025, when Opus 4.5 and GPT 5.2 Codex were released, vibe coding became much easier (which might be true) and how a lot of developers who had not coded for a while started returning to coding (e.g. famous founders). Find and link to references to these and talk about it.

The question I'm addressing is whether developers who were not actively using GitHub actually started using GitHub more, around Nov 2025. In other words, how data-backed are these anecdotes?

Write in the engaging style of Malcolm Gladwell, weaving in anecdotes, insights, and a compelling narrative arc. Use an engaging design.

Search online for additional context, relevant references, research, supporting material, etc. Link to these liberally.

Prominently include sketchnote.avif near the top. Clicking on it should open the full-size image in a new tab

Feel free to add tooltips and popups as informative and engaging aids.

**Tooltips** are for:

- Context about non-obvious terms or phrases (only if relevant and useful)
- Additional context about references (where possible)

**Popups** are for:

- Citations. Search for and include references. Cite the key point from the reference and link to it.
- Supporting material. Provide extensive context, quotes, extracts from slides, external references, etc. Render Markdown content as HTML.

This will be deployed at https://sanand0.github.io/datastories/github-usage-increase/

---

Mention individual developers who had a significant increase in activity, and link to their profiles and notable commits. This will help humanize the story and provide concrete examples. If any other segments would benefit from specific examples, add those as well.

Include sortable tables of analysis/stats if that will help enhance the story. (You don't HAVE to. Only if and where it really adds value.)

Add concrete takeaways at the end.

The .cite-btn elements are too small. Make them bigger or, if it'll be better, use text links for the popups.

<!-- claude --resume f452cd39-e26d-41fe-9163-079eba1338b9 -->

## Sketchnote

<!-- Gemini Pro - https://gemini.google.com/u/2/app/5fd872914713c730 -->

Draw this as a visually rich, intricately detailed, colorful, and funny, sketchnote.
Think about the most important points, structure it logically so that the sketchnote is easy to follow, then draw it.
