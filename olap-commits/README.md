# OLAP git commits

## Prompt 1

Analyze data.db. It has git commits data for OLAP databases.

Analyze data like an investigative journalist hunting for stories that make smart readers lean forward and say "wait, really?"

1. Understand the Data: Identify dimensions & measures, types, granularity, ranges, completeness, distribution, trends. Map extractable features, derived metrics, and what sophisticated analyses might serve the story (statistical, geospatial, network, NLP, time series, cohort analysis, etc.).
2. Define What Matters: List audiences and their key questions. What problems matter? What's actually actionable? What would contradict conventional wisdom or reveal hidden patterns?
3. Hunt for Signal: Analyze extreme/unexpected distributions, breaks in patterns, surprising correlations. Look for stories that either confirm something suspected but never proven, or overturn something everyone assumes is true. Connect dots that seem unrelated at first glance.
4. Segment & Discover: Cluster/classify/segment to find unusual, extreme, high-variance groups. Where are the hidden populations? What patterns emerge when you slice the data differently?
5. Find Leverage Points: Hypothesize small changes yielding big effects. Look for underutilization, phase transitions, tipping points. What actions would move the needle?
6. Verify & Stress-Test:
   - **Cross-check externally**: Find evidence from the outside world that supports, refines, or contradicts your findings
   - **Test robustness**: Alternative model specs, thresholds, sub-samples, placebo tests
   - **Check for errors/bias**: Examine provenance, definitions, methodology; control for confounders, base rates, uncertainty (The Data Detective lens)
   - **Check for fallacies**: Correlation vs. causation, selection/survivorship Bias (what is missing?), incentives & Goodhart’s Law (is the metric gamed?), Simpson's paradox (segmentation flips trend), Occam’s Razor (simpler is more likely), inversion (try to disprove) regression to mean (extreme values naturally revert), second-order effects (beyond immediate impact), ...
   - **Consider limitations**: Data coverage, biases, ambiguities, and what cannot be concluded
7. Prioritize & Package: Select insights that are:
   - **High-impact** (not incremental) - meaningful effect sizes vs. base rates
   - **Actionable** (not impractical) - specific, implementable
   - **Surprising** (not obvious) - challenges assumptions, reveals hidden patterns
   - **Defensible** (statistically sound) - robust under scrutiny

**Narrative-driven data story**. Write like Malcolm Gladwell. Visualize like the NYT graphics team. Think like a detective who must defend findings under scrutiny.

- **Compelling hook**: Start with a human angle, tension, or mystery that draws readers in
- **Story arc**: Build the narrative through discovery, revealing insights progressively
- **Integrated visualizations**: Beautiful, interactive charts/maps that are revelatory and advance the story (not decorative)
- **Concrete examples**: Make abstract patterns tangible through specific cases
- **Evidence woven in**: Data points, statistics, and supporting details flow naturally within the prose
- **"Wait, really?" moments**: Position surprising findings for maximum impact
- **So what?**: Clear implications and actions embedded in the narrative
- **Honest caveats**: Acknowledge limitations without undermining the story

## Prompt 2

Create a BEAUTIFUL New York Times style scrolltelling web page from this.

Prefer creative, distinctive frontends that surprise and delight, not generic, "on distribution" outputs.

Focus on:

- Typography: beautiful, unique, and interesting fonts, not generic fonts like Arial and Inter. Opt for distinctive choices that elevate the frontend's aesthetics.
- Color & Theme: Commit to a cohesive aesthetic. Use CSS variables for consistency. Dominant colors with sharp accents outperform timid, evenly-distributed palettes. Draw from IDE themes and cultural aesthetics for inspiration.
- Motion: Use animations for effects and micro-interactions. Prioritize CSS-only solutions for HTML. Focus on high-impact moments: one well-orchestrated page load with staggered reveals (animation-delay) creates more delight than scattered micro-interactions.
- Backgrounds: Create atmosphere and depth rather than defaulting to solid colors. Layer CSS gradients, use geometric patterns, or add contextual effects that match the overall aesthetic.

Override framework / browser defaults to avoid generic AI-generated aesthetics:

- Overused font families (Inter, Roboto, Arial, system fonts)
- Clichéd color schemes (particularly purple gradients on white backgrounds)
- Predictable layouts and component patterns
- Cookie-cutter design that lacks context-specific character

Interpret creatively and make unexpected choices that feel genuinely designed for the context. Vary between light and dark themes, different fonts, different aesthetics. You still tend to converge on common choices (Space Grotesk, for example) across generations. Avoid this: it is critical that you think outside the box!

## Prompt 3

The top half of the phrase "Wait, really?" gets cut off. The body font is too small to read -- make it readable for older readers (but the number of words per line is fine, so feel free to increase the container width).

## Results

- [Markdown Story](story.md)
- [Data Visualization](index.html)
- [Copilot logs](copilot-log.md)
