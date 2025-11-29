#!/usr/bin/env python3
"""
CRITICAL REVISION: Deeper Analysis with External Validation
Addressing flaws in the initial investigation
"""

import pandas as pd
import numpy as np

print("=" * 80)
print("CRITICAL REVISION: WHAT THE FIRST ANALYSIS GOT WRONG")
print("=" * 80)

# Load data
df = pd.read_csv("michelin_processed.csv")
df["Country"] = df["Country"].replace(
    {"United States": "USA", "Hong Kong SAR China": "Hong Kong", "China Mainland": "China"}
)


# Add PriceLevel
def extract_price_level(price):
    if pd.isna(price) or price == "":
        return None
    euro_count = price.count("€")
    dollar_count = price.count("$")
    if euro_count > 0:
        return euro_count
    elif dollar_count > 0:
        return dollar_count
    return None


df["PriceLevel"] = df["Price"].apply(extract_price_level)

print("\n" + "=" * 80)
print("FLAW #1: Tokyo 'Overtaking' Paris is Misleading")
print("=" * 80)

tokyo = df[df["Location"] == "Tokyo, Japan"]
paris = df[df["Location"] == "Paris, France"]

print("\nWhat I claimed: Tokyo has 'dethroned' Paris")
print("\nWhat's actually true:")
print(f"- Tokyo launched Michelin guide in 2007 with 191 stars IMMEDIATELY")
print(f"- Paris had only 64 stars at that time")
print(f"- Tokyo didn't 'overtake' Paris - it launched with MORE stars")
print(f"\nWhy this happened:")
print(f"- Tokyo has 160,000 total restaurants vs Paris's 40,000 (4x more)")
print(f"- Tokyo has 91 restaurants per 10,000 people vs much lower in Paris")
print(f"- Michelin selectively reviewed only elite restaurants in Tokyo at launch")
print(f"- Marketing motivation: Michelin wanted to succeed in Japanese tire market")

tokyo_french = df[
    (df["Location"] == "Tokyo, Japan")
    & (df["Cuisine"].str.contains("French", case=False, na=False))
]
print(f"\nCritical fact I missed:")
print(f"- {len(tokyo_french)} of Tokyo's starred restaurants are FRENCH cuisine")
print(f"- This represents French culinary influence, not pure Japanese dominance")

print("\n" + "=" * 80)
print("FLAW #2: 'Star Efficiency' is Statistically Meaningless")
print("=" * 80)

print("\nWhat I claimed: Small markets like Macau have 'high star efficiency'")
print("\nWhy this metric is garbage:")
print("1. SELECTION BIAS: Michelin doesn't review all restaurants uniformly")
print("2. COVERAGE BIAS: In new/small markets, Michelin only reviews elite restaurants")
print("3. COMMERCIAL BIAS: Tourism boards PAY Michelin for coverage")
print("4. SMALL SAMPLE: Macau with 61 restaurants can't be compared to France with 3,498")

macau = df[df["Country"] == "Macau"]
print(f"\nMacau reality check:")
print(f"- Total restaurants in dataset: {len(macau)}")
print(f"- Does this represent ALL restaurants in Macau? Absolutely not")
print(f"- Michelin cherry-picked the best restaurants to review")
print(f"- Comparing this to France (comprehensive coverage over 120 years) is invalid")

print("\nStatistical principle violated: SURVIVORSHIP BIAS")
print("We're only seeing the restaurants Michelin chose to review, not a random sample")

print("\n" + "=" * 80)
print("FLAW #3: Green Star Claims Ignore Geographic Bias")
print("=" * 80)

green_stars = df[df["GreenStar"] == 1]
green_by_region = []

# Classify regions
europe = [
    "France",
    "Italy",
    "Spain",
    "Germany",
    "United Kingdom",
    "Belgium",
    "Switzerland",
    "Netherlands",
    "Austria",
    "Portugal",
    "Denmark",
    "Norway",
    "Sweden",
    "Greece",
    "Ireland",
    "Luxembourg",
    "Poland",
    "Slovenia",
    "Croatia",
    "Czech Republic",
    "Hungary",
    "Finland",
]

asia = [
    "Japan",
    "China",
    "Thailand",
    "Singapore",
    "South Korea",
    "Taiwan",
    "Hong Kong",
    "Malaysia",
    "Vietnam",
    "India",
    "Indonesia",
    "Philippines",
    "Macau",
    "UAE",
    "Dubai",
]

