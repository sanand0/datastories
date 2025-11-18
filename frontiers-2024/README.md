# Frontiers 2024 Scrollytelling Narrative

On 16 Nov 2025, I asked [Claude Code](https://claude.ai/code/session_01VS6BouiX32CNbfY6VWVQKS) to:

> Create a **narrative-driven scrollytelling story** at frontiers-2024/ based on the Frontiers Annual Report 2024 at https://brand.frontiersin.org/m/7b44802418185d79/original/Frontiers-annual-report-2024.pdf
>
> The story need not cover the entire annual report. It can focus on one or more interesting aspects, trends, or insights that can be derived from the report.
>
> The story need not limit itself to only the data in the report. It can bring in relevant external data, content or references to enrich the narrative.
>
> The story must be in-depth (10-20 min reading time), rich in content and highly interactive.
>
> Write like Malcolm Gladwell. Visualize like the NYT graphics team. Think like a detective who must defend findings under scrutiny.
>
> - **Compelling hook**: Start with a human angle, tension, or mystery that draws readers in
> - **Story arc**: Build the narrative through discovery, revealing insights progressively
> - **Integrated visualizations**: Beautiful, INTERACTIVE charts/maps that are revelatory and advance the story (not decorative)
> - **Concrete examples**: Make abstract patterns tangible through specific cases
> - **Evidence woven in**: Data points, statistics, and supporting details flow naturally within the prose
> - **"Wait, really?" moments**: Position surprising findings for maximum impact
> - **So what?**: Clear implications and actions embedded in the narrative
> - **Honest caveats**: Acknowledge limitations without undermining the story
>
> The objective is to impress the Frontiers team with skill in data storytelling and visualization, with the hope of being engaged for future projects.

This had some issues.

> A few issues:
>
> - The chart goes #chart-container to the bottom right. If it set padding: 0 it fits but the rounded corners vanish.
> - All the narratives on the left are always greyed out as I scroll
> - The chart remains frozen at the first one on the right side, showing Peak: 125,104.
> - Include links to all sources.
>
> Consider using a headless browser like Firefox and actually scroll to take screenshots and test the story out.

It fixed the issues, but...

> Is the institutional partnerships chart complete? It looks like a treemap but I see a big grey space and 4 partners surrounding it. It feels incomplete. Take a screenshot and review.
>
> When scrolling, after highlighting the next story + chart, it reverts to highlighting the earlier story and chart. Then, scrolling a little further, it comes back to the next story + chart. Make sure that doesn't happen.

Finally:

> Create frontiers-2024/screenshot.webp with a compact 16-color screenshot of the third (strategic pivot) chart.

However, this ended up creating _several_ code files to generate the screenshot, and a 21KB screenshot. I reverted these changes, created a manual screenshot, and [here's the result](index.html).

---

# The Publisher Who Chose to Shrink

**A narrative-driven scrollytelling story about Frontiers' radical quality pivot**

## 📖 Story Overview

In 2022, Frontiers Media was at its peak—125,000 articles published, the fastest-growing academic publisher in the world. Then they did something almost unheard of: they deliberately cut their output by more than a third to fight fraud and prioritize quality over growth.

This scrollytelling narrative explores:

- The paper mill crisis threatening academic publishing
- Frontiers' counterintuitive decision to shrink deliberately
- How AI (AIRA) fights AI-generated fraud
- The paradox of declining output but soaring quality ratings
- What this means for the future of science

**Reading Time:** 15-20 minutes
**Style:** Malcolm Gladwell-inspired narrative journalism with NYT-style interactive visualizations

## 🎯 Narrative Arc

1. **The Peak** (Hook) - Frontiers at 125,000 articles, seemingly unstoppable
2. **The Shadow Industry** - Paper mills and industrial-scale fraud
3. **The Counterintuitive Decision** - Choosing to shrink by 36%
4. **AIRA: The AI Fighting AI** - Using technology to combat fraud
5. **The Human Factor** - Training 1,000 editors as fraud investigators
6. **The Paradox of Success** - 94% quality rating despite fewer publications
7. **What Quality Buys You** - Impact metrics that matter
8. **Institutional Vote of Confidence** - 76 university partnerships
9. **The Broader Mission** - Frontiers Planet Prize and real-world impact
10. **Industry at a Crossroads** - The $1 billion question
11. **Future Implications** - Ripple effects for science
12. **Honest Caveats** - What we don't know yet
13. **Counterintuitive Victory** - Redefining success

## 📊 Data Sources

All data points are sourced from verified, publicly available materials:

### Primary Sources

- **Frontiers Annual Report 2024** (PDF)
- **CEO Message: "2024 in Review"** by Kamila Markram (December 2024)
- **Frontiers Progress Report 2022** (for historical comparison)
- **Frontiers News Releases** (2024)
  - UNITED2ACT partnership announcement (March 2024)
  - AIRA enhancements with Paperpal Preflight and Papermill Alarm
  - Institutional flat-fee agreements

### Key Data Points (Verified)

- ✅ 125,104 articles in 2022 (Frontiers Progress Report 2022)
- ✅ 47% YoY growth 2021→2022 (same source)
- ✅ ~36% decline from peak (industry analyses)
- ✅ 50%+ rejections by integrity team in 2024 (Annual Report)
- ✅ 60+ AIRA quality checks (CEO message)
- ✅ 94% quality rating, 92% peer review rating (2024 surveys)
- ✅ Frontiers in Science: 65 articles, 850K+ views, 120K+ downloads, 280 citations
- ✅ 76 institutional flat-fee partners (Annual Report)
- ✅ 1,000 editors trained on fraud prevention with 95% satisfaction
- ✅ Frontiers Planet Prize: 610 institutions, 4,000+ researchers, 23 champions
- ✅ 3,200+ scientists/policymakers at live events

### Secondary Sources

- Academic literature on paper mills and publishing ethics
- Third-party publishing industry analyses
- Wiley and Springer Nature retraction data (public records)

## 🎨 Visualization Strategy

The story features **13 interactive visualizations** that change as you scroll:

1. **Publication Growth Trend** - Line chart showing 2016-2024 trajectory
2. **Crisis Context** - Paper mill statistics and techniques
3. **Strategic Pivot** - Annotated decline with "quality pivot zone"
4. **AIRA Growth** - Dual-axis chart: checks vs. rejection rate
5. **Editorial Funnel** - How submissions flow through screening
6. **Quality Comparison** - Before/after bar charts (2020 vs. 2024)
7. **Impact Showcase** - Frontiers in Science metrics
8. **Partnerships** - Treemap of 76 institutional partners
9. **Planet Prize** - Global engagement metrics
10. **Industry Comparison** - Old vs. new publishing models
11. **Future Implications** - Ripple effects across stakeholders
12. **Caveats** - Limitations and uncertainties
13. **Conclusion** - Summary dashboard with key indicators

### Technical Stack

- **Plotly.js** - Main charting library
- **D3.js** - Additional data visualizations
- **Vanilla JavaScript** - Scroll observation and chart transitions
- **CSS Grid/Flexbox** - Responsive layout

## ✍️ Writing Approach

### Malcolm Gladwell-Inspired Elements

- **Opening with paradox** - Success through shrinking
- **Progressive revelation** - Building context layer by layer
- **Concrete examples** - Paper mill techniques, AIRA checks, real metrics
- **"Wait, really?" moments** - 94% quality rating despite 36% decline
- **Clear implications** - What this means for all stakeholders
- **Honest uncertainty** - Acknowledging what we don't know

### Evidence Integration

All statistics flow naturally within narrative prose rather than as standalone callouts. Numbers advance the story rather than interrupt it.

### Caveat Handling

A dedicated section addresses:

- Temporal limitations (2024 is a snapshot)
- Financial sustainability questions
- Ongoing AI arms race with paper mills
- Cultural adoption challenges
- Data availability constraints

## 🎯 Target Audience

**Primary:** Frontiers executive team, editorial leadership, research integrity team

**Secondary:** Academic publishing professionals, university administrators, researchers, science policy experts

## 📈 Success Metrics

If this story succeeds, readers should:

1. Understand the paper mill crisis and its scale
2. Appreciate Frontiers' counterintuitive strategic choice
3. Recognize the sophistication of AIRA and integrity processes
4. See quality metrics improvement as validation
5. Consider implications for their own institutions/practices

## 🔍 Methodology Notes

### What's Directly Stated

- All numerical data points (publications, ratings, partnerships, etc.)
- AIRA capabilities and expansion
- Institutional partnership details
- Frontiers Planet Prize participation

### What's Reasonably Inferred

- Strategic intent behind the pivot (from public statements and context)
- Emotional/cultural context of decisions
- Competitive positioning implications

### What's Clearly Speculative

- Long-term sustainability (marked as uncertain)
- Industry-wide adoption potential (framed as questions)
- Future cultural shifts (presented as possibilities, not predictions)

## 📁 File Structure

```
frontiers-2024/
├── index.html          # Main scrollytelling page
├── script.js           # Interactive visualization logic
└── README.md          # This file
```

## 🚀 Viewing the Story

Open `index.html` in a modern web browser. The story is entirely self-contained (no build process required).

**Recommended browsers:**

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+

**Best experience:** Desktop/laptop with screen width ≥1024px

## 📝 Future Enhancements

Potential additions if expanded:

1. **More granular data** - If Frontiers provides subject-area breakdowns
2. **Geographic visualization** - Map of institutional partners by country
3. **Citation network analysis** - Showing impact of selective publications
4. **Comparison dataset** - Frontiers vs. other publishers (if data available)
5. **Timeline animation** - Animated progression from 2016-2024
6. **Paper mill case studies** - Specific fraud detection examples
7. **Interview integration** - Video/audio clips from key stakeholders

## 📚 Related Reading

- [Frontiers Annual Reports](https://www.frontiersin.org/about/annual-reports)
- [Frontiers Research Integrity](https://www.frontiersin.org/about/research-integrity)
- [UNITED2ACT Initiative](https://www.frontiersin.org/news/2024/03/05/frontiers-joins-united2act-to-combat-paper-mills-in-scholarly-publishing)
- [Frontiers Planet Prize](https://www.frontiersin.org/planet-prize)

## 🤝 Attribution

**Data:** Frontiers Media SA (2024)
**Narrative & Visualization:** Created to showcase data storytelling capabilities
**Libraries:** Plotly.js, D3.js

---

**Contact for questions about methodology, data sources, or potential collaborations.**
