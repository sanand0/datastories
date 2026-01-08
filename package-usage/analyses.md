# Analyses to Perform

- Core gap metric: log10(dependents_count + 1) - log10(dependent_repos_count + 1), rank top outliers within each platform. This reveals packages that are deeply depended on by other packages but not used much directly. Cool because it spots hidden infrastructure in plain sight.
- Hidden champions list: high dependents_count, low dependent_repos_count, and low stars/forks; surface the most extreme names. This shows the quiet workhorses of the ecosystem. Cool because these are the invisible packages everyone benefits from.
- Reverse gap list: high dependent_repos_count, low dependents_count to identify app-heavy but library-light packages. This shows packages popular with app devs but rarely used as building blocks. Cool because it highlights tools that feel big but are not core plumbing.
- Log-log scatter (dependents_count vs dependent_repos_count) with regression line; highlight largest positive/negative residuals. This shows who breaks the usual pattern between library usage and app usage. Cool because the outliers are where the stories live.
- Distribution shape checks: power-law vs log-normal fit for dependents_count and dependent_repos_count; compare PyPI vs npm. This shows whether popularity is dominated by a tiny elite or more evenly spread. Cool because it tells us how fragile or robust the ecosystem might be.
- Concentration analysis: what share of total dependents_count is captured by top 1%, 5%, 10% packages. This shows how much the ecosystem relies on a small set of packages. Cool because it reveals if a few packages hold up the whole stack.
- License segmentation: gap metric and outlier prevalence by normalized_licenses/license_normalized. This shows whether certain licenses are more common in hidden plumbing. Cool because it links legal choices to real usage patterns.
- Domain segmentation: classify by keywords/description (rules + NLP clustering) into web/ML/infra/etc; compare gap metric by domain. This shows which fields have the most hidden infrastructure. Cool because it tells us where the invisible work happens.
- Staleness vs dependence: time since latest_release_published_at vs dependents_count; find critical but stale packages. This shows important packages that may be aging quietly. Cool because it spots potential future pain points early.
- Release cadence cohorts: derive first_release_year, last_release_year, releases_per_year from versions[]; compare gap metric by cohort. This shows whether old or slow-moving packages are still essential. Cool because it challenges the idea that only fast-moving packages matter.
- "Critical but fragile" index: high dependents_count with low contributions_count and low stars/forks plus high staleness. This shows packages many rely on but few people support. Cool because it identifies the riskiest bottlenecks.
- Deprecation risk: packages with status/deprecation_reason set and high dependents_count. This shows where the ecosystem depends on packages that are winding down. Cool because it reveals hidden technical debt.
- Repository host segmentation: group by repository_url host/org; identify orgs hosting many hidden champions. This shows who is quietly powering the ecosystem. Cool because it uncovers unexpected stewards.
- Rank vs reality: compare Libraries.io rank to gap metric; find packages that are more depended upon than their rank implies. This shows underappreciated packages that punch above their weight. Cool because it catches the underrated heroes.
- Cross-ecosystem name collisions: same package names in PyPI and npm; compare gap metrics and popularity fields. This shows whether a name means the same thing in both worlds. Cool because it can reveal surprising parallels or mismatches.
- Keyword surprises: extract top keywords among hidden champions vs mainstream packages; note surprising terms. This shows themes that are more common in hidden plumbing than in popular apps. Cool because it highlights the unseen tech stack.
- Cluster analysis: vectorize keywords/description + numeric metrics; cluster to find unusual high-variance groups. This shows distinct populations of packages beyond the obvious categories. Cool because it uncovers hidden tribes.
- Leverage point candidates: packages with high dependents_count but low dependent_repos_count and low stars/forks (high upside for docs/visibility). This shows where small attention could have big ecosystem impact. Cool because it suggests easy wins.

## Steps Run

