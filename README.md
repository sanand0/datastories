# Data Stories

Interactive visualizations and data narratives.

Website: [sanand0.github.io/datastories/](https://sanand0.github.io/datastories/)

## Stories

- [Google Searches](google-searches/). Categorized every Google Search since Jan 2021 into 50 topics. It's mostly tech, AI, and geo-cultural. I also need to allocate more time to testing, databases, and other 'spiky' topics.
- [ChatGPT vs Google Usage](chatgpt-vs-google/). How my ChatGPT usage has grown at the expense of Google usage. Google is only 60% of my usage, and far lower in engagement
- [Vipassana](vipassana-chatgpt/). A manually LLM-generated comic story of my meditation experience (via ChatGPT)
- [Vipassana](vipassana/). A programmatically LLM-generated comic story of my meditation experience via [Gemini](https://developers.googleblog.com/en/generate-images-gemini-2-0-flash-preview/)
- [ChatGPT Topics](chatgpt-topics/). Categorized the 6,000 ChatGPT conversations I've had in the last 2 years to understand what topics I discuss the most. It's mostly tech, AI, reading/writing, and some daily-life stuff.
- [Indian High Courts Analysis](indian-high-courts/). Comprehensive analysis of 16M judgments from 25 Indian High Courts. Reveals court efficiency disparities, seasonal justice patterns, and systematic UAPA bail delays across states.
- [Horoscope Contradictions](horoscope-2025-06-16/). Use Deep Research to read horoscopes (Sagittarius, 16 June 2025) and list contradictions from various Indian media sources.
- [Employment Trends](employment-trends/). Explored US employment growth since 1980. Some like Scenic Transportation grew over 2X. Others like Rail & Central Banks shrank to 40-80% of original size.
- [Weight Journey 2025](weight-2025-06/). Lost 22 kg in 22 weeks through intermittent fasting. Skipped lunch, no snacks, no extra exercise.

## License

[MIT](LICENSE)

<!--

File structure:

- README.md: Manually updated with story links
- config.json: Manually updated with story links
- index.html: Renders config.json as cards
- setup.sh: Run via .github/workflows/deploy.yml to generate [story-folder]/index.html from [story-folder]/README.md
- [story-folder]/
  - README.md
  - Other supporting files

When adding a new story, update:

- config.json
- README.md
- setup.sh

Assets are stored in a GitHub Release creatd via:

```bash
gh release create main --title "Assets" --notes "Data story assets"
```

Add assets by running:

```bash
gh release upload main --clobber $FILE
```

Linting: `npm run lint`

-->
