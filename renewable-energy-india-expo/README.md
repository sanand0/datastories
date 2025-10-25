# India's Renewable Energy Revolution - Data Visualization

A beautiful New York Times-style narrative data visualization of the Renewable Energy India Expo 2025, featuring 519 exhibitors.

## 🎨 Live Visualization

Open `index.html` in your browser to view the interactive data story with:

- **6 interactive Chart.js visualizations**
- **Scrollytelling narrative** with insights woven throughout
- **NYT-inspired design** with Playfair Display & Source Serif typography
- **Responsive layout** that works on all devices

### Quick Start

```bash
# Start local server
python3 -m http.server 8765

# Open in browser
open http://localhost:8765
```

Or simply open `index.html` directly in your browser.

## 📊 Visualizations Included

1. **India vs International** - Doughnut chart showing 85% domestic dominance
2. **Sector Distribution** - Solar's 64% market domination
3. **Manufacturing Categories** - What companies actually produce
4. **International Players** - China's 44 exhibitors vs Germany's 16
5. **Technology Trends** - From solar (433) to IoT (13)
6. **Company Scale** - Manufacturers (178) vs Startups (31)

Plus custom-styled **value chain visualization** showing the complete ecosystem from upstream to O&M.

## 📁 Project Structure

```
├── index.html           # Main visualization page
├── script.js            # Chart.js visualization code
├── analyze_exhibitors.py # Python analysis script
├── insights.json        # Comprehensive insights data
├── insights.md          # Written narrative
├── exhibitors.csv       # Raw exhibitor data
├── sectors.csv          # Sector breakdown
├── countries.csv        # Geographic distribution
└── technologies.csv     # Technology mentions
```

## 🔧 Technologies Used

- **Chart.js 4.4.0** - Interactive charts
- **Bootstrap 5.3** - Responsive grid & utilities
- **Google Fonts** - Playfair Display (headlines) + Source Serif 4 (body)
- **ES Modules** - Modern JavaScript
- **Vanilla JS** - No framework overhead

## 📈 Key Insights Visualized

- **85% domestic players** - India's manufacturing ecosystem
- **Complete value chain** - 65 upstream → 250 manufacturers → 126 installers
- **Solar domination** - 917 mentions (64% of all activity)
- **China factor** - 44 companies (pragmatic collaboration)
- **Manufacturing focus** - 250 manufacturers vs 126 service providers
- **Technology gaps** - EV charging (17), IoT (13) underrepresented

## 🎯 Design Principles

Following NYT data journalism best practices:

- **Story first** - Data supports narrative, not vice versa
- **Progressive disclosure** - Insights revealed as you scroll
- **Visual hierarchy** - Typography-driven layout
- **Minimal chrome** - Let data and story shine
- **Accessible colors** - High contrast, colorblind-friendly
- **Print-inspired** - Elegant serif fonts, generous whitespace

## 📝 Data Sources

Analysis based on 519 exhibitors at Renewable Energy India Expo 2025. Data extracted from:

- Company descriptions
- Product categories
- Geographic information
- Technology keywords (NLP)

## 🚀 Running Analysis

To regenerate insights from raw data:

```bash
uv run --script analyze_exhibitors.py
```

This will update:

- `insights.json`
- `sectors.csv`
- `countries.csv`
- `technologies.csv`

## 📄 License

Data storytelling project - feel free to adapt and reuse.