- Loaded cached Libraries.io pages for PyPI and npm from `.cache/libraries-io/*` (10,000 packages each).
- Cleaned and normalized fields, then computed derived metrics: `gap`, `reverse_gap`, log transforms, staleness, release cadence, hidden_score, and critical_fragile.
- Tagged domains from keywords/description and built clusters using TF-IDF + numeric features.
- Saved all results to `analysis_results/` as CSVs and PNGs (plots are the log-log and staleness scatterplots per platform).
- Ran robustness checks: gap threshold sensitivity, min-repo filters, 80% subsample stability, shuffled placebo correlations, domain-level correlations, regression controls, ratio-vs-gap comparisons, zero-repo shares, and outlier host distributions. Outputs are in `analysis_results/robustness_*.csv`.

## Findings (ELI15)

- Dependence is very concentrated: the top 1% of packages carry ~54% of all PyPI dependents and ~42% of all npm dependents. That means a tiny core holds up most of the ecosystem. See `analysis_results/concentration.csv`.
- Library-use counts look more like a power law, while direct-repo-use counts look more log-normal. In plain terms: package-to-package usage is “winner-take-most,” but app usage is a bit more spread out. See `analysis_results/distribution_fits.csv`.
- Hidden champions in PyPI are heavily clustered around Alibaba Cloud utils (e.g., `alibabacloud-*`). In npm, the top hidden champions have very odd names and near-zero dependent repos, which smells like auto-generated or vendor-only packages. See `analysis_results/pypi_hidden_champions.csv` and `analysis_results/npm_hidden_champions.csv`.
- Infra is the biggest “hidden gap” domain in both ecosystems, especially npm. Infrastructure packages are depended on a lot more than they are directly used. See `analysis_results/pypi_domain_gap.csv` and `analysis_results/npm_domain_gap.csv`.
- Newer cohorts (especially 2020–2023) show higher gap values and faster release cadence. This suggests newer packages are more “library-first” than “app-first.” See `analysis_results/pypi_cadence_cohorts.csv` and `analysis_results/npm_cadence_cohorts.csv`.
- Staleness has a small negative correlation with dependence (more depended packages are a bit fresher), but there are still stale, highly depended packages like `toml`, `colorama` (PyPI) and `babel-*`, `lodash` (npm). See `analysis_results/pypi_stale_critical.csv` and `analysis_results/npm_stale_critical.csv`.
- “Critical but fragile” lists surface very old but still-relied-on packages in PyPI (e.g., `uuid`, `functools`) and common-name packages in npm. This is the quiet infrastructure that could surprise people if it breaks. See `analysis_results/pypi_critical_fragile.csv` and `analysis_results/npm_critical_fragile.csv`.
- Reverse-gap picks out packages popular with app developers but not heavily depended on by other packages (e.g., `openapi-codec` in PyPI and `prelude-ls` in npm). These feel big to users but are not core plumbing. See `analysis_results/pypi_reverse_gap.csv` and `analysis_results/npm_reverse_gap.csv`.
- There are 176 name collisions between PyPI and npm; `node` is much more “hidden” in PyPI than in npm, suggesting the same name can mean very different roles across ecosystems. See `analysis_results/cross_ecosystem_name_collisions.csv`.
- Keyword surprises show hidden champions use niche or vendor tags (e.g., `nvidia`, `cuda`, `tea`, `tong`), which hints at specialized or automated package families. See `analysis_results/pypi_keyword_surprises.csv` and `analysis_results/npm_keyword_surprises.csv`.
- Cluster analysis shows npm has large clusters around TypeScript definitions and tooling, with some clusters showing high staleness. That means a lot of the “hidden plumbing” is type metadata and build tools. See `analysis_results/pypi_clusters.csv` and `analysis_results/npm_clusters.csv`.

## Verification & Stress-Testing

