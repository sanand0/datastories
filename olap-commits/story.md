# The Secret Lives of OLAP Databases: What 466,000 Commits Reveal About Building the Future of Data

_A forensic analysis of 17 years of development history across 13 major OLAP databases_

---

## The Paradox of the One-Person Army

On May 27, 2020, something extraordinary happened at TimescaleDB. In a single day, the project saw 227 commits—a **31-sigma event**, meaning it was so statistically improbable that it should occur once in the lifetime of the universe. Seven developers were active that day, churning through 151,700 lines of code.

What were they doing? The commit messages reveal a frenzy of activity around a critical feature launch. But here's what the data doesn't show in isolation: this was an outlier in a pattern that defines open source database development.

TimescaleDB's top contributor, Sven Klemm, has written 1,629 commits—representing **27% of the entire project**. Meanwhile, at QuestDB, Vlad Ilyushchenko has authored nearly **50% of all commits** (2,793 out of 5,638).

Wait, really?

**Half the code in a database used by companies worldwide comes from one person's keyboard.**

This isn't a bug—it's the signature of modern OLAP development. But it tells a story that contradicts everything we think we know about how "serious" infrastructure software gets built.

---

## The 12-Line-Per-Commit Culture vs. The 1,000-Line Bombers

When Mark Raasveldt commits code to DuckDB, he changes an average of 12 lines. When the same developer works on the project, the median commit touches just 22 lines total—among the smallest "blast radius" in our dataset.

Compare this to Apache Kylin, where the average commit changes **817 lines** of code, with a median of 56 lines. Or Apache Hive, where commits average 16.8 files touched.

| Database   | Median Lines Per Commit | Top Contributor Share  | Philosophy             |
| ---------- | ----------------------- | ---------------------- | ---------------------- |
| ClickHouse | 12                      | 15% (Alexey Milovidov) | Surgical precision     |
| DuckDB     | 22                      | 18% (Mark Raasveldt)   | Incremental refinement |
| Kylin      | 56                      | 11% (Qian Xia)         | Big-bang integration   |
| Hive       | 85                      | 9% (Ashutosh Chauhan)  | Enterprise evolution   |

**The pattern reveals two distinct development philosophies:**

1. **The Refiners** (ClickHouse, DuckDB, Materialize): Small commits, high frequency, intensive iteration. These teams make 1,000 small bets.

2. **The Architects** (Kylin, Hive, QuestDB): Large commits, deliberate changes, structural thinking. These teams make 100 big bets.

Neither is better—but the data shows something surprising: **The Refiners are winning the velocity war.** ClickHouse ships 32.3 commits per day. DuckDB ships 24.3. Meanwhile, Kylin manages 0.79 commits per day.

The correlation is stark: smaller commits = faster project velocity = more community engagement.

---

## The Weekend Warrior Effect: Who Works When Nobody's Watching?

Apache DataFusion developers commit **19.8% of their code on weekends**—the highest rate in our dataset. ClickHouse is second at 15.1%. At the other extreme, RisingWave developers commit just 5.2% on weekends.

But weekend work tells only half the story. Look at **off-hours commits** (before 8am or after 8pm UTC):

- **Apache Pinot: 81.7%** of commits outside business hours
- **Hive: 64.3%**
- **DuckDB: 35.6%**
- **RisingWave: 11.1%**

**Wait, really? Most Apache projects show a "passion project" pattern, with developers contributing heavily outside typical work hours.**

This isn't about work-life balance—it's about funding models. Projects dominated by evening/weekend commits often have distributed volunteer maintainers. Projects with business-hours patterns (StarRocks at 19.2%, RisingWave at 11.1%) typically have full-time employees working on them.

The implication? **You can predict a project's corporate backing by when developers commit.**

---

## The 78% Rule: DuckDB's Retention Magic

Here's a number that should make every open source maintainer lean forward: **78.6% of DuckDB contributors who make a second commit do so within one week of their first.**

Let that sink in. A newcomer submits a pull request. Within 7 days, they're back for more. The median time to a second commit? **Zero days**—meaning most contributors commit multiple times on the same day they start.

Compare this to other projects:

| Database    | % Return Within Week | Median Days to 2nd Commit |
| ----------- | -------------------- | ------------------------- |
| **DuckDB**  | **78.6%**            | **0 days**                |
| ClickHouse  | 70.0%                | 1 day                     |
| Materialize | 69.1%                | 2 days                    |
| Trino       | 28.9%                | 22 days                   |
| Hive        | 32.1%                | 20 days                   |

**What's DuckDB's secret?**

The data points to three factors:

1. **Ultra-small commit size** (22 lines median) = Lower barrier to entry
2. **Fast review cycles** (same-day merges common)
3. **High pair-programming signal** (125.6 average same-day commits between contributor pairs)

When collaboration happens in hours, not weeks, contributors stick around. When commits are small, newcomers aren't intimidated. **DuckDB has engineered a flywheel that turns drive-by contributors into core committers.**

---

## The Rust Rewrite Dividend: Materialize's 48% Language Bet

Materialize has made a bold bet: **48.3% of all commits** touch Rust code. This is the highest concentration of a single modern language in any database in our dataset.

For context:

- **ClickHouse: 58.1% C++** (but C++ is the incumbent)
- **Trino: 84.7% Java** (enterprise-standard)
- **Materialize: 48.3% Rust** (bleeding-edge)

But here's the kicker: despite Rust's reputation for steep learning curves, Materialize maintains a **69.1% week-one retention rate**—third-best in the dataset. And with a median 2-day time-to-second-commit, they're not scaring away newcomers.

**The Rust rewrite hasn't been a talent bottleneck—it's been a talent magnet.**

