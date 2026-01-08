# Prompts

## Research (Codex - GPT 5.2 Codex xhigh)

How can I find Python packages that are heavily used by other Python packages but far less used by developers in their applications?

How can I do the same for npm packages?

If there's no obvious practical and effective approach, evaluate diverse options and recommend the most pragmatic approach that comes closest to my objective.

Replies:

- [ChatGPT 🔒](https://chatgpt.com/c/695f7a6b-9c68-8324-9b6c-e882d256af1c)
- [Gemini 🔒](https://gemini.google.com/u/2/app/ae505def8e134e6d)
- [Claude 🔒](https://claude.ai/chat/bfec0835-83b8-4719-b9f9-4a757be73345)

## Scrape

Write a compact Python script `fetch_libraries.py` to call the Libraries.io API to get the most depended-upon PyPI packages.

GET https://libraries.io/api/search?platforms=PyPI&sort=dependents_count&order=desc&page=1&per_page=100&api_key=$API_KEY

This fetches page 1 of the most depended-upon PyPI packages, 100 packages per page. Rate limit: 60 requests per minute.

Fetch the first 100 pages, cached, so that if I re-run, I don't hammer the API again. Use the `LIBRARIES_IO_API_KEY` from `.env`.

The result is an array with keys: {name, dependent_repos_count, dependents_count, forks, stars, rank, contributions_count, ...}. Extract the mentioned fields into a CSV file `pypi-repos.csv`.

Repeat the same for platforms=npm into `npm-repos.csv`.

Run, test, and ensure it works.

Commit as you go.

## Interview

My aim is to identify Python and npm packages that are heavily used by other packages (high dependents_count) but are relatively less used directly by developers in their applications (low dependent_repos_count).

But there's no reason to stop there! We can take this much deeper (though roughly in that direction).

Keep in mind that:

- Derived metrics add value: what sophisticated analyses are enabled if we extract new fields (statistical, geospatial, network, NLP, time series, cohort analysis, etc.)
- Interesting analysis comes when we: Analyze extreme/unexpected distributions, breaks in patterns, surprising correlations. Stories that either confirm something suspected but never proven, or overturn something everyone assumes is true. Connect dots that seem unrelated at first glance.
- Segments offer Discovery: Cluster/classify/segment to find unusual, extreme, high-variance groups. Where are the hidden populations? What patterns emerge when you slice the data differently?
- Leverage points are interesting: Hypothesize small changes yielding big effects. Look for underutilization, phase transitions, tipping points. What actions would move the needle?

Now, interview me like an expert business analyst or investigative journalist to understand what analyses might be interesting.

- What would an expert in this field check that beginners would miss?
- In this context, what questions would an expert ask that a beginner would not know to?
- What patterns would an expert in this field recognize that beginners would miss?

Based on your interview, save the list of analyses to perform in analyses.md.

### Interview response

- Goals & Decisions
  - Audience: developers, i.e. users of packages.
  - Purpose: Engagement and entertainment, Not actionability
- Definitions & Thresholds
  - "heavily used by packages" and "low direct usage" are probably better defined via log scales, I think? If that doesn't work well, percentiles could be an alternative.
  - Extremes are usually more interesting, especially outlieres
  - Treat scoped npm packages or PyPI namespace conventions same as unscoped
- Scope & Time
  - Trends over time will be nice
  - Yearly periods are probably best
  - This is a one-time analysis - I won't be refreshing data - but we can look back historically
- Enrichment & External Signals
  - You can pull in any data available from .cache/ - nothing else
- Risk & Health
  - I'm not focused on supply-chain risk or adoption strategy unless beyond anything naturally interesting to the average developer
  - Same for maintainer identity
  - Yes, "critical but fragile" packages sound interesting!
- Segmentation
  - Domain (web, ML, infra), license seem interesting. Nothing wrong with others either
  - Compare PyPI vs npm
  - No specific cohorts to highlight - your call
- Storytelling
  - My hunch: There are some hidden packages that form the infrastructure for most other packages that end-users rarely use.
  - All of these narratives sound interesting: risk, opportunity, ecosystem dynamics, but especially hidden champions.
- Outputs
  - For now, just deliver a list of analyses to perform.

### Explain why it's cool

Update analyses.md to explain in simple ELI15 language what the analysis might reveal and why that's cool!

## Analyze

Run ALL the analyses in analyses.md. Save the results in files. Update analyses.md with the steps and the findings.

## Test

- Verify & Stress-Test
  - **Cross-check externally**: Find evidence from the outside world that supports, refines, or contradicts your findings
  - **Test robustness**: Alternative model specs, thresholds, sub-samples, placebo tests
  - **Check for errors/bias**: Examine provenance, definitions, methodology; control for confounders, base rates, uncertainty (The Data Detective lens)
  - **Check for fallacies**: Correlation vs. causation, selection/survivorship Bias (what is missing?), incentives & Goodhart’s Law (is the metric gamed?), Simpson's paradox (segmentation flips trend), Occam’s Razor (simpler is more likely), inversion (try to disprove) regression to mean (extreme values naturally revert), second-order effects (beyond immediate impact), ...
  - **Consider limitations**: Data coverage, biases, ambiguities, and what cannot be concluded
- Prioritize & Package: Select insights that are:
  - **High-impact** (not incremental) - meaningful effect sizes vs. base rates
  - **Actionable** (not impractical) - specific, implementable
  - **Surprising** (not obvious) - challenges assumptions, reveals hidden patterns
  - **Defensible** (statistically sound) - robust under scrutiny

Revise / update analyses.md based on these tests and the final selected insights.

Then update analyses.md with enough information for another agent to understand what you did and create a story out of it. (Include any interesting tidbits.)

## Story (Claude Code)

Read the files in this directory, which has analyses you need to narrate and visualize.

- prompts.md has the prompts used to create the analyses
- analyses.md has the analyses performed and their results - with details of the other files.

Based on this, write a compelling visual data story that would engage and entertain developers.

Write as a **Narrative-driven Data Story**. Write like Malcolm Gladwell. Visualize like the NYT graphics team. Think like a detective who must defend findings under scrutiny.

- **Compelling hook**: Start with a human angle, tension, or mystery that draws readers in
- **Story arc**: Build the narrative through discovery, revealing insights progressively
- **Integrated visualizations**: Beautiful, interactive charts/maps that are revelatory and advance the story (not decorative)
- **Concrete examples**: Make abstract patterns tangible through specific cases
- **Evidence woven in**: Data points, statistics, and supporting details flow naturally within the prose
- **"Wait, really?" moments**: Position surprising findings for maximum impact
- **So what?**: Clear implications and actions embedded in the narrative
- **Honest caveats**: Acknowledge limitations without undermining the story

For the design aesthetic (typography, color & theme, backgrounds, etc.), follow Vox. Motion: Use animations for effects and micro-interactions. Prioritize CSS-only solutions for HTML. Focus on high-impact moments: one well-orchestrated page load with staggered reveals (animation-delay) creates more delight than scattered micro-interactions.

Commit as you go.

## Revise insights (Codex - GPT 5.2 Codex xhigh)

Stories are interesting when they have heroes. Increase the focus on individual packages. Update analyses.md with insights based on specific packages: outliers, in particular, are interesting.

## Story v2 (Claude Code)

Read the files in this directory, which has analyses you need to narrate and visualize.

- prompts.md has the prompts used to create the analyses
- analyses.md has the analyses performed and their results - with details of the other files.

Based on this, write a compelling visual data story that would engage and entertain developers.

Write as a **Narrative-driven Data Story**. Write like Malcolm Gladwell. Visualize like the NYT Upshot team. Think like a detective who must defend findings under scrutiny.

- **Compelling hook**: Start with a human angle, tension, or mystery that draws readers in
- **Story arc**: Build the narrative through discovery, revealing insights progressively
- **Integrated visualizations**: Beautiful, interactive charts/maps that are revelatory and advance the story (not decorative)
- **Concrete examples**: Make abstract patterns tangible through specific cases
- **Evidence woven in**: Data points, statistics, and supporting details flow naturally within the prose
- **"Wait, really?" moments**: Position surprising findings for maximum impact
- **So what?**: Clear implications and actions embedded in the narrative
- **Honest caveats**: Acknowledge limitations without undermining the story

Stories are interesting when they have heroes. Highlight individual packages. Outliers, in particular, are interesting. Scatterplots highlighting individual packages are a good way of highlighting these outliers.

For the design aesthetic (typography, color & theme, backgrounds, etc.), follow The Upshot. Motion: Use animations for effects and micro-interactions. Prioritize CSS-only solutions for HTML. Focus on high-impact moments: one well-orchestrated page load with staggered reveals (animation-delay) creates more delight than scattered micro-interactions.

Commit as you go.

## Documentation (Claude Code)

Create a README.md clearly explaining to a layman what this repo is about, how it was generated (point to prompts.md), what data sourcing & analyses were performed (mention key analyses, point to analyses.md) and how (point to all relevant code), and how the visualization was generated. Note that this will be hosted under package-usage/ of https://github.com/sanand0/datastories/ and deployed at https://sanand0.github.io/datastories/package-usage/ - and don't hesitate to sprinkle in wit and humor!

## Clean-up (Claude Code)

Link to specific files in README.md - wherever possible.

Delete all files not required by index.html and not pointed to by README.md. I'm trying to get the repo size as small as possible. Commit as you go. Test and ensure nothing essential is missed out.

## Fix clean-up issues (Claude Code)

Bring back any Python scripts you deleted and explain mention them (with explanation + links) in README.md. They barely take up space.
