#!/usr/bin/env python3
"""
Investigative Journalism Analysis - Michelin Stars
Hunting for "wait, really?" moments
"""

import pandas as pd
import numpy as np
from collections import Counter
import re
import json

print("=" * 80)
print("MICHELIN STARS: THE INVESTIGATIVE DEEP DIVE")
print("=" * 80)

# Load data
df = pd.read_csv("michelin_processed.csv")

# Clean country names (USA vs United States issue)
df["Country"] = df["Country"].replace(
    {"United States": "USA", "Hong Kong SAR China": "Hong Kong", "China Mainland": "China"}
)

print("\n🔍 INVESTIGATION 1: THE GEOGRAPHY OF EXCELLENCE")
print("=" * 80)

# Stars per capita analysis would be interesting but we don't have population data
# Instead, let's look at concentration and density

# 3-star restaurants by city
three_star = df[df["Award"] == "3 Stars"].copy()
print(f"\nTotal 3-star restaurants: {len(three_star)}")
print("\nCities with 3-star restaurants:")
city_3star = three_star["Location"].value_counts()
print(city_3star)

# Calculate star "efficiency" - ratio of stars to total restaurants
print("\n🔍 INVESTIGATION 2: EFFICIENCY - Where Stars Are Most Concentrated")
print("=" * 80)

country_stars = (
    df.groupby("Country")
    .agg(
        {
            "Award": lambda x: (
                (x == "3 Stars").sum() * 3 + (x == "2 Stars").sum() * 2 + (x == "1 Star").sum()
            ),
            "Name": "count",
        }
    )
    .rename(columns={"Award": "TotalStars", "Name": "TotalRestaurants"})
)

country_stars["StarEfficiency"] = country_stars["TotalStars"] / country_stars["TotalRestaurants"]
country_stars = country_stars[country_stars["TotalRestaurants"] >= 50]  # Min 50 restaurants
country_stars = country_stars.sort_values("StarEfficiency", ascending=False)

print("\nTop 10 countries by Star Efficiency (min 50 restaurants):")
print(country_stars.head(10))

print("\n🔍 INVESTIGATION 3: PRICE ANALYSIS - The Cost of Stars")
print("=" * 80)


# Extract price level (count €/$ symbols)
def extract_price_level(price):
    if pd.isna(price) or price == "":
        return None
    # Count € or $ symbols
    euro_count = price.count("€")
    dollar_count = price.count("$")
    if euro_count > 0:
        return euro_count
    elif dollar_count > 0:
        return dollar_count
    else:
        return None


df["PriceLevel"] = df["Price"].apply(extract_price_level)

price_by_award = (
    df[df["PriceLevel"].notna()].groupby("Award")["PriceLevel"].agg(["mean", "median", "std"])
)
print("\nAverage price level by award:")
print(price_by_award)

# Are there any 1-star restaurants that are cheap?
cheap_stars = df[(df["Award"] == "1 Star") & (df["PriceLevel"] <= 2)]
print(f"\n1-star restaurants with price level ≤ 2: {len(cheap_stars)}")
print("\nSample of affordable 1-star restaurants:")
print(cheap_stars[["Name", "Location", "Cuisine", "Price"]].head(10))

print("\n🔍 INVESTIGATION 4: GREEN STARS - Sustainability Champions")
print("=" * 80)

green_stars = df[df["GreenStar"] == 1]
print(
    f"\nTotal Green Star restaurants: {len(green_stars)} ({len(green_stars) / len(df) * 100:.1f}%)"
)

green_by_country = green_stars["Country"].value_counts().head(10)
print("\nTop 10 countries with Green Stars:")
print(green_by_country)

# Green stars by award level
green_by_award = green_stars["Award"].value_counts()
print("\nGreen Stars by award level:")
print(green_by_award)

# Percentage of each award category that has green star
for award in ["3 Stars", "2 Stars", "1 Star", "Bib Gourmand", "Selected Restaurants"]:
    total = len(df[df["Award"] == award])
    green = len(df[(df["Award"] == award) & (df["GreenStar"] == 1)])
    pct = green / total * 100 if total > 0 else 0
    print(f"{award}: {green}/{total} ({pct:.1f}%)")

print("\n🔍 INVESTIGATION 5: CUISINE DIVERSITY")
print("=" * 80)

# Most common cuisines for 3-star restaurants
three_star_cuisines = three_star["Cuisine"].value_counts()
print("\nCuisines of 3-star restaurants:")
print(three_star_cuisines)

# Countries with most diverse cuisines
cuisine_diversity = df.groupby("Country")["Cuisine"].nunique().sort_values(ascending=False)
cuisine_diversity = cuisine_diversity[df.groupby("Country").size() >= 50]  # Min 50 restaurants
print("\nTop 10 countries by cuisine diversity (min 50 restaurants):")
print(cuisine_diversity.head(10))

print("\n🔍 INVESTIGATION 6: OUTLIERS AND EXTREMES")
print("=" * 80)

