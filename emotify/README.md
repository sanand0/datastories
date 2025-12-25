# The Ambiguous Song

An interactive data story exploring how humans label emotions in music, featuring analysis of 400 tracks across 4 genres rated by multiple annotators.

**Live Demo**: Open `index.html` in a web browser (works offline!)

## What's Inside

This folder contains everything needed to run the visualization:

### Core Files

- `index.html` - Main story page with dark vinyl/concert aesthetic
- `script.js` - Interactive visualizations using Chart.js

### Data Files

- `data/story.json` (266KB) - Processed dataset with tracks, examples, metrics
- `data/config.json` (941B) - Color schemes and labels
- `data/data.csv.gz` (51KB) - Raw rating data (compressed from 394KB)

### Audio Examples (10 tracks)

- `data/audio/*.opus` - Embedded one-minute clips demonstrating:
  - Unanimous consensus (joy, power)
  - Near-consensus (calmness, tension, tenderness)
  - Bittersweet mixes (nostalgia + sadness)
  - High disagreement (ambiguous tracks)
  - All 9 GEMS emotions represented

### Model Metrics

- `artifacts/metrics.csv` (66KB) - Model performance data

**Total Size**: 1.4MB (16 files)

## Features

### Design

- Dark theme inspired by vinyl records and concert halls
- Unique typography: Playfair Display, Crimson Text, Space Mono
- Animated waveforms and rotating vinyl grooves
- Scroll-triggered fade-in animations
- Neon cyan/magenta accents on dark background

### Intuitive Explanations

Technical features explained with real-world analogies:

- **Spectral Contrast**: City skyline (building heights)
- **MFCCs**: Sonic color/fingerprint
- **Onset/Attack**: How suddenly sound hits you

### Interactive Visualizations

7 Chart.js visualizations revealing:

1. Emotion selection distributions
2. Emotion bias across the dataset
3. Consensus vs ambiguity scatter plot
4. Genre-emotion correlations
5. Top predictive audio features
6. Emotion-specific feature importance
7. Model performance comparison (stratified vs cross-genre)

## Technical Details

**Framework**: Vanilla JavaScript + Chart.js 4.4.0
**Audio Format**: Opus (1-minute clips)
**Data Format**: JSON + CSV
**Deployment**: Static site (GitHub Pages ready)

## Data Sources

- **Audio**: 400 one-minute clips (classical, rock, pop, electronic)
- **Annotations**: Multi-label ratings using Geneva Emotional Music Scale (GEMS)
- **Features**: 82 audio features extracted with librosa
- **Models**: Random Forest, XGBoost, Ridge, MLP

## Links

- **Repository**: https://github.com/sanand0/datastories/tree/main/emotify
- **GEMS Scale**: [Zentner et al. 2008](https://doi.org/10.1037/0022-3514.94.3.494)

## License

Data and code available in the parent repository.