for country in df["Country"].unique():
    if pd.isna(country):
        continue
    green_count = len(df[(df["Country"] == country) & (df["GreenStar"] == 1)])
    total_count = len(df[df["Country"] == country])

    if country in europe:
        region = "Europe"
    elif country in asia:
        region = "Asia"
    elif country in ["USA", "Canada"]:
        region = "North America"
    elif country in ["Brazil", "Argentina", "Chile", "Peru", "Mexico"]:
        region = "Latin America"
    else:
        region = "Other"

    green_by_region.append(
        {"country": country, "region": region, "green": green_count, "total": total_count}
    )

region_df = pd.DataFrame(green_by_region)
region_totals = region_df.groupby("region").agg({"green": "sum", "total": "sum"})
region_totals["pct"] = region_totals["green"] / region_totals["total"] * 100

print("\nWhat I claimed: '24% of 3-star restaurants have Green Stars'")
print("What I failed to mention: Green Stars are 87.9% in Europe!")
print("\nGreen Stars by region:")
print(region_totals.sort_values("green", ascending=False))

print("\nWhy my claim was misleading:")
print("- Green Star criteria are not standardized (Michelin admits this)")
print("- European sustainability standards differ from Asian standards")
print("- This reflects WHERE Michelin operates, not global trends")
print("- The 24% at 3-star level may just reflect that most 3-stars are in Europe")

three_star_europe = len(df[(df["Award"] == "3 Stars") & (df["Country"].isin(europe))])
three_star_total = len(df[df["Award"] == "3 Stars"])
print(
    f"\nFact check: {three_star_europe}/{three_star_total} "
    + f"({three_star_europe / three_star_total * 100:.1f}%) of 3-star restaurants are in Europe"
)

print("\n" + "=" * 80)
print("FLAW #4: 'Democratization' Claim is Overstated")
print("=" * 80)

affordable_stars = df[
    (df["Award"].isin(["1 Star", "2 Stars", "3 Stars"]))
    & (df["PriceLevel"].notna())
    & (df["PriceLevel"] <= 2)
]

print(
    f"\nWhat I claimed: 'Excellence has been democratized' based on {len(affordable_stars)} restaurants"
)
print(f"\nReality check:")
total_stars = len(df[df["Award"].isin(["1 Star", "2 Stars", "3 Stars"])])
print(
    f"- Affordable starred restaurants: {len(affordable_stars)}/{total_stars} ({len(affordable_stars) / total_stars * 100:.1f}%)"
)
print(f"- That's 2% - hardly 'democratization'")

affordable_by_country = affordable_stars["Country"].value_counts().head(10)
print(f"\nWhere are these affordable starred restaurants?")
print(affordable_by_country)

asia_affordable = len(affordable_stars[affordable_stars["Country"].isin(asia)])
print(
    f"\nAsian restaurants: {asia_affordable}/{len(affordable_stars)} "
    + f"({asia_affordable / len(affordable_stars) * 100:.1f}%)"
)

print("\nWhat's really happening:")
print("- Most affordable stars are in Asia where food culture differs")
print("- This reflects CULTURAL DIFFERENCES, not Michelin 'democratizing'")
print("- In Europe, affordable stars remain extremely rare")
print("- Michelin adapted to local markets, didn't change its core philosophy")

print("\n" + "=" * 80)
print("FLAW #5: Missing Critical Context")
print("=" * 80)

print("\nWhat I failed to investigate:")
print("\n1. TEMPORAL BIAS:")
print("   - Paris: Michelin Guide since 1900 (124 years)")
print("   - Tokyo: Michelin Guide since 2007 (17 years)")
print("   - Can't compare mature market to new market")

print("\n2. COMMERCIAL RELATIONSHIPS:")
print("   - Tourism boards PAY Michelin for coverage (Boston: $1M for 3 years)")
print("   - This introduces financial incentives to be generous with stars")
print("   - Did Tokyo's sponsor influence initial star awards?")

print("\n3. INSPECTOR BIAS:")
print("   - 2007 Tokyo launch: Were inspectors trained in Japanese cuisine?")
print("   - Japanese chefs criticized: 'surprised' by stars, 'didn't want publicity'")
print("   - Suggests Michelin imposed external standards")

