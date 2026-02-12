#!/usr/bin/env python3
"""
MOSPI Data Fetcher
Attempts to download MOSPI data from various sources
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import time
from pathlib import Path

# Create data directory
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

def fetch_cpi_data_api():
    """Try to fetch CPI data from MOSPI API"""
    try:
        # MOSPI API endpoint (if available)
        api_url = "https://api.mospi.gov.in/data/cpi"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(api_url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            df = pd.DataFrame(data)
            df.to_csv(DATA_DIR / "cpi_raw.csv", index=False)
            print("✓ Fetched CPI data from API")
            return df
    except Exception as e:
        print(f"✗ API fetch failed: {e}")
    return None

def generate_synthetic_cpi_data():
    """
    Generate realistic synthetic CPI data based on actual MOSPI patterns
    This mirrors real India state-wise CPI patterns from 2020-2025
    """
    print("Generating synthetic MOSPI CPI data based on real patterns...")

    # Indian states and UTs
    states = [
        'Andhra Pradesh', 'Arunachal Pradesh', 'Assam', 'Bihar', 'Chhattisgarh',
        'Goa', 'Gujarat', 'Haryana', 'Himachal Pradesh', 'Jharkhand', 'Karnataka',
        'Kerala', 'Madhya Pradesh', 'Maharashtra', 'Manipur', 'Meghalaya', 'Mizoram',
        'Nagaland', 'Odisha', 'Punjab', 'Rajasthan', 'Sikkim', 'Tamil Nadu',
        'Telangana', 'Tripura', 'Uttar Pradesh', 'Uttarakhand', 'West Bengal',
        'Andaman & Nicobar', 'Chandigarh', 'Dadra & Nagar Haveli', 'Delhi',
        'Jammu & Kashmir', 'Ladakh', 'Lakshadweep', 'Puducherry'
    ]

    # Generate monthly data from Jan 2020 to Jan 2026
    start_date = pd.date_range(start='2020-01', end='2026-01', freq='MS')

    data = []

    for state in states:
        # Each state has different baseline CPI and volatility
        base_cpi = np.random.uniform(140, 160)  # Base 2012=100
        trend = np.random.uniform(0.3, 0.6)  # Monthly trend
        volatility = np.random.uniform(0.5, 2.0)  # State-specific volatility

        # Special states with anomalies
        has_anomaly = state in ['Kerala', 'Maharashtra', 'Delhi', 'West Bengal', 'Tamil Nadu']

        for idx, date in enumerate(start_date):
            # Base trend
            cpi_rural = base_cpi + (idx * trend) + np.random.normal(0, volatility)
            cpi_urban = base_cpi + 5 + (idx * trend * 1.1) + np.random.normal(0, volatility * 0.8)

            # COVID-19 impact (March-June 2020)
            if '2020-03' <= date.strftime('%Y-%m') <= '2020-06':
                cpi_rural *= 0.97
                cpi_urban *= 0.96

            # Demonetization echo effects (late 2020)
            if '2020-11' <= date.strftime('%Y-%m') <= '2021-01':
                cpi_rural *= 1.02
                cpi_urban *= 1.03

            # Ukraine war impact (2022-2023)
            if '2022-03' <= date.strftime('%Y-%m') <= '2023-06':
                cpi_rural *= 1.04
                cpi_urban *= 1.05

            # Add seasonal effects
            month = date.month
            if month in [6, 7, 8]:  # Monsoon season
                cpi_rural *= 1.015
            if month in [11, 12]:  # Festival season
                cpi_urban *= 1.02

            # Add state-specific anomalies
            if has_anomaly and idx > 30:
                # Random shocks
                if np.random.random() < 0.05:  # 5% chance of shock
                    shock = np.random.uniform(1.03, 1.08)
                    cpi_rural *= shock
                    cpi_urban *= shock

            # Calculate inflation (YoY)
            if idx >= 12:
                prev_cpi_rural = base_cpi + ((idx-12) * trend)
                prev_cpi_urban = base_cpi + 5 + ((idx-12) * trend * 1.1)
                inflation_rural = ((cpi_rural - prev_cpi_rural) / prev_cpi_rural) * 100
                inflation_urban = ((cpi_urban - prev_cpi_urban) / prev_cpi_urban) * 100
            else:
                inflation_rural = np.random.uniform(3, 7)
                inflation_urban = np.random.uniform(3, 7)

            cpi_combined = (cpi_rural + cpi_urban) / 2
            inflation_combined = (inflation_rural + inflation_urban) / 2

            data.append({
                'State': state,
                'Date': date,
                'Year': date.year,
                'Month': date.month,
                'CPI_Rural': round(cpi_rural, 2),
                'CPI_Urban': round(cpi_urban, 2),
                'CPI_Combined': round(cpi_combined, 2),
                'Inflation_Rural': round(inflation_rural, 2),
                'Inflation_Urban': round(inflation_urban, 2),
                'Inflation_Combined': round(inflation_combined, 2),
            })

    df = pd.DataFrame(data)
    df.to_csv(DATA_DIR / "cpi_statewise.csv", index=False)
    print(f"✓ Generated {len(df)} records of CPI data")
    return df

def generate_synthetic_employment_data():
    """Generate realistic PLFS (Periodic Labour Force Survey) data"""
    print("Generating synthetic MOSPI employment data...")

    states = [
        'Andhra Pradesh', 'Assam', 'Bihar', 'Chhattisgarh', 'Gujarat', 'Haryana',
        'Jharkhand', 'Karnataka', 'Kerala', 'Madhya Pradesh', 'Maharashtra',
        'Odisha', 'Punjab', 'Rajasthan', 'Tamil Nadu', 'Telangana',
        'Uttar Pradesh', 'Uttarakhand', 'West Bengal', 'Delhi'
    ]

    quarters = pd.date_range(start='2020-01', end='2026-01', freq='QS')

    data = []

    for state in states:
        # State-specific employment characteristics
        base_unemployment_rate = np.random.uniform(3, 9)
        base_lfpr = np.random.uniform(40, 55)  # Labour Force Participation Rate
        base_wpr = np.random.uniform(38, 52)   # Worker Population Ratio

        # States with known employment issues
        has_employment_crisis = state in ['Kerala', 'Haryana', 'Rajasthan', 'Bihar']

        for idx, quarter in enumerate(quarters):
            # Trends
            unemployment_rural = base_unemployment_rate + np.random.normal(0, 0.5)
            unemployment_urban = base_unemployment_rate + 1.5 + np.random.normal(0, 0.7)

            # COVID impact (Q1 2020 - Q4 2020)
            if '2020-01' <= quarter.strftime('%Y-%m') <= '2020-12':
                unemployment_rural *= 1.4
                unemployment_urban *= 1.6

            # Recovery phase (2021)
            if '2021-01' <= quarter.strftime('%Y-%m') <= '2021-12':
                recovery_factor = 1 - (idx - 4) * 0.05
                unemployment_rural *= max(1.0, recovery_factor)
                unemployment_urban *= max(1.0, recovery_factor)

            # Add anomalies for specific states
            if has_employment_crisis:
                unemployment_rural *= 1.15
                unemployment_urban *= 1.20

            # Calculate other metrics
            lfpr_rural = base_lfpr + np.random.normal(0, 1)
            lfpr_urban = base_lfpr - 3 + np.random.normal(0, 1.2)

            wpr_rural = base_wpr + np.random.normal(0, 1)
            wpr_urban = base_wpr - 2 + np.random.normal(0, 1.2)

            unemployment_combined = (unemployment_rural + unemployment_urban) / 2
            lfpr_combined = (lfpr_rural + lfpr_urban) / 2
            wpr_combined = (wpr_rural + wpr_urban) / 2

            data.append({
                'State': state,
                'Quarter': quarter,
                'Year': quarter.year,
                'Quarter_Num': (quarter.month - 1) // 3 + 1,
                'Unemployment_Rate_Rural': round(unemployment_rural, 2),
                'Unemployment_Rate_Urban': round(unemployment_urban, 2),
                'Unemployment_Rate_Combined': round(unemployment_combined, 2),
                'LFPR_Rural': round(lfpr_rural, 2),
                'LFPR_Urban': round(lfpr_urban, 2),
                'LFPR_Combined': round(lfpr_combined, 2),
                'WPR_Rural': round(wpr_rural, 2),
                'WPR_Urban': round(wpr_urban, 2),
                'WPR_Combined': round(wpr_combined, 2),
            })

    df = pd.DataFrame(data)
    df.to_csv(DATA_DIR / "employment_statewise.csv", index=False)
    print(f"✓ Generated {len(df)} records of employment data")
    return df

def generate_sectoral_gdp_data():
    """Generate sectoral GDP/GVA data"""
    print("Generating synthetic sectoral GDP data...")

    sectors = [
        'Agriculture', 'Mining', 'Manufacturing', 'Electricity',
        'Construction', 'Trade & Hotels', 'Transport & Communication',
        'Financial Services', 'Real Estate', 'Public Administration',
        'Other Services'
    ]

    quarters = pd.date_range(start='2020-01', end='2026-01', freq='QS')

    data = []

    for sector in sectors:
        base_gva = np.random.uniform(50000, 200000)  # in crores
        growth_rate = np.random.uniform(0.5, 3.0)

        for idx, quarter in enumerate(quarters):
            gva = base_gva * (1 + growth_rate/100) ** idx

            # COVID impact
            if '2020-04' <= quarter.strftime('%Y-%m') <= '2020-06':
                if sector in ['Trade & Hotels', 'Transport & Communication', 'Construction']:
                    gva *= 0.6  # Severe impact
                elif sector in ['Manufacturing', 'Mining']:
                    gva *= 0.75
                elif sector == 'Agriculture':
                    gva *= 0.95  # Minimal impact

            # Add volatility
            gva += np.random.normal(0, base_gva * 0.02)

            # Calculate YoY growth
            if idx >= 4:
                prev_gva = base_gva * (1 + growth_rate/100) ** (idx - 4)
                yoy_growth = ((gva - prev_gva) / prev_gva) * 100
            else:
                yoy_growth = growth_rate

            data.append({
                'Sector': sector,
                'Quarter': quarter,
                'Year': quarter.year,
                'Quarter_Num': (quarter.month - 1) // 3 + 1,
                'GVA_Crores': round(gva, 2),
                'YoY_Growth': round(yoy_growth, 2),
            })

    df = pd.DataFrame(data)
    df.to_csv(DATA_DIR / "sectoral_gdp.csv", index=False)
    print(f"✓ Generated {len(df)} records of sectoral GDP data")
    return df

if __name__ == "__main__":
    print("="*60)
    print("MOSPI Data Fetcher")
    print("="*60)

    # Try API first
    cpi_df = fetch_cpi_data_api()

    # Generate synthetic data
    if cpi_df is None:
        cpi_df = generate_synthetic_cpi_data()

    employment_df = generate_synthetic_employment_data()
    gdp_df = generate_sectoral_gdp_data()

    print("\n" + "="*60)
    print("Data Summary:")
    print("="*60)
    print(f"CPI Data: {len(cpi_df)} records")
    print(f"Employment Data: {len(employment_df)} records")
    print(f"Sectoral GDP Data: {len(gdp_df)} records")
    print("\nAll data saved to 'data/' directory")
