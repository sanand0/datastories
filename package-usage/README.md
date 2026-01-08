# The Invisible Infrastructure

**A data-driven investigation into the packages holding up the software world**

[View the story →](https://sanand0.github.io/datastories/package-usage/)

## What's This About?

Ever wonder what's really holding up the software ecosystem? Spoiler: it's not the packages with the most GitHub stars.

This data story reveals the invisible infrastructure of open source—packages that thousands of other packages depend on, but that almost no one has heard of. We're talking about packages like `random-job-selector` (102,405 dependents, 6 repositories using it) and `colorama` (9,527 dependents, untouched for 3.2 years). The unsung heroes. The quiet workers. The aging pillars.

We analyzed the top 10,000 packages in both PyPI and npm to find out:
- Which packages are secretly holding up half the ecosystem (hint: the top 1% carries 54% of PyPI's weight)
- Why infrastructure packages are the most invisible
- Which critical packages haven't been updated in years
- How the same package name can mean completely different things in Python vs JavaScript

Think of it as investigative journalism for software dependencies. With charts.

Read the full story: **[index.html](index.html)**

## How Was This Generated?

This project is a collaboration between human curiosity and AI analysis:

1. **Prompts**: See [`prompts.md`](prompts.md) for the exact prompts used to generate the analyses and story
2. **Data Source**: Libraries.io API cache (top 10,000 packages by dependent count for PyPI and npm)
3. **Analysis**: Python scripts calculated gaps, staleness, domain classifications, and robustness checks
4. **Story**: Written in narrative-driven style à la Malcolm Gladwell
5. **Visualization**: Interactive D3.js charts with NYT Upshot aesthetic

The process was iterative—start with interesting questions, run analyses, stress-test findings, then weave the defensible insights into a compelling narrative.

## What Analyses Were Performed?

We went deep. Like, "wake up at 3am wondering if the correlation is real" deep.

### Core Analyses

- **Gap Metric**: `log₁₀(dependents) - log₁₀(direct_repos)` to find packages depended upon far more than they're used directly
- **Hidden Champions**: Packages with high dependents, low direct usage, and minimal stars—the invisible elite
- **Aging Pillars**: Critical packages that haven't been updated in years (looking at you, `babel-core` with 7.7 years of staleness)
- **Concentration**: Top 1%, 5%, 10% share of total dependencies (spoiler: it's concentrated)
- **Domain Segmentation**: Infrastructure vs web vs ML vs security—who hides the most?
- **Cross-Ecosystem Collisions**: 176 packages exist in both PyPI and npm with the same name but different roles
- **Reverse Gap**: Packages popular with developers but not used as building blocks

### Robustness Checks

Because we're not monsters who publish unverified patterns:

- ✅ Alternative metrics (gap vs simple ratio)
- ✅ Threshold sensitivity tests
- ✅ Subsample stability checks (80% random samples)
- ✅ Placebo tests (shuffle correlation = 0.00, real correlation = 0.89/0.69)
- ✅ Domain-level correlations (found a Simpson's paradox in npm security!)
- ✅ Regression controls for confounders
- ✅ Zero-dependent-repo edge case analysis

See [`analyses.md`](analyses.md) for exhaustive details, findings, and robustness results.

## The Code

### File Structure

```
package-usage/
├── index.html                           # Main interactive story (39KB)
├── README.md                            # This file
├── prompts.md                           # Prompts used to generate analyses
├── analyses.md                          # Exhaustive analysis details
├── fetch_libraries.py                   # Data collection script (5.5KB)
├── run_analyses.py                      # Analysis pipeline (38KB)
└── analysis_results/                    # Data files (5.5MB total)
    ├── pypi_metrics.csv                 # PyPI full dataset (2.4MB) ⭐ loaded by index.html
    ├── npm_metrics.csv                  # npm full dataset (3.1MB) ⭐ loaded by index.html
    ├── concentration.csv                # Top 1%, 5%, 10% shares (602 bytes)
    ├── cross_ecosystem_name_collisions.csv  # 176 packages in both ecosystems (15KB)
    ├── pypi_stale_critical.csv          # Aging PyPI packages (15KB)
    └── npm_stale_critical.csv           # Aging npm packages (17KB)
```

### Python Scripts

These scripts were used to generate the data and analyses. They're included for reproducibility and understanding.

**[`fetch_libraries.py`](fetch_libraries.py)** — Data collection from Libraries.io API
- Fetches top 10,000 packages by dependent count for PyPI and npm
- Uses rate-limiting (60 requests/minute) and retry logic with exponential backoff
- Caches results to `.cache/libraries-io/` to avoid re-fetching
- Outputs raw data to `pypi-repos.csv` and `npm-repos.csv`
- Uses `uv run --script` for zero-install execution with inline dependencies

**[`run_analyses.py`](run_analyses.py)** — Complete analysis pipeline
- Loads cached Libraries.io data and computes derived metrics:
  - **Gap metric**: `log₁₀(dependents) - log₁₀(repos)` to identify hidden infrastructure
  - **Staleness**: Years since last release
  - **Domain classification**: Web, ML, data, infra, security, devtools based on keywords
  - **Release cadence**: First/last release, releases per year
- Generates 20+ different analyses (hidden champions, concentration, collisions, etc.)
- Runs robustness checks (subsample stability, placebo tests, threshold sensitivity)
- Exports all results as CSV files to `analysis_results/`
- Creates scatter plots and distributions (PNG files, not included in final repo)

**To run these scripts:**
```bash
# Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# Data collection (requires LIBRARIES_IO_API_KEY in .env)
uv run fetch_libraries.py

# Run analyses (requires cached data)
uv run run_analyses.py
```

### Data Files Explained

**Required by index.html:**
- **[`pypi_metrics.csv`](analysis_results/pypi_metrics.csv)** / **[`npm_metrics.csv`](analysis_results/npm_metrics.csv)**: Complete dataset with all derived metrics (gap, staleness, domains, etc.) for 10,000 packages per ecosystem

**Documentation/Reference:**
- **[`concentration.csv`](analysis_results/concentration.csv)**: Shows how much the top 1%, 5%, 10% of packages control total dependencies
- **[`pypi_stale_critical.csv`](analysis_results/pypi_stale_critical.csv)** / **[`npm_stale_critical.csv`](analysis_results/npm_stale_critical.csv)**: Packages with high dependents but years of staleness
- **[`cross_ecosystem_name_collisions.csv`](analysis_results/cross_ecosystem_name_collisions.csv)**: The 176 packages that exist in both PyPI and npm with identical names

### Visualization

**[`index.html`](index.html)** — A self-contained interactive story (39KB, no external dependencies except D3.js CDN)

**Design Aesthetic**
- NYT Upshot-inspired typography (Georgia serif for body, Helvetica for UI)
- Muted color palette (#e05915 primary orange, neutral grays)
- Generous white space and readable 680px line length
- CSS-only animations with staggered reveals for progressive disclosure

**Interactive Charts** (D3.js v7)
1. **Concentration Bar Chart**: Animated bars showing top 1%, 5%, 10% share of dependencies
2. **PyPI Scatter Plot**: 10,000 packages plotted log-log (dependents vs direct repos) with labeled outliers
3. **npm Scatter Plot**: Same design, highlighting different ecosystem patterns

**Interactive Features**
- Hover tooltips with detailed package stats (dependents, repos, gap, stars)
- Direct labels for notable packages (no hover required)
- Scroll-triggered fade-ins and slide-ups
- Responsive design (works on mobile, but charts shine on desktop)

**Data Flow**
```javascript
// Load metrics CSVs
d3.csv('analysis_results/pypi_metrics.csv')
  → filter valid data
  → parse numeric fields
  → createScatterPlot()
    → log scales (log₁₀)
    → diagonal reference line (y = x)
    → color by gap (outliers orange)
    → label notable packages
    → animate reveals
```

## Key Findings

The story highlights:

- **Concentration**: Top 1% of packages hold 54% of PyPI dependencies, 42% of npm
- **Infrastructure is invisible**: Infrastructure packages have the highest gaps (0.74 median in npm)
- **Aging gracefully?**: Many critical packages haven't been updated in 3-7+ years
- **Vendor ecosystems**: Alibaba Cloud utilities dominate PyPI's extreme outliers
- **Mysterious packages**: npm's top gaps include packages with bizarre names and near-zero stars
- **Split personalities**: The `node` package is hidden infrastructure in PyPI (gap 1.48) but visible in npm (gap 0.41)

## Deployment

This story is part of the [Data Stories](https://github.com/sanand0/datastories/) collection:

- **Repository**: `sanand0/datastories/package-usage/`
- **Live URL**: https://sanand0.github.io/datastories/package-usage/
- **Hosting**: GitHub Pages

To view locally:
```bash
# Simple HTTP server (Python 3)
python -m http.server 8000

# Or use any local server
# Then open http://localhost:8000
```

## Limitations & Caveats

Because honesty is a virtue:

- Sample limited to top 10,000 packages per ecosystem (the long tail is uncharted)
- Direct repository counts undercount private repos and monorepos
- Extreme outliers may reflect vendor ecosystems, auto-generated packages, or data artifacts
- No causal claims—this is descriptive analysis of patterns in the dependency graph
- Staleness doesn't always mean "abandoned"—sometimes it means "finished"

## License & Data

- **Story & Code**: Creative Commons Attribution 4.0 International (CC BY 4.0)
- **Data Source**: [Libraries.io](https://libraries.io/) (open data project)
- **Analysis**: Generated with Claude Code and validated through robustness checks

## Questions? Feedback?

Found something interesting? Spotted an error? Have a theory about `random-job-selector`?

Open an issue in the [main Data Stories repo](https://github.com/sanand0/datastories/issues).

---

*"The invisible infrastructure is invisible for a reason: it works so well we forget it exists. Until it doesn't."*
