#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["pandas>=2.0", "orjson"]
# ///
"""Extract insights from Renewable Energy India Expo exhibitor data."""

import re
from collections import Counter, defaultdict
from pathlib import Path
import pandas as pd
import orjson


def load_data(path: str) -> pd.DataFrame:
    """Load and clean exhibitor data."""
    df = pd.read_csv(path)
    df = df.fillna("")
    df["country"] = df["info_2"].apply(lambda x: x if x and not x.startswith("http") else "")
    df["description_length"] = df["description"].str.len()
    return df


def extract_categories(df: pd.DataFrame) -> dict:
    """Extract and analyze product categories."""
    all_categories = []
    category_by_company = {}

    for idx, row in df.iterrows():
        cats = [c.strip() for c in row["product_categories_"].split(",") if c.strip()]
        all_categories.extend(cats)
        category_by_company[row["company_name"]] = cats

    # Parse hierarchical categories
    main_sectors = Counter()
    sub_categories = Counter()
    sector_subcategory = defaultdict(Counter)

    for cat in all_categories:
        if ">" in cat:
            parts = cat.split(">", 1)
            sector = parts[0].strip()
            subcat = parts[1].strip() if len(parts) > 1 else ""
            main_sectors[sector] += 1
            if subcat:
                sub_categories[subcat] += 1
                sector_subcategory[sector][subcat] += 1
        else:
            main_sectors[cat] += 1

    return {
        "main_sectors": dict(main_sectors.most_common()),
        "sub_categories": dict(sub_categories.most_common(20)),
        "sector_breakdown": {k: dict(v.most_common(10)) for k, v in sector_subcategory.items()},
        "category_by_company": category_by_company,
    }


def analyze_countries(df: pd.DataFrame) -> dict:
    """Analyze geographic distribution."""
    countries = df[df["country"] != ""]["country"].value_counts()

    # Calculate India vs International split
    india_count = countries.get("India", 0)
    international_count = countries.sum() - india_count

    return {
        "country_distribution": countries.to_dict(),
        "india_vs_international": {
            "India": int(india_count),
            "International": int(international_count),
        },
        "top_international": countries[countries.index != "India"].head(10).to_dict(),
    }


def extract_technologies(df: pd.DataFrame) -> dict:
    """Extract technology keywords from descriptions."""
    tech_keywords = {
        "AI/ML": r"\b(artificial intelligence|machine learning|AI|ML|neural|deep learning)\b",
        "IoT": r"\b(IoT|Internet of Things|smart sensors|connected devices)\b",
        "Blockchain": r"\b(blockchain|distributed ledger|smart contract)\b",
        "Storage/Battery": r"\b(battery|storage|BESS|lithium|energy storage)\b",
        "Green Hydrogen": r"\b(hydrogen|H2|electrolysis|fuel cell)\b",
        "Solar": r"\b(solar|photovoltaic|PV|panel|module)\b",
        "Wind": r"\b(wind turbine|wind energy|wind power)\b",
        "Smart Grid": r"\b(smart grid|grid management|microgrid|SCADA)\b",
        "EV Charging": r"\b(EV|electric vehicle|charging station|charger)\b",
        "Inverter": r"\b(inverter|converter|power electronics)\b",
        "Monitoring": r"\b(monitoring|analytics|optimization|predictive)\b",
        "Efficiency": r"\b(efficiency|optimization|performance)\b",
    }

    tech_mentions = Counter()
    companies_by_tech = defaultdict(list)

    for idx, row in df.iterrows():
        text = (row["description"] + " " + row["product_categories_"]).lower()
        for tech, pattern in tech_keywords.items():
            if re.search(pattern, text, re.IGNORECASE):
                tech_mentions[tech] += 1
                companies_by_tech[tech].append(row["company_name"])

    return {
        "technology_distribution": dict(tech_mentions.most_common()),
        "companies_by_technology": {k: v[:5] for k, v in companies_by_tech.items()},
    }


