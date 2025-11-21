#!/usr/bin/env python3
"""
Michelin Stars Data Analysis
Investigative journalism approach to uncovering surprising insights
"""

import pandas as pd
import numpy as np
from collections import Counter
import re

# Load datasets
print("Loading datasets...")
df_current = pd.read_csv('michelin_current.csv')
df_1star = pd.read_csv('michelin_1star.csv')
df_2star = pd.read_csv('michelin_2star.csv')
df_3star = pd.read_csv('michelin_3star.csv')

print(f"\n=== DATA OVERVIEW ===")
print(f"Current dataset: {len(df_current):,} restaurants")
print(f"Historical 1-star: {len(df_1star):,} restaurants")
print(f"Historical 2-star: {len(df_2star):,} restaurants")
print(f"Historical 3-star: {len(df_3star):,} restaurants")

print(f"\n=== CURRENT DATA COLUMNS ===")
print(df_current.columns.tolist())
print(f"\n=== HISTORICAL DATA COLUMNS ===")
print(df_1star.columns.tolist())

# Data completeness
print(f"\n=== DATA COMPLETENESS ===")
print("Current dataset missing values:")
print(df_current.isnull().sum())

# Award distribution
print(f"\n=== AWARD DISTRIBUTION ===")
award_dist = df_current['Award'].value_counts()
print(award_dist)

# Price distribution
print(f"\n=== PRICE DISTRIBUTION ===")
price_dist = df_current['Price'].value_counts()
print(price_dist)

# Geographic distribution
print(f"\n=== TOP 20 LOCATIONS ===")
location_dist = df_current['Location'].value_counts().head(20)
print(location_dist)

# Cuisine distribution
print(f"\n=== TOP 20 CUISINES ===")
cuisine_dist = df_current['Cuisine'].value_counts().head(20)
print(cuisine_dist)

# Green Star distribution
print(f"\n=== GREEN STAR DISTRIBUTION ===")
green_star_dist = df_current['GreenStar'].value_counts()
print(green_star_dist)

# Extract country from Location
def extract_country(location):
    if pd.isna(location):
        return None
    # Location format is typically "City, Country"
    parts = location.split(',')
    if len(parts) >= 2:
        return parts[-1].strip()
    return parts[0].strip()

df_current['Country'] = df_current['Location'].apply(extract_country)

print(f"\n=== TOP 20 COUNTRIES ===")
country_dist = df_current['Country'].value_counts().head(20)
print(country_dist)

# Stars by country
print(f"\n=== 3-STAR RESTAURANTS BY COUNTRY ===")
three_stars = df_current[df_current['Award'] == '3 Stars']
print(three_stars['Country'].value_counts())

print(f"\n=== 2-STAR RESTAURANTS BY COUNTRY (TOP 10) ===")
two_stars = df_current[df_current['Award'] == '2 Stars']
print(two_stars['Country'].value_counts().head(10))

# Cross-validation with historical data
print(f"\n=== VERIFICATION: Historical data years ===")
if 'year' in df_1star.columns:
    print(f"1-star year range: {df_1star['year'].min()} - {df_1star['year'].max()}")
if 'year' in df_2star.columns:
    print(f"2-star year range: {df_2star['year'].min()} - {df_2star['year'].max()}")
if 'year' in df_3star.columns:
    print(f"3-star year range: {df_3star['year'].min()} - {df_3star['year'].max()}")

# Save processed data
df_current.to_csv('michelin_processed.csv', index=False)
print(f"\n✓ Saved processed data to michelin_processed.csv")