- Alternative metric check: gap vs simple ratio (dependents_count / dependent_repos_count) are nearly identical (Spearman > 0.996; top-1% overlap = 100%). The hidden list is not a metric artifact. See `analysis_results/robustness_gap_ratio.csv`.
- Threshold sensitivity: moving the outlier threshold from top 1% to 0.5% or 2% preserves only ~48–50% overlap. The “absolute top” is stable, but the broader outlier set is sensitive to the cutoff. See `analysis_results/robustness_gap_thresholds.csv`.
- Min-repo filter test: requiring dependent_repos_count >= 5 or >= 20 almost wipes out the top-gap list (near-zero overlap for PyPI, low overlap for npm). This confirms the extreme gap mostly comes from packages that are barely used directly. See `analysis_results/robustness_min_repos.csv`.
- Subsample stability: 10 random 80% subsamples keep ~0.75 Jaccard overlap with the full outlier set. The signal is not just random noise, but the tail is still fragile. See `analysis_results/robustness_subsample.csv`.
- Placebo shuffle: the real correlation between package-to-package usage and app usage is strong (PyPI r≈0.89, npm r≈0.69), while shuffled data collapses to ~0.00. The association is real. See `analysis_results/robustness_shuffle_corr.csv`.
- Domain-level correlations: no Simpson’s flip for staleness (all weakly negative), but npm security shows a negative correlation between dependents and dependent repos, opposite the overall trend. This is a real segment-level reversal worth a story. See `analysis_results/robustness_domain_corr.csv`.
- Regression controls: after controlling for log_repos and stars/forks, staleness remains slightly negative (small effect), and repos are the dominant predictor (R² ~0.79 PyPI, ~0.50 npm). See `analysis_results/robustness_regression.csv`.
- Zero-dependent-repo packages are a small share of the top-10k lists (PyPI 4.4%, npm 0.8%) and contribute <0.4% of total dependents, so they do not drive overall concentration—but they dominate the extreme gap tail. See `analysis_results/robustness_zero_repo.csv`.
- Outlier provenance: PyPI gap outliers split ~47% GitHub / ~47% unknown repo host; npm outliers are ~73% GitHub. This suggests hidden champions are often not fully linked to public repos. See `analysis_results/robustness_outlier_hosts.csv`.

## Limitations, Biases, and Fallacies Checked

- Coverage bias: dataset is only the top 10,000 packages by dependents_count per ecosystem (Libraries.io search pages 1–100). Findings do not apply to the long tail.
- External validation is not done (constraint: only `.cache/` data allowed). All cross-checks use internal metadata such as stars, forks, repo_host, status.
- Definitions: dependent_repos_count reflects known repositories on Libraries.io, not actual app usage; private repos and monorepos are undercounted.
- Potential gaming: stars/forks can be gamed; vendor-generated packages can inflate dependents_count within a controlled ecosystem.
- Correlation vs causation: gaps do not mean being depended on causes low app usage; they are descriptive patterns only.
- Survivorship bias: older, well-known packages remain visible; deprecations may remove some packages from the data stream.
- Regression to the mean: extreme outliers are expected; robustness tests show the tail is sensitive to filters and thresholds.

## Selected Insights (High-Impact, Surprising, Defensible)

- Ecosystem dependence is highly concentrated: the top 1% of packages carry ~54% of PyPI dependents and ~42% of npm dependents. High-impact because it shows a tiny core holds up most software. See `analysis_results/concentration.csv`.
- Infrastructure is the hidden core: infra-tagged packages have the highest median gap in both ecosystems (especially npm). This confirms the “invisible plumbing” hunch with domain evidence. See `analysis_results/pypi_domain_gap.csv` and `analysis_results/npm_domain_gap.csv`.
- Extreme gap outliers are dominated by very low direct usage: removing packages with dependent_repos_count < 5 almost erases the outlier list. This suggests the most dramatic “hidden champions” are often vendor or auto-generated ecosystems (e.g., `alibabacloud-*`, `random-job-selector`). See `analysis_results/robustness_min_repos.csv`.
- Segment-level reversal exists: npm security packages show a negative dependents-vs-repos correlation, opposite the overall positive trend. This is a clean Simpson’s-style flip that makes a great “hidden rules differ by domain” story. See `analysis_results/robustness_domain_corr.csv`.
- Stale but critical packages are real: many high-dependents packages are multi-year stale (e.g., `babel-*`, `lodash`, `toml`, `colorama`). This is not a huge effect overall, but the specific list is defensible and compelling. See `analysis_results/pypi_stale_critical.csv` and `analysis_results/npm_stale_critical.csv`.

## Package Heroes & Outliers (Examples)