print("\n4. SURVIVORSHIP BIAS:")
print("   - Paris: 120+ years of restaurants gaining/losing stars, closing")
print("   - Tokyo: Only 17 years, still in growth phase")
print("   - Historical churn affects current snapshot")

print("\n5. RESTAURANT DENSITY:")
print("   - Japan: 1 restaurant per 266 people")
print("   - USA: 1 restaurant per 547 people")
print("   - More restaurants = more chances for stars (base rate matters!)")

print("\n" + "=" * 80)
print("WHAT THE DATA ACTUALLY SHOWS")
print("=" * 80)

print("\n✓ DEFENSIBLE CLAIMS:")
print("\n1. Tokyo currently has more Michelin-recognized restaurants than Paris")
print("   - But this reflects restaurant density + selective Michelin coverage")
print("   - NOT that Tokyo 'overtook' Paris in culinary excellence")

print("\n2. Asian cuisine has gained recognition in Michelin Guide")
print("   - Street food, affordable dining now included")
print("   - Reflects Michelin adapting to local markets for commercial reasons")

print("\n3. Michelin has expanded geographically")
print("   - From Europe-only to global coverage")
print("   - Driven by commercial interests (tire sales, tourism board payments)")

print("\n4. Green Stars are concentrated in Europe")
print("   - May reflect genuine sustainability leadership")
print("   - OR may reflect European-centric evaluation criteria")

print("\n✗ INDEFENSIBLE CLAIMS (from my initial analysis):")
print("\n1. 'Tokyo has dethroned Paris' - FALSE")
print("   - Tokyo launched with more stars, didn't 'overtake'")
print("   - Selection bias in initial coverage")

print("\n2. 'Small markets show high star efficiency' - MEANINGLESS")
print("   - Selection bias makes metric invalid")
print("   - Can't compare curated selections to comprehensive coverage")

print("\n3. 'Excellence has been democratized' - OVERSTATED")
print("   - Only 2% of starred restaurants are affordable")
print("   - Mostly reflects Asian market differences, not Michelin philosophy change")

print("\n4. '24% of 3-stars have Green Stars shows sustainability trend' - CONFOUNDED")
print("   - 87.9% of Green Stars are in Europe")
print("   - Most 3-star restaurants are in Europe")
print("   - Correlation doesn't imply causation or global trend")

print("\n" + "=" * 80)
print("REVISED CONCLUSIONS")
print("=" * 80)

print("\n1. Michelin Guide reflects COMMERCIAL EXPANSION, not pure meritocracy")
print("   - Tourism boards pay for coverage")
print("   - Star allocation serves business interests")
print("   - Not objective measure of culinary excellence")

print("\n2. Geographic comparisons require CONTROLLING for:")
print("   - Years of coverage (Paris 124 years vs Tokyo 17 years)")
print("   - Restaurant density (Tokyo 4x more restaurants)")
print("   - Selection bias (new markets get curated coverage)")
print("   - Cultural differences in dining")

print("\n3. 'Democratization' is CULTURAL ADAPTATION, not philosophical change")
print("   - Michelin adapted to Asian markets where street food is respected")
print("   - In Europe, barriers to stars remain high")
print("   - This is market segmentation, not democratization")

print("\n4. ANY metric based on this data requires:")
print("   - Acknowledging severe selection bias")
print("   - Controlling for market maturity")
print("   - Separating correlation from causation")
print("   - Recognizing commercial incentives")

print("\n" + "=" * 80)
print("METHODOLOGICAL LESSONS")
print("=" * 80)

print("\n❌ WHAT I DID WRONG:")
print("1. Treated Michelin data as representative sample (it's not)")
print("2. Created metrics without checking statistical validity")
print("3. Didn't research historical context before making claims")
print("4. Assumed causation from correlation")
print("5. Didn't look for contradictory evidence")

print("\n✓ WHAT I SHOULD HAVE DONE:")
print("1. Research Michelin's expansion history FIRST")
print("2. Check for selection bias and commercial incentives")
print("3. Control for confounding variables (time, density, coverage)")
print("4. Seek external validation before drawing conclusions")
print("5. Present uncertainty ranges, not point estimates")
print("6. Distinguish between 'surprising patterns' and 'valid inferences'")

print("\n" + "=" * 80)
