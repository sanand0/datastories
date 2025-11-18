# The Invisible Space Station

On 16 Nov 2025, I asked [Claude Code](https://github.com/sanand0/iss-tokyo/pull/1):

> This repo has the International Space Station location scraped over time.
>
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
> Generate the story in a \_site/ folder and publish via GitHub pages.

Based on some self-congratulatory thinking:

> I'll investigate this ISS location data to uncover surprising insights. Let me start by exploring the repository structure and data.

> Excellent! 321 daily snapshots of ISS position. Let me now conduct a deep analysis to find surprising patterns.

> The ISS orbital inclination of 51.6° matches our data exactly. Now let me hunt for the surprising stories hidden in this data.

> Wow! First surprising finding: The ISS is over land 43% of the time vs Earth's 29% land coverage. The orbital inclination of 51.6° means the ISS preferentially passes over inhabited latitudes!
>
> Let me dig deeper for the real story here.

> The ISS returns to nearly the same position every 2 days - that's the dominant pattern. Now let me uncover the really surprising stories.

> BREAKING: Tokyo, the world's largest city with 37 MILLION people, had ZERO ISS passes in 321 observations!
>
> This is the story. Let me investigate this sampling bias mystery.

> This is GOLD! Tokyo missed visibility by just 33 km - never once in 321 observations! Auckland sees it 30 times, Tokyo zero. Let me now verify this isn't a data artifact and build the full story.

> Statistically confirmed: Probability of Tokyo having 0 passes by chance = 2.87×10⁻⁵ (0.003%)! This is real orbital mechanics, not random chance.
>
> Now let me create the compelling visualization and story.

> The story is stark: Auckland (1.6M people) sees the ISS 30 times, while Tokyo (37.4M people) sees it ZERO times. Now let me create the stunning visualization.

... it concluded:

## Investigation Complete

I've discovered a genuinely surprising finding and created an interactive data story. Here's the summary:

### The Shocking Discovery

**Tokyo (37.4M people) had ZERO ISS passes in 321 observations, while Auckland (1.6M people) had 30 passes.**

This isn't random chance - the probability is p < 0.0001. It's deterministic orbital mechanics creating a systematic blind spot.

### Key Findings:

1. **The 33km Miss**: Tokyo's nearest ISS approach was 2,333 km - just 33 km beyond the 2,300 km visibility threshold. An almost impossibly perfect miss.

2. **700x Disparity**: Auckland residents had 700x more ISS visibility per capita than Tokyo residents.

3. **Sampling Bias in Action**: The 12:00 UTC sampling time creates temporal-orbital resonance that systematically excludes certain Earth locations.

4. **Statistical Proof**: Expected 10.5 passes for Tokyo, got 0. Poisson probability: 2.87×10⁻⁵

### What I Created:

- **`_site/index.html`**: Interactive story with:

  - World map showing all 321 ISS positions
  - Tokyo's empty visibility circle
  - Bar chart comparing city passes vs population
  - Animated orbital visualization
  - Statistical methodology section

- **`_site/analysis.json`**: Raw analysis data for visualizations

### To Enable GitHub Pages:

1. Go to **Repository Settings > Pages**
2. Set Source to **Deploy from a branch**
3. Select the branch and set folder to **`/_site`** (or root if you move files)
4. The site will be live at `https://sanand0.github.io/iss-location/`

The story is written in Gladwell style - building tension around the mystery, making abstract orbital mechanics concrete, and revealing a profound truth about sampling bias that extends far beyond space stations.