- PyPI hidden outliers with real direct use (>=5 dependent repos): `odoo` (18,189 dependents, 241 repos, gap 1.88, ~4.1y stale), `alibabacloud-tea-util` (1,056, 17, gap 1.77), `winrt-runtime` (495, 8, gap 1.74), `plumber` (530, 9, gap 1.73), `odict` (531, 10, gap 1.68). See `analysis_results/pypi_gap_outliers.csv`.
- PyPI vendor cluster that dominates the extreme tail: `alibabacloud-*` utilities show huge gaps with tiny direct-repo usage (e.g., `alibabacloud-endpoint-util` at 614 dependents vs 3 repos, gap 2.19). This looks like an internal ecosystem. See `analysis_results/pypi_gap_outliers.csv`.
- PyPI “aging pillars”: `toml` (5,158 dependents, ~5.2y stale), `colorama` (9,527, ~3.2y), `chardet` (3,493, ~2.4y) still anchor many packages despite slow release cadence. See `analysis_results/pypi_stale_critical.csv`.
- PyPI legacy/stdlib-named packages show up as fragile: `uuid`, `functools`, `wsgiref` have 18–20 years of staleness but still appear in dependents lists, likely as compatibility shims. See `analysis_results/pypi_critical_fragile.csv`.
- npm extreme gap outliers include strange-name packages: `random-job-selector` (102,405 dependents, 6 repos, gap 4.17), `@types/hyper-function-component` (30,112, 4, gap 3.78), and `unique-names-generator` (76,656, 105, gap 2.86). These dominate the extreme tail and may reflect auto-generated or vendor ecosystems. See `analysis_results/npm_gap_outliers.csv` and `analysis_results/npm_hidden_champions.csv`.
- npm “real” hidden infrastructure: `@aws-sdk/middleware-content-length` (760 dependents, 4 repos, gap 2.18), `@aws-sdk/util-body-length-node` (575, 4, gap 2.06), `@alifd/next` (11,215, 82, gap 2.13). These are recognizable packages with strong hidden-usage signals. See `analysis_results/npm_metrics.csv`.
- npm app darlings (reverse gap): `prelude-ls` (406,379 repos vs 1,417 dependents) and `superagent` (65,452 vs 10,850) are widely used directly but not deeply depended upon by other packages. See `analysis_results/npm_reverse_gap.csv`.
- npm aging pillars: `babel-core` (~7.7y stale), `babel-eslint` (~5.9y), `lodash` (~4.9y), `ts-node` (~2.1y) still sit on huge dependent trees. See `analysis_results/npm_stale_critical.csv`.
- Cross-ecosystem split personality: `node` is a much more “hidden” package in PyPI (538 dependents vs 17 repos, gap 1.48) than in npm (2,193 vs 845, gap 0.41), showing the same name plays very different roles. See `analysis_results/cross_ecosystem_name_collisions.csv`.

## Story Pack Notes (for another agent)

- Core datasets: `analysis_results/pypi_metrics.csv` and `analysis_results/npm_metrics.csv` contain all derived metrics per package.
- Key lists to quote: hidden champions (`analysis_results/pypi_hidden_champions.csv`, `analysis_results/npm_hidden_champions.csv`), stale criticals (`analysis_results/pypi_stale_critical.csv`, `analysis_results/npm_stale_critical.csv`), leverage candidates (`analysis_results/pypi_leverage_candidates.csv`, `analysis_results/npm_leverage_candidates.csv`).
- Key evidence charts: log-log scatter and staleness plots (`analysis_results/pypi_loglog_scatter.png`, `analysis_results/npm_loglog_scatter.png`, `analysis_results/pypi_staleness_scatter.png`, `analysis_results/npm_staleness_scatter.png`).
- Robustness proofs: `analysis_results/robustness_gap_ratio.csv`, `analysis_results/robustness_gap_thresholds.csv`, `analysis_results/robustness_min_repos.csv`, `analysis_results/robustness_subsample.csv`, `analysis_results/robustness_domain_corr.csv`.
- Interesting tidbits: npm hidden champions include extremely odd names with near-zero dependent repos (possible auto-generated packages). PyPI hidden champions are heavily clustered around `alibabacloud-*` utilities. PyPI gap outliers often lack a repo host link, while npm outliers mostly live on GitHub.
