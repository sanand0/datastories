## Post mortem (23 Mar 2026)

### 1. Entire process so far

This project began as a request to test whether GitHub developer activity increased after November 2025, using authenticated GitHub REST API sampling and a structural-break analysis.

The work unfolded in several phases.

#### Phase 1: initial pipeline design

I first planned a pipeline around:

- seeding users from `/search/commits`
- measuring pre/post activity in equal windows around `2025-11-01`
- building a monthly time series for change-point detection
- documenting the results in `results.md`

I created `scripts/github_activity_analysis.py` and initially tried to use commit search counts directly for per-user activity.

#### Phase 2: first major correction — search counts were unreliable

The first counting approach was flawed.

I tried global commit search queries like:

- `author:<login>`
- `author-email:<email>`

Those produced implausible totals for some users, including counts in the millions, which made it clear the method was not trustworthy for direct user-level measurement.

I then switched to a more reliable method:

- use `/search/commits` only for seeding
- use `/repos/{owner}/{repo}/commits` with `per_page=1` plus `Link` headers for counting

This was a strong correction. It fixed an entire class of bad measurements.

#### Phase 3: first large sample

I collected a first large batch of users seeded from `May-Oct 2025`.

That required handling:

- search rate limits
- transient API failures (`500`)
- persistent search budget constraints
- resumable writes to CSV files

The final first large batch yielded:

- `900` eligible users in batch 1
- then a distinct page-2 overlap batch of `700` users
- combined overlap-seeded total: `1,600` eligible users

I also built a smaller monthly panel for structural-break analysis.

#### Phase 4: robustness and heavy-tail discovery

Initial aggregate results seemed mildly positive, but robustness checks showed this was misleading.

The important discovery was that a very small number of users dominated aggregate commit volume. In the overlap-seeded monthly panel, the top 10 users generated most of the total commits.

This meant:

- raw totals could drift upward
- even if the typical user did not become more active

That changed the interpretation of the monthly evidence.

#### Phase 5: efficiency experiments

I tested whether the collection could be made cheaper without changing user-level conclusions.

The main experiment compared:

- counting up to 2 observed repos per user
- counting just the primary observed repo

Result:

- the primary repo captured a median of 100% of both pre and post counts
- one-repo labels agreed with two-repo labels about 99.8% of the time

That was one of the most useful findings operationally, because it cut future API cost roughly in half.

#### Phase 6: bias diagnosis

The user then asked the right methodological question: was the sample construction itself biased?

The answer was yes.

The original seed window overlapped the pre-comparison window:

- seed period: `May-Oct 2025`
- pre window: `Aug-Oct 2025`

That means the design selected users who were active very near the break date. This created a serious regression-to-the-mean risk and could mechanically inflate the measured decline rate.

I diagnosed this by:

- comparing results across batches
- computing decline rates by pre-activity quintile
- showing that users with higher pre counts were much more likely to “decline” afterward

#### Phase 7: debiased sensitivity cohorts

To address the overlap bias efficiently, I added parameters so the seed period could be moved earlier.

I then collected new cohorts from:

- `Mar-Apr 2025`, page 1
- `Mar-Apr 2025`, page 2

while excluding users already seen in the overlap-seeded batches.

This produced a smaller but better debiased sensitivity sample:

- `109` users in `earlyseed`
- `53` users in `earlyseed_p2`
- combined earlier-seeded total: `162`

#### Phase 8: final verification and stress testing

I then ran the key verification layer:

- overlap-seeded vs earlier-seeded comparison
- Wilson confidence intervals
- regression-to-the-mean quintile table
- change-point comparisons on monthly panels
- placebo break-month sweep

This produced the final defensible interpretation:

- meaningful increases were consistently around 6%
- the “surge” story did not survive scrutiny
- the “decline” story was plausible but too selection-sensitive to quantify precisely

#### Phase 9: final documentation

I rewrote `results.md` from scratch as a standalone report for a journalist or researcher, including:

- research question
- data collection method
- replication commands
- bias discussion
- findings
- limitations

This `notes.md` entry documents the process and what to improve next time.

### 2. Successes

These techniques worked especially well.

#### A. Using search for discovery and repo endpoints for counting

This was the most important architectural correction.

What worked:

- `/search/commits` to find candidate developers
- repo commits endpoint for actual counts

Why it worked:

- search is good for sampling
- repo endpoints are better for reliable per-user counting

What would make this easier next time:

- prompt should explicitly say: “Use search endpoints for sampling only; validate any counting method against a second endpoint before scaling.”

#### B. Resumable batch outputs

Persisting intermediate CSVs under batch folders was extremely helpful.

What worked:

- `seed_observations.csv`
- `seed_candidates.csv`
- `user_windows.csv`
- `monthly_user_counts.csv`
- `collection_metadata.csv`

Practical impact:

- long runs could resume safely
- reruns did not waste all previous work
- later verification could reuse old data instead of recollecting everything

What would make this easier next time:

- environment/prompt should encourage “batch-aware, resumable outputs” from the start for any API-heavy project

#### C. One-repo validation experiment

This was a high-value technique.

What worked:

- validate a cheaper approximation against a more expensive method before reusing it

Practical impact:

- reduced API cost meaningfully
- allowed collecting additional debiased cohorts

What would make this easier next time:

- prompt should explicitly request one “cost-down experiment” early in the workflow, not after the main collection

#### D. Debiased sensitivity sample

Moving the seed window earlier was the correct methodological stress test.

What worked:

- non-overlapping seed period
- exclusion of already-seen users
- same pre/post windows for comparison

Practical impact:

- revealed that the increase estimate was stable
- revealed that the decline estimate was sampling-sensitive

What would make this easier next time:

- the initial prompt/environment should flag overlap bias as a standard risk whenever sample construction and comparison windows overlap

