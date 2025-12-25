# Music Emotion Prediction from Audio Features

## Initial model

Develop and compare multiple modelling approaches to predict emotional response proportions for music tracks based **strictly** on audio features.

The dataset consists of 400 one-minute audio excerpts across four genres: `classical`, `rock`, `pop`, and `electronic`.

- **Audio Path:** `emotify/{genre}/{1..100}.opus`
- **Annotations:** `emotify/data.csv` contains ~8,400 rater-track entries.
- **Emotional Scale:** 9 GEMS categories (amazement, solemnity, tenderness, nostalgia, calmness, power, joy, tension, and sadness).
- **Target Calculation:** For each track i and emotion e:
  - k(i,e) = Count of raters who selected emotion e.
  - n(i) = Total number of raters for track i.
  - **Target:** p(i,e) = k(i,e) / n(i) (The probability/proportion of the emotion).

Libraries available: `numpy`, `scipy`, `pandas`, `scikit-learn`, `torch`, `torchaudio`, `librosa`, `xgboost`.
ffmpeg is also installed.
Install whatever else is required.

Use a stratified Shuffle Split: Random 80/20 split, maintaining genre balance.
Leave-One-Genre-Out: Train on 3 genres and test on the 4th to evaluate cross-genre generalization.

Extract features that will enable higher accuracy models. Consider (but don't limit to) spectral centroid, rolloff, bandwidth, flatness, onset strength, energy envelope variance, attack rates. Aggregate windowed features using mean, standard deviation, and 25th/75th percentiles to create a fixed-length vector per song.
Ignore metadata like filenames or folder-based genre labels during feature extraction.

Metrics:

- **MAE:** Mean Absolute Error on p(i,e) (per emotion and macro-averaged).
- **Correlation:** Pearson and Spearman correlation between predicted and ground truth proportions.
- **Top-K Overlap:** Accuracy of the model in predicting the top 3 most-voted emotions for a track.
- **Calibration:** Comparison of predicted probabilities vs. observed frequencies.

Compare the metrics across the approaches and recommend the best approach.

Share a summary of the results in SUMMARY.md.

Commit as you go.

## List features

Which features have the best predictive power? Does this vary across emotions? Analyze and explain this in SUMMARY.md.

## Narrate the story

Create a single HTML page (index.html + script.js + data/config) that narrates a data-driven story about the distribution of emotions across the songs - how humans score them, the bias and noise, etc. Write about what features predict this best and how, and what that means.

Write in the style of Malcolm Gladwell. Visualize like the NYT graphics team. Think like a detective who must defend findings under scrutiny.

- **Compelling hook**: Start with a human angle, tension, or mystery that draws readers in
- **Story arc**: Build the narrative through discovery, revealing insights progressively
- **Integrated visualizations**: Beautiful, interactive charts/maps that are revelatory and advance the story (not decorative)
- **Concrete examples**: Make abstract patterns tangible through specific cases
- **Evidence woven in**: Data points, statistics, and supporting details flow naturally within the prose
- **"Wait, really?" moments**: Position surprising findings for maximum impact
- **So what?**: Clear implications and actions embedded in the narrative
- **Honest caveats**: Acknowledge limitations without undermining the story

Link to sources wherever relevant, and be liberal. Embed .opus files as examples - but not more than 10. I will be committing only the files you embed to save space.
This repository will be deployed on GitHub under https://github.com/sanand0/datastories/ under the `emotify` folder and deployed via GitHub Pages at https://sanand0.github.io/datastories/emotify/. Link to sources on GitHub or GitHub Pages as required.

Commit as you go.

## Revert the visualization

I didn't like the story. The visualization has bugs and poor quality. So I'll have Claude re-do this.

Delete index.html and any files required ONLY for the data visualization.

Create a README.md that has the complete context of this project, each file, what you did and how, what insights come out of it, and points to cover in a story. I will provide that as context to Claude and have it re-do this task.

Commit.

## Visualize the story

Same prompt as [Narrate the story](#narrate-the-story) but with this prefix.

Read README.md for context about this project.

## Fix bugs and redesign

The "Top Features by Emotion" card was empty except for the title and subtitle. The canvas was empty.
Same with the "Performance Degrades Across Genres" card.

The console showed this error.

```
Error loading data: TypeError: emotionFeatures.filter is not a function
    at script.js:328:45
    at Array.forEach (<anonymous>)
    at createEmotionFeaturesChart (script.js:327:20)
    at initCharts (script.js:28:5)
    at script.js:17:5
```

The term "spectral contrast" isn't clear enough. Explain it ultra-intuitively. Similarly, explain other features intuitively. Examples are nice, too.

Don't mention Malcolm Gladwell, NYT graphics team, or any of that, explicitly.

Also, redesign. Prefer creative, distinctive frontends that surprise and delight, not generic, "on distribution" outputs.

Focus on:

- Typography: beautiful, unique, and interesting fonts, not generic fonts like Arial and Inter. Opt for distinctive choices that elevate the frontend's aesthetics.
- Color & Theme: Commit to a cohesive aesthetic. Use CSS variables for consistency. Dominant colors with sharp accents outperform timid, evenly-distributed palettes. Draw from real-life / cultural aesthetics for inspiration. Ensure high readability.
- Motion: Use animations for effects and micro-interactions. Prioritize CSS-only solutions for HTML. Focus on high-impact moments: one well-orchestrated page load with staggered reveals (animation-delay) creates more delight than scattered micro-interactions.
- Backgrounds: Create atmosphere and depth rather than defaulting to solid colors. Layer CSS gradients, use geometric patterns, or add contextual effects that match the overall aesthetic.

Override framework / browser defaults to avoid generic AI-generated aesthetics:

- Overused font families (Inter, Roboto, Arial, system fonts)
- Clichéd color schemes (particularly purple gradients on white backgrounds)
- Predictable layouts and component patterns
- Cookie-cutter design that lacks context-specific character

Interpret creatively and make unexpected choices that feel genuinely designed for the context. Vary between light and dark themes, different fonts, different aesthetics. You still tend to converge on common choices across generations. Avoid this: it is critical that you think outside the box!

Commit as you go.

## Package

Create a folder called emotify/ that contains all files required to run the visualization (as well as linked files). ZIP data.csv (and revise the link) to save space. I will be copying just the emotify/ folder and committing it to GitHub.

## Compare with humans

Is the randomforest prediction better or worse than humans? I mean, if randomforest made a prediction, how often does this lie within the range of predictions made by humans and how often outside of it? Is it as good as a human, or better or worse, at aligning with others?

Think about how to measure this. Measure it. Then append your analysis to SUMMARY.md.

Commit.

## Update story

Update the visualization story using this additional information, and using the same style as before: How well does the RandomForest align with human raters compared to a single human rater? Is it "as good as a human" at aligning with other raters?

Make sure the correction does not appear like edits, an addendum, or a patch. It should be seamlessly integrated into the original story.

```markdown
## RandomForest vs. Human Agreement (Range + Alignment)

Question: is the RandomForest “as good as a human” at aligning with other raters? Two complementary checks help:

1) **Within the human consensus range (statistical)**
   For each track/emotion in the **stratified test set**, compute a 95% **Wilson** confidence interval for the human proportion (based on all rater labels), then check whether the RF prediction falls inside.

   - **RF within 95% human CI (macro): 0.817**
   - By emotion: amazement 0.888, solemnity 0.863, tenderness 0.800, nostalgia 0.838, calmness 0.738, power 0.863, joy 0.700, tension 0.812, sadness 0.850.

   Interpretation: about **82%** of RF predictions land inside the human-consensus interval. The hardest emotions for “within-range” alignment are **joy** and **calmness**.

   Additional “human range” definitions (macro coverage):
   - **Clopper–Pearson exact 95% CI:** 0.857
   - **Jeffreys posterior 90% credible interval:** 0.711
   - **Bootstrap 95% interval (binomial resampling of raters):** 0.679

   Interpretation: exact intervals are more forgiving; bootstrap/Jeffreys are tighter and reduce coverage. RF still lands inside most human ranges, but the definition of “range” matters.

2) **RF vs. a single human at matching the crowd (expected MAE)**
   Treat a single rater’s label as a “prediction” of the crowd proportion. For each track/emotion, the expected absolute error of a single human is:
   **E|Y − p| = 2·p·(1 − p)**, where `p` is the crowd proportion.

   - **RF MAE (macro): 0.116**
   - **Expected single‑human MAE (macro): 0.267**
   - **RF / human ratio: 0.43**

   Interpretation: the RandomForest aligns **substantially better** with the crowd mean than a single random human does.

3) **Strict “range of human labels” (unanimity test)**
   If all raters for a track/emotion are unanimous (all 0 or all 1), the human label range collapses to a point. In those cases, RF predictions rarely hit *exactly* 0 or 1:

   - **Unanimous cases (fraction of track/emotion pairs): 0.144**
   - **RF outside the strict unanimous range: 1.00**

   Interpretation: RF is **almost never perfectly extreme**, even when humans are unanimous. This is expected for a regressor and suggests modest “hedging” compared to unanimous human votes.
```

Copy updated files to emotify/ and commit.
