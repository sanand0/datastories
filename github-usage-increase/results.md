# Did GitHub developer activity surge after November 2025?

## Short answer

No clear broad surge appears in the data.

Across the main analysis, only about **6%** of sampled developers showed a **meaningful increase** in commit activity after `2025-11-01`. That result stayed near 6% even after I changed the sampling design to reduce bias.

There is more evidence of a **decline** than an increase, but the exact size of that decline depends a lot on how users are sampled. So the strongest conclusion is:

- there is **no evidence of a broad post-Nov-2025 surge**
- there **may have been a decline**, but its magnitude is **not estimated robustly enough** to state as a clean population fact

## Research question

The goal was to test whether the release of Opus 4.5 in November 2025 coincided with a measurable increase in public GitHub commit activity.

More specifically:

1. What fraction of developers became significantly more active after a hypothesized break date?
2. Does the data itself point to a structural break, and if so, when?

## Final conclusion

After collection, redesign, debiasing, and stress testing, the most defensible findings are:

- In the large overlap-seeded sample (`n = 1,600`), **96 / 1,600 = 6.0%** of users showed a meaningful increase.
- In a smaller but less-biased earlier-seeded sensitivity sample (`n = 162`), **10 / 162 = 6.2%** showed a meaningful increase.
- Those two estimates are very close, which argues **against** a hidden broad surge.
- November 2025 does **not** emerge as a robust positive change-point.
- Raw monthly totals can look mildly positive, but that signal is dominated by a very small number of extremely active users.

So the evidence supports this statement:

> A small minority of developers became much more active, but there is no sign of a widespread post-November-2025 activation wave in public GitHub commits.

## What I did

I ran the project in several stages.

### 1. Built a data collection pipeline

I created `scripts/github_activity_analysis.py` to:

- authenticate to GitHub using `GITHUB_TOKEN`
- seed candidate developers from the GitHub REST `/search/commits` endpoint
- count commits efficiently using the repo commits endpoint with `per_page=1` and the `Link` header
- save raw and derived datasets under `data/github_activity/`
- analyze user-level before/after changes
- run monthly aggregate change-point checks

### 2. Collected a first large sample

I first sampled developers by searching commits in **May–October 2025**, then measured their commits in two equal windows:

- pre window: `2025-08-02` to `2025-10-31`
- post window: `2025-11-01` to `2026-01-30`

That yielded:

- first batch: `900` eligible users
- second distinct overlap batch: `700` eligible users
- combined overlap-seeded sample: `1,600` users

### 3. Discovered and corrected major methodological issues

Several corrections were needed before the final analysis was trustworthy:

- `.env` handling was simplified once the file was converted to standard `KEY=VALUE`
- global commit-search counting by `author:` / `author-email:` produced unreliable results and absurd totals, so counting was moved to the **repo commits** endpoint
- some repo requests returned intermittent `500` errors, so retries and safe fallback handling were added
- the original seed design overlapped the pre window, which risked **regression-to-the-mean bias**

### 4. Ran efficiency experiments

I tested whether cheaper collection would materially change the user-level results.

It did not:

- using only the **primary observed repo** per user captured a median of **100%** of both pre and post commits
- one-repo counting matched two-repo increase labels **99.8%** of the time
- one-repo counting matched two-repo decrease labels **99.8%** of the time

That made it practical to collect additional validation cohorts cheaply.

### 5. Collected debiased sensitivity cohorts

To reduce seed-window overlap bias, I collected additional users from an **earlier non-overlapping seed period**:

- seed window: `2025-03-01` to `2025-04-30`
- excluded all users already seen in the overlap-seeded batches

That produced:

- earlyseed batch: `109` eligible users
- earlyseed page-2 batch: `53` eligible users
- combined earlier-seeded sample: `162` users

This sample is smaller, but much better for checking whether the overlap-seeded decline result was artificially inflated.

### 6. Ran verification and stress tests

I then compared results across designs and ran several checks:

- **between-batch comparison**
  - overlap-seeded sample vs earlier-seeded sample
- **confidence intervals**
  - Wilson intervals for increase and decrease shares
- **regression-to-the-mean diagnostic**
  - decline rates by pre-activity quintile
- **change-point detection**
  - `ruptures` PELT on monthly series
  - one-break scan
- **heavy-tail robustness**
  - trim top 1% of users
  - inspect median monthly user counts