#### E. Placebo break-month sweep

This was a simple but very effective stress test.

What worked:

- compare the hypothesized break month to nearby placebo months

Practical impact:

- showed November was not special on the increase metric
- strengthened the “no broad surge” conclusion

What would make this easier next time:

- the data-analysis workflow should include a default “placebo date sweep” step whenever a user supplies a hypothesized intervention date

### 3. Problems faced

This section is intentionally blameless. The goal is not to point fingers, but to identify root causes and improve future runs.

#### Problem 1: wrong early counting method

What happened:

- I initially used commit search counts (`author:` / `author-email:`) as if they were trustworthy user-level totals

Root cause:

- I moved too quickly from “search can find users” to “search can also count users”
- I did not validate the first counting approach on a few known cases before scaling it

Practical impact:

- wasted time
- misleading early outputs
- extra iterations before trustworthy collection began

Safe fix:

- add a standing rule to the prompt/skill:
  - “Before scaling any API counting method, validate it on 3–5 concrete cases and compare against an alternative endpoint.”

This would prevent an entire class of measurement failures.

#### Problem 2: `.env` handling was more complicated than necessary

What happened:

- the first version of the code tolerated multiple token names and nonstandard export-like shapes

Root cause:

- I optimized for flexibility before understanding the actual environment

Practical impact:

- extra complexity in code
- extra debugging time

Safe fix:

- standardize `.env` early and document it clearly:

```bash
GITHUB_TOKEN=...
```

- prompt/environment should state whether `.env` is guaranteed to be standard `KEY=VALUE`

#### Problem 3: too much time spent on overlap-seeded users before debiasing

What happened:

- I collected a large overlap-seeded sample before fully interrogating whether that design biased the decline estimate

Root cause:

- I focused first on statistical power
- I did not foreground the risk that the seed window overlapped the pre window

Practical impact:

- the large sample was still useful
- but it overinvested in a design whose decline interpretation later needed qualification

Safe fix:

- for any before/after study, force an explicit “bias audit” before the first large run:
  - overlap between seed and outcome windows
  - selection on recent activity
  - regression to the mean
  - survivorship bias
  - heavy-tail concentration

This should be a required checklist in the data-analysis workflow.

#### Problem 4: late discovery of heavy-tail dominance

What happened:

- the raw monthly aggregate looked mildly positive at first
- only later did the concentration analysis show that a few users dominated the totals

Root cause:

- I initially treated aggregate movement as potentially meaningful before measuring concentration

Practical impact:

- early interpretation was too generous to the raw aggregate
- later rewrite was necessary

Safe fix:

- always compute concentration metrics early for behavioral count data:
  - top 1%, top 5%, top 10-user shares
  - median vs mean
  - winsorized variants

This should be part of the default analysis template.

#### Problem 5: too much iterative debugging inside the main thread

What happened:

- several implementation pivots happened sequentially:
  - search counts
  - repo counts
  - rate-limit pacing
  - batch handling
  - debiasing

Root cause:

- I was solving method and implementation issues interleaved, rather than isolating the riskiest assumptions earlier

Practical impact:

- more backtracking than ideal
- more user-visible pivots

Safe fix:

- for future API studies, separate the workflow explicitly:
  1. method validation on tiny sample
  2. cost-down experiment
  3. bias audit
  4. scale-up collection
  5. verification

That structure would reduce repeated redesign.

#### Problem 6: some conclusions were stated too confidently before full verification

What happened:

- earlier drafts leaned toward a stronger decline conclusion before the overlap bias was fully stress-tested

Root cause:

- the initial large sample was precise enough to look persuasive
- but precision in a biased estimand is still misleading

Practical impact:

- `results.md` had to be rewritten multiple times
- interpretive confidence shifted materially

Safe fix:

- prompt/skill should remind:
  - “High precision is not high validity if the estimand is biased.”
- require a “what would change this conclusion?” section before final write-up

### Root-cause improvements for future work

These changes would improve future performance across an entire class of similar tasks.

#### Prompt improvements

Add explicit instructions like:

- “Validate the counting method before scaling.”
- “Audit sample-selection bias before the first large run.”
- “If a hypothesized break date is given, run placebo break-month checks.”
- “For heavy-tailed behavioral data, compute trimmed, winsorized, median-based, and concentration-based variants by default.”

#### Environment improvements

- Standardize `.env` to `KEY=VALUE`
- Document one canonical token name: `GITHUB_TOKEN`
- Pre-install common analysis dependencies used repeatedly here:
  - `pandas`
  - `numpy`
  - `ruptures`

This would reduce repeated dependency resolution overhead.

#### Tooling improvements

- Provide a reusable helper for GitHub `Link`-header counting
- Provide a reusable helper for Wilson confidence intervals and placebo date sweeps
- Provide a reusable batch manifest format for API collection jobs

#### Skill improvements

The data-analysis skill would benefit from a default “verification ladder”:

1. baseline estimate
2. alternative measurement validation
3. bias audit
4. robustness trims / winsorization
5. placebo test
6. confidence statement

That would make it easier to move from “interesting output” to “defensible conclusion.”

### Final assessment

Despite several course corrections, the process ended in a much stronger place than where it started.

The main success was methodological: the analysis moved from a fragile first-pass result to a bias-checked conclusion that separates:

- what is stable
- what is sensitive
- what is still uncertain

That is the right outcome for this kind of research task.

### Suggested next steps

If this project continues, the highest-value next work is:

1. collect more **earlier non-overlapping** seed cohorts to tighten the debiased interval
2. test alternative pre/post window lengths
3. add plots for:
   - batch comparison
   - placebo sweep
   - concentration curve
   - quintile regression-to-mean diagnostic
4. if possible, broaden beyond default-branch searchable commits using another data source