# Most expensive restaurants
expensive = df[df["PriceLevel"] == 5].copy()
print(f"\nMost expensive tier (5-symbol) restaurants: {len(expensive)}")
expensive_by_award = expensive["Award"].value_counts()
print("\nExpensive restaurants by award:")
print(expensive_by_award)

# Are there Selected Restaurants (no stars) that are ultra-expensive?
expensive_no_stars = expensive[expensive["Award"] == "Selected Restaurants"]
print(f"\nExpensive (5-tier) restaurants with NO stars: {len(expensive_no_stars)}")
if len(expensive_no_stars) > 0:
    print(expensive_no_stars[["Name", "Location", "Cuisine", "Award"]].head(10))

print("\n🔍 INVESTIGATION 7: TOKYO VS PARIS - The Battle of Culinary Capitals")
print("=" * 80)

tokyo = df[df["Location"] == "Tokyo, Japan"]
paris = df[df["Location"] == "Paris, France"]

print(f"\nTokyo: {len(tokyo)} restaurants")
print(tokyo["Award"].value_counts())

print(f"\nParis: {len(paris)} restaurants")
print(paris["Award"].value_counts())


# Calculate total "star points"
def calc_star_points(award_series):
    return (
        (award_series == "3 Stars").sum() * 3
        + (award_series == "2 Stars").sum() * 2
        + (award_series == "1 Star").sum()
    )


tokyo_points = calc_star_points(tokyo["Award"])
paris_points = calc_star_points(paris["Award"])

print(f"\nTokyo total star points: {tokyo_points}")
print(f"Paris total star points: {paris_points}")
print(f"Winner: {'Tokyo' if tokyo_points > paris_points else 'Paris'}")

print("\n🔍 INVESTIGATION 8: FACILITY PATTERNS")
print("=" * 80)

# Extract facilities
all_facilities = []
for facilities in df[df["FacilitiesAndServices"].notna()]["FacilitiesAndServices"]:
    if isinstance(facilities, str):
        all_facilities.extend([f.strip() for f in facilities.split(",")])

facility_counts = Counter(all_facilities)
print("\nTop 20 facilities/services:")
for facility, count in facility_counts.most_common(20):
    print(f"{facility}: {count}")

# Which facilities correlate with 3-star restaurants?
three_star_facilities = []
for facilities in three_star[three_star["FacilitiesAndServices"].notna()]["FacilitiesAndServices"]:
    if isinstance(facilities, str):
        three_star_facilities.extend([f.strip() for f in facilities.split(",")])

three_star_facility_counts = Counter(three_star_facilities)
print("\nTop facilities in 3-star restaurants:")
for facility, count in three_star_facility_counts.most_common(10):
    pct = count / len(three_star) * 100
    print(f"{facility}: {count}/{len(three_star)} ({pct:.1f}%)")

print("\n🔍 INVESTIGATION 9: ANOMALIES AND SURPRISES")
print("=" * 80)

# Countries with 3-star restaurants but very few total restaurants
country_counts = df["Country"].value_counts()
three_star_by_country = df[df["Award"] == "3 Stars"]["Country"].value_counts()

print("\nCountries with 3-star restaurants and <100 total restaurants (high impact):")
for country in three_star_by_country.index:
    total = country_counts.get(country, 0)
    if total < 100:
        three = three_star_by_country[country]
        print(f"{country}: {three} three-star / {total} total ({three / total * 100:.1f}%)")

print("\n🔍 INVESTIGATION 10: STREET FOOD & BIB GOURMAND")
print("=" * 80)

street_food = df[df["Cuisine"].str.contains("Street Food", case=False, na=False)]
print(f"\nTotal street food restaurants: {len(street_food)}")
print("\nStreet food by location:")
print(street_food["Location"].value_counts().head(10))

print("\nStreet food by award:")
print(street_food["Award"].value_counts())

# Bib Gourmand analysis - good value
bib = df[df["Award"] == "Bib Gourmand"]
print(f"\nBib Gourmand restaurants: {len(bib)}")
print("\nTop 10 locations for Bib Gourmand:")
print(bib["Location"].value_counts().head(10))

print("\n" + "=" * 80)
print("✓ INVESTIGATION COMPLETE")
print("=" * 80)

# Save key findings
findings = {
    "total_restaurants": len(df),
    "three_star_count": len(three_star),
    "tokyo_vs_paris": {
        "tokyo_total": len(tokyo),
        "paris_total": len(paris),
        "tokyo_star_points": int(tokyo_points),
        "paris_star_points": int(paris_points),
    },
    "green_stars": {
        "total": len(green_stars),
        "percentage": float(len(green_stars) / len(df) * 100),
    },
    "top_star_efficiency_countries": country_stars.head(5)["StarEfficiency"].to_dict(),
}

with open("findings.json", "w") as f:
    json.dump(findings, f, indent=2, default=str)

print("\n✓ Saved findings to findings.json")