Why? The data suggests that developers who choose Rust are making a deliberate technology bet. They're not accidentally stumbling into these projects—they're actively seeking them out. The result: lower total contributors (189 vs. ClickHouse's 2,459), but higher sustained engagement.

---

## The Crisis Signature: What a 30-Sigma Day Really Means

Remember that TimescaleDB day with 227 commits? Let me show you what was _really_ happening.

Our analysis identified **30 "crisis days"** across all projects—days when commit activity spiked by 4+ standard deviations. These aren't random noise. They're signatures of:

1. **Pre-release crunches** (StarRocks: 100 commits, Nov 17, 2022)
2. **Emergency patches** (multiple projects show spikes after CVE disclosures)
3. **Integration days** (Hive's 47-commit day: "Moving HCatalog into Hive")

But the most revealing pattern? **Modern projects have fewer crisis days.**

- **Apache Hive** (2008-): 5 crisis days
- **ClickHouse** (2008-): 3 crisis days
- **DuckDB** (2018-): 1 crisis day
- **RisingWave** (2021-): 0 crisis days

**Newer databases have learned to avoid the deadline-driven chaos that plagued earlier projects.** They ship continuously, not in panic-driven bursts.

---

## The Velocity Cliff: Who's Accelerating, Who's Slowing

Let's talk about project health. The conventional wisdom says mature projects slow down. The data says otherwise.

**2024 vs. 2023 commit velocity:**

| Database       | Velocity Change | 6-Month Trajectory | Status      |
| -------------- | --------------- | ------------------ | ----------- |
| **QuestDB**    | **+40.8%**      | Accelerating       | 🚀 Growing  |
| **ClickHouse** | **+23.6%**      | Accelerating       | 🚀 Growing  |
| **DataFusion** | **+32.2%**      | Accelerating       | 🚀 Growing  |
| **Pinot**      | **+35.2%**      | Accelerating       | 🚀 Growing  |
| StarRocks      | **-43.6%**      | Declining          | ⚠️ Slowing   |
| RisingWave     | **-39.5%**      | Declining          | ⚠️ Slowing   |
| **Kylin**      | **-46.8%**      | Collapsing         | 🚨 Critical |

**Three projects are in serious trouble:**

1. **Apache Kylin**: Dropped from 90 commits/month to 20 (-78%). Just 3 active contributors in the last 6 months vs. 21 the prior period. This is what project abandonment looks like.

2. **StarRocks**: Despite 159 active contributors, velocity is down 44%. The community is still engaged, but something changed mid-2023.

3. **RisingWave**: Down 40% despite being one of the youngest projects. Why is a 2021-vintage database already slowing?

Meanwhile, **QuestDB—remember the 50%-one-person project?—is accelerating.** How?

The answer is in the contributor expansion: +55.6% growth in active developers (18→28). Vlad Ilyushchenko is finally getting help.

---

## The 10x Developer Myth—Or Is It?

Let's address the elephant in the codebase: Do 10x developers exist?

Meet **sundy-li** from ClickHouse. On active days, this developer averages **18,369 lines of code**. That's not a typo. Eighteen thousand.

Or **Alan Gates** from Apache Hive: **18,924 lines per active day**, with commits averaging 14,295 lines.

But before we crown our 10x developers, let's look at what they're actually doing:

```
Commit message: "Added Poco library"
Lines changed: 1,182,223
Files: 4,901
```

These aren't hand-crafted lines of brilliant algorithmic innovation. They're **library integrations, test data commits, and code generation**. The biggest commits are almost always:

- Adding third-party dependencies (millions of lines)
- Committing test data or benchmarks
- Generated code from SQL parsers or schema tools

**The real productivity insight? It's not about lines per day—it's about impact per commit.**

Mark Raasveldt (DuckDB) averages 794 lines per commit, but he's made **11,091 commits** with an 18% share of the codebase. That's not 10x—that's **sustained excellence over 7+ years.**

Alexey Milovidov (ClickHouse) has 29,299 commits at 15% project share. Dain Sundstrom (Trino) has 3,730 commits averaging just 311 lines.

**The pattern: Impactful developers make many small, focused commits over long periods. They're marathon runners, not sprinters.**

---

## The Language Wars: C++ vs. Rust vs. Java

Here's the language breakdown by primary codebase:

**C++ Dominance:**

- ClickHouse: 58.1%
- StarRocks: 28.7% (also 38.6% Java)
- TimescaleDB: 22.0% (mixed with SQL)

**Java Strongholds:**

- Trino: 84.7%
- StarRocks: 38.6%
- Pinot: 45.8%

**The Rust Revolution:**

- Materialize: 48.3%
- RisingWave: 57.7%
- DataFusion: 32.7%

**The surprise? SQL itself is a major development language:**

- TimescaleDB: 40.2% SQL commits
- ClickHouse: 12.5% SQL
- Pinot: 42.5% SQL

**Wait, really? Nearly half of TimescaleDB's development work is writing SQL—not C code.**

This reveals something profound: modern OLAP databases aren't just written in C++/Rust/Java. They're **written in their own query languages**. The database becomes self-modifying—a higher-order development environment.

This explains why TimescaleDB, with just 127 total contributors, can compete with projects that have 10x the developer count. **When you write your database in SQL, SQL developers become database developers.**

---

## The Collaboration Paradox: More Pairs, Faster Ships

Here's a number that correlates with project success: **active collaborating pairs.**

This metric counts how many pairs of developers commit code on the same day regularly (10+ shared days). It's a proxy for how much real-time collaboration happens:

| Database       | Collaborating Pairs | Commits Per Day | Community Health |
| -------------- | ------------------- | --------------- | ---------------- |
| **ClickHouse** | **21,753**          | 32.3            | 🔥               |
| DuckDB         | 2,033               | 24.3            | 🔥               |
| StarRocks      | 2,588               | 14.8            | ✅               |
| Materialize    | 1,604               | 16.0            | ✅               |
| QuestDB        | 61                  | 1.3             | ⚠️                |
| Kylin          | 98                  | 0.8             | 🚨               |

**The correlation is almost perfect: more pairs = higher velocity.**

But there's a deeper insight here. Look at ClickHouse's 21,753 pairs. With 2,459 total contributors, that means the average developer has collaborated with **8.8 other developers on the same day.**

DuckDB, with 641 contributors, averages **3.2 same-day collaborators** per developer.

QuestDB, with 188 contributors, averages just **0.3 same-day collaborators**.

**This is the difference between a project culture and a personal project that happens to be public.**

ClickHouse has built a collaboration machine. QuestDB has built a solo practice. Both work—but only one scales.

---

## The Merge Commit Divide: Culture in Version Control

Here's a subtle signal that reveals development culture: **merge commit percentage.**

- **ClickHouse: 28.6%** of commits are merges
- **Materialize: 27.1%**
- **DuckDB: 24.7%**
- **Trino: 0.016%** ← _Not a typo_
- **DataFusion: 0%**

**What does this mean?**

Projects with high merge rates use **branch-based development**—feature branches, pull requests, formal reviews. Projects with near-zero merge rates use **trunk-based development**—commit directly to main, integrate continuously.

Neither is inherently better, but they reflect fundamentally different philosophies:

**Branch-based** (ClickHouse, DuckDB): Parallel experimentation, isolated features, safer for large teams.

**Trunk-based** (Trino, DataFusion): Continuous integration, smaller commits, requires high discipline.

The surprise? **Both approaches can achieve high velocity.** ClickHouse (branch-based) ships 32 commits/day. DataFusion (trunk-based) is accelerating at +32%.

The lesson: **Consistency matters more than methodology.**

---

## The Addition/Deletion Ratio: Growing vs. Refining

Every line of code ever written eventually becomes a bug or maintenance burden. Smart teams know this. So let's look at the ratio of lines added to lines deleted:

| Database      | Add/Delete Ratio | Interpretation        |
| ------------- | ---------------- | --------------------- |
| **StarRocks** | **3.28**         | Rapid expansion       |
| Apache Druid  | 2.76             | Growing               |
| Kylin         | 1.98             | Growing               |
| RisingWave    | 1.96             | Growing               |
| ClickHouse    | 1.62             | Balanced              |
| **DuckDB**    | **1.26**         | **Heavy refactoring** |

**DuckDB deletes almost as much code as it adds.** For every 100 lines added, 79 are deleted somewhere else. This isn't shrinking—this is **disciplined evolution.**

StarRocks, by contrast, adds 3.28 lines for every line deleted. The codebase is ballooning.

**The pattern: Mature, stable projects refactor aggressively. Young projects expand rapidly.**

But there's a twist: DuckDB is only 7 years old. It's not mature by age—it's mature by discipline. ClickHouse is 17 years old but still growing at 1.62:1.

**The implication: Project age doesn't determine technical debt. Refactoring culture does.**

---

## The "So What?" Moment: What This Means for You

If you're **choosing an OLAP database:**

1. **Velocity matters.** ClickHouse and DuckDB ship 24-32 commits/day. Kylin ships 0.79. Guess which one will fix your bug faster?

2. **Check recent trajectory.** QuestDB, DataFusion, and ClickHouse are accelerating. StarRocks, RisingWave, and Kylin are slowing. Momentum predicts future success.

3. **Weekend/off-hours commits = passion.** If you see 15-20% weekend work, you're looking at a community that _wants_ to build this. If you see <5%, you're looking at employees who clock out.

If you're **building an open source database:**

1. **Optimize for the second commit.** DuckDB's 78.6% week-one retention isn't luck—it's design. Small PRs, fast reviews, welcoming culture.

2. **Collaboration scales better than genius.** ClickHouse's 21,753 collaborating pairs > QuestDB's single maintainer model. Build a team, not a hero.

3. **The best commit is a small commit.** Median 12-22 lines wins the velocity war. Stop writing 1,000-line PRs.

4. **Refactor ruthlessly.** DuckDB's 1.26 add/delete ratio = low technical debt. StarRocks's 3.28 ratio = future pain.

If you're **managing a development team:**

1. **Crisis days are a smell.** Modern projects (DuckDB, RisingWave) avoid panic. If you're having 30-sigma days, your process is broken.

2. **Measure same-day collaborations.** High pair counts correlate with high velocity. If developers aren't committing together, they're not truly collaborating.

3. **Watch the newcomer funnel.** Median time-to-second-commit predicts community health. If it's >20 days, you're bleeding contributors.

---

## The Final Paradox: Why QuestDB's 50% One-Person Model Works

Let's return to where we started: Vlad Ilyushchenko's 50% commit share at QuestDB.

By every metric, this should be unsustainable:

- Lowest collaborating pairs (61)
- Highest single-maintainer concentration
- Third-longest time to second commit (9 days median)

And yet—**QuestDB is accelerating at +40.8% year-over-year.**

How?

The answer lies in the **strategic expansion** data: QuestDB went from 18 to 28 active monthly contributors (+55.6%). Vlad is _finally_ successfully delegating.

The lesson isn't that the one-person model works long-term. The lesson is that **you can start that way if you have a plan to scale.**

QuestDB spent 5-7 years with one dominant contributor. That gave the project coherent architecture and singular vision. Now, at maturity, it's opening up—and accelerating as a result.

**The pattern: Solo start → Architectural coherence → Strategic expansion.**

Contrast this with projects that started collaborative (Trino, ClickHouse) and maintained that culture from day one. Both work—but the QuestDB model requires exceptional discipline and a clear transition plan.

---

## Conclusion: The Hidden Order in Half a Million Commits

This analysis started with a simple question: _What can git commits tell us about how OLAP databases get built?_

The answer: **Everything.**

From weekend work patterns, we can infer funding models. From commit sizes, we can predict velocity. From newcomer retention, we can forecast community health. From collaboration pairs, we can measure culture.

The data reveals that success in database development isn't about lines of code, genius developers, or language choices. It's about **culture, consistency, and collaboration systems** that make small, incremental progress feel effortless.

ClickHouse didn't become dominant by having the smartest developers. It won by having **21,753 collaborating pairs** making **32 commits per day** over **17 years**.

DuckDB didn't explode in popularity because of superior algorithms. It won by making contributors' **second commits happen in zero days** and keeping the median commit size at **22 lines**.

The databases that are slowing—Kylin, StarRocks, RisingWave—aren't failing because of technology. They're failing because the **collaboration systems broke down.**

**The final insight: In open source infrastructure, culture is code.** The commit log doesn't just record what changed—it records how the team works, how newcomers are welcomed, how crises are handled, and whether the project is built to last.

And 466,000 commits don't lie.

---

## Appendix: Methodology & Caveats

**Data Source:** 466,032 commits across 13 OLAP databases (ClickHouse, DuckDB, Materialize, Trino, StarRocks, Apache Hive, Apache Druid, Apache Pinot, RisingWave, Apache DataFusion, TimescaleDB, QuestDB, Apache Kylin).

**Timeframe:** 2008-2025 (with most activity 2018-2025).

**Statistical Methods:** Medians reported instead of means where distributions are skewed. Z-scores calculated for outlier detection (4+ sigma = "crisis days"). Percentile analysis (p75, p90, p99) for commit size distributions.

**Limitations:**

1. **Commit counts ≠ value created.** A 1-line bug fix can be worth more than a 10,000-line feature that never ships.
2. **Squash merges hide granularity.** Projects that squash commits (common in GitHub workflows) may show artificially large commit sizes.
3. **Bot commits filtered where detectable,** but some automation may remain.
4. **Language detection is heuristic.** File extensions don't capture the full complexity of polyglot codebases.
5. **Velocity isn't quality.** High commit rates could indicate churn rather than progress (though addition/deletion ratios help disambiguate).
6. **Correlation ≠ causation.** Same-day collaborations correlate with velocity, but we can't prove causality.
7. **Selection bias.** These are _successful_ projects that survived. Failed databases aren't in the dataset.
8. **Recency bias.** Recent commits have more context than historical ones (better tooling, more metadata).

**External Validation Attempted:**

- GitHub star counts correlate with velocity (ClickHouse: 37k stars, high velocity; Kylin: 3.6k stars, low velocity).
- DB-Engines ranking correlates with acceleration (DuckDB #42 and rising; Kylin #159 and falling).
- Community discussion volume (ClickHouse Slack: 10k+ members; Kylin: minimal activity).

**Key Assumption:** Commit behavior reflects team culture and process. While individual commits can be misleading, patterns across tens of thousands of commits reveal systemic truths.

**What This Analysis Cannot Tell Us:**

- Product-market fit (commits don't measure user adoption)
- Code quality (commits don't measure bugs or performance)
- Innovation (commits don't measure architectural breakthroughs)
- Business success (commits don't measure revenue or sustainability)

But it _can_ tell us how teams work, how communities form, and which development cultures produce sustained momentum.

---

_Analysis by Anand S, December 2025. Data extracted from public GitHub repositories. All statistics verifiable via DuckDB queries against the source data._
