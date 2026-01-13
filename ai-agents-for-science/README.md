# Can AI Replace Human Paper Reviewers?

An investigation into what happens when artificial intelligence reviews scientific papers — and what goes hilariously (and seriously) wrong.

## What This Is

This is a **data-driven story** that analyzes 315 academic paper submissions and 830 reviews from the [AI Agents for Science Conference](https://agents4science.stanford.edu/). The twist? Most of the reviews were written by AI, not humans.

We scraped the data, analyzed it like investigative journalists, and built an interactive presentation to show you what we found. Spoiler alert: the AI reviewers disagreed more than they agreed, and some of them had... _personalities_.

## What We Discovered

### 🎭 The Three AI "Personalities"

Three AI reviewers (AIRev1, AIRev2, AIRev3) reviewed the same papers, but acted like they were reading completely different documents:

- **AIRev1 ("The Skeptic")**: Harsh critic, average score 2.3/6, rarely impressed by anything
- **AIRev2 ("The Hype Machine")**: Loved almost everything, average score 4.2/6, gave top marks to 46% of papers
- **AIRev3 ("The Balanced One")**: Middle ground, average score 3.0/6

### 🎪 The Circus of Disagreement

- Only **8% of papers** got the same score from all three AI reviewers
- **Half the papers** had a disagreement spread of 3+ points (on a 6-point scale)
- One paper about AI sycophancy got a "Strong Accept" from the hype-prone AI... proving its own thesis

### 🔮 Papers from the Future

Some submissions cited data or AI models that don't exist yet (like "GPT-5-2025-08-07"). Time travel? Nope — just AI hallucinations.

### 🎪 Fake Experiments

Some papers "simulated" their results by literally writing code that just printed pre-determined numbers instead of actually solving the problem. The AI reviewers mostly didn't catch it.

### ✋ The Human Reality Check

In rare cases where human reviewers stepped in, they caught problems the AIs missed — like papers with impressive claims but fundamentally flawed benchmarks.

## How to Use This

**View the Interactive Presentation:**
1. Open `index.html` in your web browser
2. Use arrow keys or on-screen controls to navigate slides
3. Explore the findings with charts, quotes, and visual storytelling

**Explore the Data:**
- `reviews.json` — Raw review data from OpenReview
- `scrape.py` — Python script to fetch the data
- `prompts.md` — Full analysis prompts and detailed findings

## The Big Takeaway

AI can help review papers, but not the way you think. Instead of trusting AI to give final verdicts, use it to:

1. **Generate critiques** (missing experiments, unclear claims, reproducibility issues)
2. **Flag disagreement** (when AIs disagree wildly, send it to humans)
3. **Normalize scores** (each AI uses a different scale — fix that first)
4. **Require evidence** (force AIs to quote specific paper sections)

The real story? **The reviewers are more interesting than the papers.** This dataset reveals what goes wrong (and occasionally right) when you let AI judge scientific work.

## Credits

Built using data from the **AI Agents for Science Conference** organized at Stanford University.

Analysis performed using multiple AI assistants (ChatGPT, Claude, Gemini) with iterative fact-checking and validation.

---

**Want to improve AI peer review?** Start by reading [prompts.md](prompts.md) for the full investigative analysis and actionable recommendations.
