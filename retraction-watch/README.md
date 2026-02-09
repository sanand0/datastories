# Researcher of the Future

Generated from the [retraction-watch](https://gitlab.com/crossref/retraction-watch-data/-/blob/main/retraction_watch.csv) dataset
by Codex using GPT 5.3 Codex with the prompt:

```markdown
Analyze retraction-watch/retraction_watch.csv like an investigative journalist hunting for stories that make smart readers lean forward and say "wait, really?"

- Understand the Data: Identify dimensions & measures, types, granularity, ranges, completeness, distribution, trends. Map extractable features, derived metrics, and what sophisticated analyses might serve the story (statistical, geospatial, network, NLP, time series, cohort analysis, etc.).
  - Search online for context.
- Define What Matters: List audiences and their key questions. What problems matter? What's actually actionable? What would contradict conventional wisdom or reveal hidden patterns?
- Hunt for Signal: Analyze extreme/unexpected distributions, breaks in patterns, surprising correlations. Look for stories that either confirm something suspected but never proven, or overturn something everyone assumes is true. Connect dots that seem unrelated at first glance.
- Highlight Heroes & Villains: Identify standout entities (people, places, products, segments) that defy norms. Who's overperforming or underperforming? Who's driving trends or bucking them?
- Segment & Discover: Cluster/classify/segment to find unusual, extreme, high-variance groups. Where are the hidden populations? What patterns emerge when you slice the data differently?
- Find Leverage Points: Hypothesize small changes yielding big effects. Look for underutilization, phase transitions, tipping points. What actions would move the needle?
- Verify & Stress-Test:
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

Package these this into a beautiful slide deck, McKinsey style.
Make the slides content rich, i.e. clear and self-explanatory with enough detail to help the audience understand without a narrator.
Pagest should include rich, highly interactive data visualization prominently where appropriate (and preferably, often.)
Use iconography, typography, stock images, etc. as appropriate.
Write as a single page HTML application in the style of the rest of the data stories.
```