def analyze_company_scale(df: pd.DataFrame) -> dict:
    """Infer company scale from descriptions."""
    scale_indicators = {
        "Large": r"\b(GW|gigawatt|billion|global|worldwide|multinational|fortune|leader|largest)\b",
        "Established": r"\b(decades|established|since \d{4}|years of experience|\d{2}\+ years)\b",
        "Startup": r"\b(startup|founded 20[2-9]\d|emerging|young|new)\b",
        "Manufacturer": r"\b(manufactur|factory|plant|production|assembl)\b",
        "Service Provider": r"\b(service|consultant|solution provider|EPC|O&M)\b",
    }

    company_scales = defaultdict(list)

    for idx, row in df.iterrows():
        text = row["description"].lower()
        for scale, pattern in scale_indicators.items():
            if re.search(pattern, text, re.IGNORECASE):
                company_scales[scale].append(row["company_name"])

    return {k: len(v) for k, v in company_scales.items()}


def find_unique_players(df: pd.DataFrame) -> dict:
    """Identify companies with unique offerings."""
    unique_finds = []

    # Find companies with rare category combinations
    category_freq = defaultdict(int)
    for cats in df["product_categories_"].str.split(","):
        for cat in cats:
            category_freq[cat.strip()] += 1

    for idx, row in df.iterrows():
        cats = [c.strip() for c in row["product_categories_"].split(",")]
        rare_cats = [c for c in cats if category_freq.get(c, 0) < 5 and c]

        if rare_cats or "other," in row["product_categories_"]:
            unique_finds.append(
                {
                    "company": row["company_name"],
                    "country": row["country"],
                    "rare_categories": rare_cats,
                    "description_snippet": row["description"][:200],
                }
            )

    return unique_finds[:15]


def analyze_value_chain(categories_data: dict) -> dict:
    """Map companies across the value chain."""
    value_chain_keywords = {
        "Upstream (Raw Materials)": [
            "Silicon feedstock",
            "raw materials",
            "polysilicon",
            "ingot",
            "wafer",
        ],
        "Midstream (Manufacturing)": [
            "manufactur",
            "Solar cells",
            "PV modules",
            "production",
            "assembly",
        ],
        "Downstream (Installation)": ["EPC", "turnkey", "installation", "project developers"],
        "Operation & Maintenance": ["O&M", "maintenance", "monitoring", "SCADA"],
        "Components & Parts": ["inverter", "battery", "cable", "connector", "mounting"],
    }

    value_chain = defaultdict(list)

    for company, cats in categories_data["category_by_company"].items():
        cat_text = " ".join(cats).lower()
        for stage, keywords in value_chain_keywords.items():
            if any(kw.lower() in cat_text for kw in keywords):
                value_chain[stage].append(company)

    return {k: len(set(v)) for k, v in value_chain.items()}


def main():
    """Run all analyses and save results."""
    df = load_data("exhibitors.csv")

    print(f"📊 Analyzing {len(df)} exhibitors...")

    # Run analyses
    categories = extract_categories(df)
    countries = analyze_countries(df)
    technologies = extract_technologies(df)
    scale = analyze_company_scale(df)
    unique = find_unique_players(df)
    value_chain = analyze_value_chain(categories)

    # Compile insights
    insights = {
        "summary": {
            "total_exhibitors": len(df),
            "countries_represented": len([c for c in df["country"].unique() if c]),
            "total_categories": len(categories["main_sectors"]),
        },
        "geographic_distribution": countries,
        "sector_analysis": {
            "main_sectors": categories["main_sectors"],
            "top_subcategories": categories["sub_categories"],
            "sector_breakdown": categories["sector_breakdown"],
        },
        "technology_trends": technologies,
        "company_profiles": scale,
        "value_chain_coverage": value_chain,
        "unique_players": unique,
    }

    # Save as JSON
    with open("insights.json", "wb") as f:
        f.write(orjson.dumps(insights, option=orjson.OPT_INDENT_2))

    # Create CSV exports for easy analysis
    pd.DataFrame([{"Sector": k, "Count": v} for k, v in categories["main_sectors"].items()]).to_csv(
        "sectors.csv", index=False
    )

    pd.DataFrame(
        [{"Country": k, "Count": v} for k, v in countries["country_distribution"].items()]
    ).to_csv("countries.csv", index=False)

    pd.DataFrame(
        [
            {"Technology": k, "Mentions": v}
            for k, v in technologies["technology_distribution"].items()
        ]
    ).to_csv("technologies.csv", index=False)

    print("✅ Analysis complete!")
    print(f"   - insights.json: Comprehensive insights")
    print(f"   - sectors.csv: Sector breakdown")
    print(f"   - countries.csv: Geographic distribution")
    print(f"   - technologies.csv: Technology trends")


if __name__ == "__main__":
    main()
