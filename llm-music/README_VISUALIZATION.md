# Can AI Hear What We Feel?

An interactive data story exploring how well artificial intelligence can understand music emotions compared to human listeners.

## 📊 The Story

This interactive visualization presents the results of an experiment where Google's Gemini AI analyzed 40 musical excerpts and predicted emotional responses based on the Geneva Emotional Music Scales (GEMS-9). These predictions were then compared against actual human ratings from the Emotify dataset.

The results reveal fascinating insights about both the capabilities and limitations of current AI systems in understanding music emotion.

## 🎵 Features

- **Interactive Audio Player**: Listen to 20+ songs and see real-time comparisons between AI and human emotional ratings
- **Radar Charts**: Visualize the emotional profile of each song across 9 emotions
- **Performance Analytics**: Explore emotion-by-emotion correlation and bias statistics
- **Best/Worst Cases**: See which songs the AI understood well and which it completely misinterpreted
- **Correlation Matrices**: Discover how AI's emotions are more "entangled" than human ratings
- **Malcolm Gladwell-style Narrative**: Data-driven storytelling that makes the insights accessible and engaging

## 📁 Files

- `index.html` - Main interactive story page
- `script.js` - D3.js visualizations and data processing
- `means_comparison.csv` - Mean emotional ratings (AI vs Human)
- `stds_comparison.csv` - Standard deviation comparisons
- `data/` - Contains .opus audio files for all songs
- `music.py` - Original Python script that called Gemini API

## 🚀 Deployment

This page is designed to be deployed via GitHub Pages. Simply:

1. Push the files to your repository
2. Enable GitHub Pages in repository settings
3. The page will be available at `https://[username].github.io/[repo-name]/`

## 🎯 Key Findings

- **Overall correlation**: 0.047 (essentially zero)
- **Mean Absolute Error**: 22.7 percentage points
- **Performance vs baseline**: AI performs 1.23-2.05× worse than predicting the average
- **Systematic biases**: Over-predicts joy/tenderness/power; under-predicts tension
- **Entanglement**: AI emotions are 57% more correlated than human ratings

## 🛠 Technology

- **Frontend**: Pure HTML/CSS with D3.js for visualizations
- **Data Processing**: Python with pandas
- **AI Model**: Google Gemini 3 Pro Preview (via OpenRouter API)
- **Human Data**: Emotify dataset (GEMS-9 emotional framework)

## 📖 Citation

If you use this visualization or analysis, please cite:

```
Music Emotion AI Analysis (2024)
Analysis of Google Gemini's music emotion prediction capabilities
compared to human ratings from the Emotify dataset.
```

## 📝 License

This visualization and analysis are provided for educational and research purposes.

---

_Created with data-driven journalism principles inspired by The New York Times graphics team_