- **placebo break sweep**
  - test candidate break months from July to December 2025

## Data sources and API methods

### GitHub endpoints used

I used two GitHub REST API surfaces:

1. `/search/commits`
   - to seed candidate users from public commits
   - constrained to date windows
   - limited by GitHub to 1,000 search results per query and 30 search requests per minute

2. `/repos/{owner}/{repo}/commits`
   - to count commits by author in a repo during a time window
   - used with:
     - `author=<login>`
     - `since=...`
     - `until=...`
     - `per_page=1`
   - commit counts were inferred from the `Link` header

### Why this design was chosen

The search endpoint is useful for finding candidate users, but not ideal for trustworthy global counting. The repo commits endpoint was much more reliable for actual counts.

This combination kept the study within rate limits while still making it possible to sample many users.

## Sampling design

### Overlap-seeded design

This was the high-power main sample:

- seed users from commit search in `May-Oct 2025`
- require at least one pre-window commit
- measure pre/post counts

This design is good for asking:

> Among developers who were active before the hypothesized break, how many later became much more active?

But it has a bias:

- the seed period overlaps the pre window
- that selects users who were active very close to the break
- later declines can then be exaggerated by regression to the mean

### Earlier non-overlapping design

This was the debiased sensitivity sample:

- seed users from `Mar-Apr 2025`
- exclude any user already seen in overlap-seeded batches
- keep the same Aug-Oct pre window and Nov-Jan post window

This is less likely to mechanically overstate declines caused by recent-activity selection.

## How “meaningful” change was defined

At the end of the analysis I used symmetric user-level rules:

- **meaningful increase**
  - post minus pre >= `10`
  - post / pre >= `2.0`

- **strong increase**
  - post minus pre >= `15`
  - post / pre >= `2.5`

- **meaningful decrease**
  - post minus pre <= `-10`
  - post / pre <= `0.5`

- **strong decrease**
  - post minus pre <= `-15`
  - post / pre <= `0.4`

These are simple, transparent thresholds rather than model-based latent categories.

## Main findings

### User-level increase estimates

#### Overlap-seeded sample (`n = 1,600`)

- meaningful increase share: **6.0%**
- 95% CI: **4.9% to 7.3%**

#### Earlier-seeded sample (`n = 162`)

- meaningful increase share: **6.2%**
- 95% CI: **3.4% to 11.0%**

### What that implies

The increase estimate is remarkably stable across a large sample and a less-biased sensitivity sample.

That makes the central finding fairly strong:

> If there had been a broad surge after November 2025, it should have shown up as a much larger increase share than ~6%.

It did not.

### User-level decrease estimates

#### Overlap-seeded sample (`n = 1,600`)

- meaningful decrease share: **48.4%**
- 95% CI: **46.0% to 50.9%**

#### Earlier-seeded sample (`n = 162`)

- meaningful decrease share: **32.1%**
- 95% CI: **25.4% to 39.6%**

### What that implies

The decline estimate moves a lot when the sampling design changes.

That means:

- the direction may be real
- the exact magnitude is **not robust enough** to quote as a precise headline number

## Change-point results

### Overlap-seeded monthly panel

For the combined overlap-seeded monthly panel:

- raw aggregate best one-break month: **2025-06**
- raw post-Nov change: **+4.7%**
- excluding top 1% of users: **-18.0%**
- median monthly user count:
  - best break around **2025-08**
  - post-Nov median effectively collapses

### Earlier-seeded monthly panel

For the earlier non-overlapping monthly panel:

- raw aggregate best one-break month: **2025-11**
- raw post-Nov change: **-49.9%**
- excluding top 1% of users: **-36.9%**

### Interpretation

The monthly change-point story is not “November surge.”

If anything:

- overlap-seeded raw totals are distorted upward by a few heavy users
- the less-biased panel points toward weakness, not surge

## Heavy-tail and concentration effects

Raw aggregate counts are highly concentrated.

In the combined overlap-seeded monthly panel:

- the top 10 users generated **83.8%** of all monthly commits

That means a few extremely active users can make aggregate totals look positive even when the typical user is flat or down.

This is why the user-level share analysis is much more informative than raw totals alone.

## Placebo test

I ran a simple placebo-style sweep across candidate break months on the overlap monthly panel.

Increase shares by candidate break month:

- `2025-07`: **13.9%**
- `2025-08`: **12.8%**
- `2025-09`: **9.4%**
- `2025-10`: **7.2%**
- `2025-11`: **2.2%**
- `2025-12`: **1.7%**

