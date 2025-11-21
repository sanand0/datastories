#!/usr/bin/env python3
"""
Create beautiful, revelatory visualizations for the Michelin story
"""

import pandas as pd
import json

# Load data
df = pd.read_csv('michelin_processed.csv')

# Clean country names
df['Country'] = df['Country'].replace({
    'United States': 'USA',
    'Hong Kong SAR China': 'Hong Kong',
    'China Mainland': 'China'
})

print("Generating visualization data...")

# ============================================================================
# VIZ 1: Tokyo vs Paris Star Comparison
# ============================================================================

cities = ['Tokyo, Japan', 'Paris, France']
city_comparison = []

for city in cities:
    city_df = df[df['Location'] == city]

    city_comparison.append({
        'city': city.split(',')[0],
        'total': len(city_df),
        'three_stars': len(city_df[city_df['Award'] == '3 Stars']),
        'two_stars': len(city_df[city_df['Award'] == '2 Stars']),
        'one_star': len(city_df[city_df['Award'] == '1 Star']),
        'bib_gourmand': len(city_df[city_df['Award'] == 'Bib Gourmand']),
        'selected': len(city_df[city_df['Award'] == 'Selected Restaurants']),
        'star_points': (
            len(city_df[city_df['Award'] == '3 Stars']) * 3 +
            len(city_df[city_df['Award'] == '2 Stars']) * 2 +
            len(city_df[city_df['Award'] == '1 Star'])
        )
    })

with open('tokyo_vs_paris.json', 'w') as f:
    json.dump(city_comparison, f, indent=2)

print("✓ Generated tokyo_vs_paris.json")

# ============================================================================
# VIZ 3: Star Efficiency by Country
# ============================================================================

country_stats = df.groupby('Country').agg({
    'Award': lambda x: (
        (x == '3 Stars').sum() * 3 +
        (x == '2 Stars').sum() * 2 +
        (x == '1 Star').sum()
    ),
    'Name': 'count'
}).rename(columns={'Award': 'TotalStars', 'Name': 'TotalRestaurants'})

country_stats['StarEfficiency'] = country_stats['TotalStars'] / country_stats['TotalRestaurants']
country_stats = country_stats[country_stats['TotalRestaurants'] >= 50]
country_stats = country_stats.sort_values('StarEfficiency', ascending=False)

efficiency_data = []
for country, row in country_stats.head(15).iterrows():
    efficiency_data.append({
        'country': country,
        'totalStars': int(row['TotalStars']),
        'totalRestaurants': int(row['TotalRestaurants']),
        'efficiency': float(row['StarEfficiency'])
    })

with open('star_efficiency.json', 'w') as f:
    json.dump(efficiency_data, f, indent=2)

print("✓ Generated star_efficiency.json")

# ============================================================================
# VIZ 4: Green Star Analysis
# ============================================================================

green_analysis = {
    'total_green_stars': int((df['GreenStar'] == 1).sum()),
    'total_restaurants': len(df),
    'percentage': float((df['GreenStar'] == 1).sum() / len(df) * 100),
    'by_award': [],
    'by_country': []
}

for award in ['3 Stars', '2 Stars', '1 Star', 'Bib Gourmand', 'Selected Restaurants']:
    total = len(df[df['Award'] == award])
    green = len(df[(df['Award'] == award) & (df['GreenStar'] == 1)])
    green_analysis['by_award'].append({
        'award': award,
        'total': total,
        'green': green,
        'percentage': float(green/total*100) if total > 0 else 0
    })

green_by_country = df[df['GreenStar'] == 1]['Country'].value_counts().head(15)
for country, count in green_by_country.items():
    total_in_country = len(df[df['Country'] == country])
    green_analysis['by_country'].append({
        'country': country,
        'green_count': int(count),
        'total_restaurants': total_in_country,
        'percentage': float(count/total_in_country*100)
    })

with open('green_stars.json', 'w') as f:
    json.dump(green_analysis, f, indent=2)

print("✓ Generated green_stars.json")

# ============================================================================
# VIZ 5: Price Analysis
# ============================================================================

def extract_price_level(price):
    if pd.isna(price) or price == '':
        return None
    euro_count = price.count('€')
    dollar_count = price.count('$')
    if euro_count > 0:
        return euro_count
    elif dollar_count > 0:
        return dollar_count
    return None

df['PriceLevel'] = df['Price'].apply(extract_price_level)

price_analysis = {'by_award': []}
for award in ['3 Stars', '2 Stars', '1 Star', 'Bib Gourmand', 'Selected Restaurants']:
    award_df = df[df['Award'] == award]
    price_data = award_df[award_df['PriceLevel'].notna()]['PriceLevel']
    if len(price_data) > 0:
        price_analysis['by_award'].append({
            'award': award,
            'mean': float(price_data.mean()),
            'median': float(price_data.median()),
            'std': float(price_data.std())
        })

with open('price_analysis.json', 'w') as f:
    json.dump(price_analysis, f, indent=2)

print("✓ Generated price_analysis.json")

# ============================================================================
# VIZ 7: Street Food Analysis
# ============================================================================

street_food = df[df['Cuisine'].str.contains('Street Food', case=False, na=False)]
street_food_locations = street_food['Location'].value_counts().head(10)

street_food_data = {
    'total': len(street_food),
    'by_location': [],
    'by_award': []
}

for location, count in street_food_locations.items():
    street_food_data['by_location'].append({
        'location': location,
        'count': int(count)
    })

for award, count in street_food['Award'].value_counts().items():
    street_food_data['by_award'].append({
        'award': award,
        'count': int(count)
    })

with open('street_food.json', 'w') as f:
    json.dump(street_food_data, f, indent=2)

print("✓ Generated street_food.json")

print("\n" + "=" * 80)
print("✓ ALL VISUALIZATION DATA GENERATED")
print("=" * 80)
print("\nGenerated files for index.html:")
print("  - tokyo_vs_paris.json")
print("  - star_efficiency.json")
print("  - green_stars.json")
print("  - price_analysis.json")
print("  - street_food.json")
