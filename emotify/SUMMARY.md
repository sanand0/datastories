# Emotify Modeling Summary

## Overview
- Computed per-track emotion proportions p(i,e) from 8,400+ rater entries (9 GEMS emotions).
- Extracted audio-only features per track (spectral centroid, rolloff, bandwidth, flatness, RMS energy, onset strength, attack rates, tempo, chroma, MFCCs, spectral contrast, ZCR) and aggregated statistics (mean, std, 25th/75th percentiles).
- Evaluated models with a stratified 80/20 split by genre and a leave-one-genre-out (LOGO) evaluation.

## Models Compared
- BaselineMean (predict per-emotion mean from training set)
- Ridge Regression (multi-output)
- Random Forest
- XGBoost
- MLP

## Results (Macro Metrics)

### Stratified 80/20 (genre-balanced)
| Model | MAE | Pearson | Spearman | Top-3 Overlap | ECE |
| --- | --- | --- | --- | --- | --- |
| BaselineMean | 0.146 | NaN | NaN | 0.479 | 0.015 |
| MLP | 0.200 | 0.210 | 0.204 | 0.554 | 0.146 |
| RandomForest | **0.116** | **0.523** | **0.550** | **0.650** | 0.031 |
| Ridge | 0.130 | 0.405 | 0.423 | 0.588 | 0.049 |
| XGBoost | 0.119 | 0.476 | 0.505 | 0.633 | 0.031 |

### Leave-One-Genre-Out (avg across genres)
| Model | MAE | Pearson | Spearman | Top-3 Overlap | ECE |
| --- | --- | --- | --- | --- | --- |
| BaselineMean | 0.149 | NaN | NaN | 0.427 | 0.055 |
| MLP | 0.219 | 0.145 | 0.154 | 0.517 | 0.161 |
| RandomForest | **0.128** | **0.389** | **0.398** | **0.584** | 0.055 |
| Ridge | 0.146 | 0.309 | 0.322 | 0.563 | 0.084 |
| XGBoost | 0.130 | 0.365 | 0.370 | 0.568 | 0.058 |

Notes:
- BaselineMean correlations are undefined (constant predictions).
- Cross-genre generalization reduces correlations and increases MAE as expected.

## Recommendation
RandomForest is the best overall approach: it delivers the lowest MAE and strongest correlations in both stratified and LOGO evaluations, while also achieving the highest top-3 emotion overlap. XGBoost is a close runner-up with similar calibration and competitive error, but slightly weaker correlations.

## Feature Importance (Permutation Importance, RandomForest)
Computed permutation importance on the stratified 80/20 split using the RandomForest model. Higher values indicate larger MAE degradation when the feature is permuted.

### Top Features Overall
1. spectral_contrast_1_p25  
2. mfcc_2_p25  
3. spectral_contrast_1_mean  
4. mfcc_2_mean  
5. onset_strength_p75  
6. mfcc_0_p75  
7. spectral_contrast_3_p25  
8. attack_rate  
9. spectral_contrast_2_p25  
10. mfcc_0_mean  

Overall signal is dominated by mid-band spectral contrast and low-order MFCC statistics, with onset strength and attack-related features contributing to arousal-related variance.

### Does Predictive Power Vary Across Emotions?
Yes. The dominant features shift by emotion, especially between arousal-heavy vs. calm/reflective categories. Top-5 features per emotion (permutation importance) are:

- amazement: mfcc_3_std, mfcc_0_p75, chroma_11_std, mfcc_0_std, mfcc_2_std  
- calmness: spectral_contrast_1_p25, spectral_contrast_1_mean, mfcc_2_p25, onset_strength_std, spectral_contrast_1_p75  
- joy: onset_strength_p75, spectral_bandwidth_std, attack_strength, spectral_contrast_1_p25, zcr_p25  
- nostalgia: spectral_contrast_1_p25, mfcc_2_p25, spectral_contrast_3_p25, attack_rate, spectral_contrast_2_p25  
- power: mfcc_2_p25, mfcc_2_mean, spectral_contrast_1_mean, spectral_contrast_1_p25, chroma_2_p25  
- sadness: spectral_contrast_1_p25, spectral_contrast_1_mean, spectral_flatness_std, spectral_contrast_5_std, spectral_contrast_1_p75  
- solemnity: attack_strength, attack_rate, mfcc_0_p75, onset_strength_mean, mfcc_7_p75  
- tenderness: spectral_contrast_1_p25, spectral_contrast_3_p25, mfcc_2_mean, spectral_contrast_1_mean, mfcc_2_p25  
- tension: spectral_contrast_3_p25, mfcc_2_p25, spectral_contrast_1_p25, spectral_contrast_1_mean, mfcc_0_std  

Interpretation highlights:
- Arousal-linked emotions (joy, power, solemnity) emphasize onset strength, attack rate, and bandwidth/energy dynamics.  
- Calm/reflective emotions (calmness, sadness, tenderness, nostalgia) lean more on spectral contrast and MFCC statistics (timbre/brightness).  
- Amazement shows stronger chroma and MFCC variance, suggesting harmonic color plus timbral variability.  

## Artifacts
- `artifacts/features.csv`: aggregated audio feature matrix
- `artifacts/targets.csv`: per-track emotion proportions
- `artifacts/metrics.csv`: full per-emotion and macro metrics
- `artifacts/feature_importance_overall.csv`: permutation importance (overall)
- `artifacts/feature_importance_by_emotion.csv`: permutation importance per emotion

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