If November 2025 had been the natural surge month, it should have looked unusually strong. It did not. It was one of the weakest candidate months.

## Is the sample size large enough?

### For ruling out a broad surge

Yes.

The overlap-seeded sample is large enough (`n = 1,600`) that the meaningful-increase estimate is fairly tight. A genuine broad post-Nov activation wave would not plausibly hide inside a confidence interval centered near 6%.

### For precisely measuring any decline

Not yet.

The earlier-seeded sensitivity sample is useful for debiasing, but still small (`n = 162`). It is enough to show that the huge overlap-seeded decline estimate is unstable, but not enough to nail down the true decline share precisely.

### Practical implication

The next most valuable data to collect would be:

- more **earlier non-overlapping seed cohorts**
- not more overlap-seeded users

## What can be concluded with confidence

These are the strongest defensible conclusions from the final analysis:

1. There was **no broad surge** in public GitHub commit activity after November 2025.
2. Only a **small minority** of sampled developers showed large post-Nov increases.
3. November 2025 does **not** stand out as a robust positive structural break.
4. Raw aggregate growth is too dominated by heavy users to support a surge claim on its own.
5. There may have been a decline in activity, but the exact share of declining users is **sensitive to sampling design** and therefore should be stated cautiously.

## What cannot be concluded

This analysis does **not** show that:

- Opus 4.5 caused any behavior change
- “about half of developers became less active” as a reliable population fact
- all GitHub developers behaved this way

Important scope limits:

- public commits only
- searchable commits only
- commit search only covers the **default branch**
- repo-based counting only covers each user’s observed active repos from the seed phase

## How to replicate

### Inputs

- a GitHub token in `.env` as:

```bash
GITHUB_TOKEN=...
```

### Main commands used

```bash
set -a && source .env
uv run scripts/github_activity_analysis.py collect \
  --batch-label main \
  --sample-target 900 \
  --aggregate-subset-size 100 \
  --max-repos-per-user 2 \
  --monthly-repos-per-user 1
```

```bash
set -a && source .env
uv run scripts/github_activity_analysis.py collect \
  --batch-label page2 \
  --exclude-batch-label main \
  --seed-page-start 2 \
  --sample-target 700 \
  --aggregate-subset-size 80 \
  --max-repos-per-user 1 \
  --monthly-repos-per-user 1
```

```bash
set -a && source .env
uv run scripts/github_activity_analysis.py collect \
  --batch-label earlyseed \
  --exclude-batch-label main,page2 \
  --seed-start-date 2025-03-01 \
  --seed-end-date 2025-04-30 \
  --sample-target 500 \
  --aggregate-subset-size 60 \
  --max-repos-per-user 1 \
  --monthly-repos-per-user 1
```

```bash
set -a && source .env
uv run scripts/github_activity_analysis.py collect \
  --batch-label earlyseed_p2 \
  --exclude-batch-label main,page2,earlyseed \
  --seed-start-date 2025-03-01 \
  --seed-end-date 2025-04-30 \
  --seed-page-start 2 \
  --sample-target 150 \
  --aggregate-subset-size 40 \
  --max-repos-per-user 1 \
  --monthly-repos-per-user 1
```

```bash
set -a && source .env
uv run scripts/github_activity_analysis.py analyze --batch-labels main,page2
```

Verification tables were then built from the batch outputs and saved under `data/github_activity/analysis/`.

### Files to inspect

- main-batch raw data: `data/github_activity/raw/`
- second overlap batch: `data/github_activity/batches/page2/raw/`
- earlier-seeded sensitivity batches:
  - `data/github_activity/batches/earlyseed/raw/`
  - `data/github_activity/batches/earlyseed_p2/raw/`
- analysis tables: `data/github_activity/analysis/`
- key verification outputs:
  - `verification_batch_summary.csv`
  - `regression_to_mean_quintiles.csv`
  - `verification_break_summaries.csv`
  - `placebo_break_sweep.csv`
  - `efficiency_experiments.csv`

## Bottom line for a reporter or researcher

If the question is “did public GitHub commit activity broadly jump after November 2025?”, the answer from this analysis is **no**.

There were some big individual increases, but not enough to call it a broad surge. Any claim of a large widespread decline should be treated more cautiously, because that result depends more strongly on how recently-active users are sampled.
