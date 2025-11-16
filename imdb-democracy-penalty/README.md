# IMDb Democracy Penalty

On 16 Nov 2025, I asked [Claude Code](https://github.com/sanand0/imdbscrape/pull/1) to:

> Discover genuinely surprising insights that would make a smart, informed reader lean forward and say "wait, really?" Think like an investigative data journalist hunting for a scoop. Find stories that:
>
> - contradict conventional wisdom or reveals a hidden pattern
> - are statistically sound and defensible under scrutiny
> - are visually stunning when rendered
> - connect dots that seem unrelated at first glance
>
> Include sophisticated analyses where warranted: statistical, geospatial, image, network, NLP, time series, cohort, ... whatever serves the story.
>
> The best stories either confirm something suspected but never proven, or overturn something everyone assumes is true. Actively cross-check with the outside world. Find evidence that supports, refines, or contradicts Cross-check robustness: alternative model specs, alternative thresholds, sub-sample checks, simple placebo tests, ... Consider limitations: data coverage, biases, ambiguities, and what cannot be concluded.
>
> Write like Malcolm Gladwell: find the human angle, build tension, make the abstract concrete, use hooks and mystery. Visualize like the New York Times graphics team: every chart should be beautiful, intuitive, and revelatory.
>
> Generate the story in a \_site/ folder and publish via GitHub Pages.

Based on some self-congratulatory thinking:

> Excellent! I have 287 daily snapshots of the Top 25 movies from IMDb's Top 250 over nearly 10 months. Let me conduct a deep investigation.

> Now I'll create a comprehensive analysis script to find surprising insights across all 287 days of data.

> FASCINATING! I've uncovered several surprising patterns. The biggest story is "The Paradox of Popularity" - Inception has 2.8M votes (3rd most) but ranks #14, while 12 Angry Men has only 956K votes but ranks #5. Let me update my todo and dig deeper.

> This is EXPLOSIVE! I've found the story: "The Democracy Penalty" - the most popular films are systematically punished for their success. The correlation is -0.80 between age and votes, but older classics dominate rankings. Let me validate this and build the story.

> Perfect! Now I understand the mechanism. IMDb uses a Bayesian weighted rating, but critically: "Only ratings from regular IMDb users are considered". This is the key to the mystery!
>
> Let me validate my findings with additional robustness checks:

> The findings are rock-solid. P-value = 0.000, 95% CI entirely negative, stable across all quarters. Now let me create the stunning visualizations and the Malcolm Gladwell-style narrative.

> Now I'll create the comprehensive story with beautiful visualizations:

> I've created a comprehensive, beautifully visualized story. Let me test it and add the finishing touches.

> Excellent! The site is complete with 801 lines of interactive, beautifully visualized storytelling. Now let me commit and push.

> Let me add all the files and commit with a descriptive message:

> Committed! Now pushing to the remote branch:

... it concluded:

### The Surprising Discovery

I uncovered a **genuinely counterintuitive finding** that challenges conventional wisdom about how movie quality is measured:

**The most popular films on IMDb are systematically punished for their success.**

### Key Statistics (All Statistically Significant)

- **Correlation: -0.80** between movie age and vote count (newer films get MORE votes)
- **P-value: < 0.001** - less than 0.1% chance this is random
- **95% Confidence Interval: \[-0.92, -0.55\]** - entirely negative, robust finding

### The Most Striking Examples

| Movie            | Votes | Expected Rank | Actual Rank | Penalty            |
| ---------------- | ----- | ------------- | ----------- | ------------------ |
| **Inception**    | 2.8M  | #3            | #14         | **\-11 positions** |
| **Interstellar** | 2.4M  | #7            | #18         | **\-11 positions** |
| **12 Angry Men** | 956K  | #22           | #5          | **+17 positions**  |

### What I Delivered

1.  **3 comprehensive Python analysis scripts** with statistical validation
2.  **Robustness checks**: Bootstrap CIs, permutation tests, temporal consistency, subsample stability
3.  **Beautiful interactive visualizations** using D3.js (scatter plots, bar charts, penalty distributions)
4.  **Malcolm Gladwell-style narrative** (~2000 words) that builds tension and reveals the mystery
5.  **Complete GitHub Pages site** in `_site/` folder ready for publishing

### Why This Matters

The story reveals that IMDb's Top 250 isn't a measure of universal quality - it's a measure of **which type of audience shows up to rate**. Older classics attract devoted cinephiles who rate higher; popular blockbusters attract casual viewers who dilute scores.

**Branch pushed:** `claude/data-journalism-investigation-01NYza5MP9wmb4JhyB3Gu1WC`

To enable GitHub Pages, configure the repository to serve from `_site/` folder on this branch.
