#!/usr/bin/env python3
"""
MOSPI Data Analysis - Detective Mode
Hunting for anomalies, patterns, and stories in India's economic data
"""

import pandas as pd
import numpy as np
from scipy import stats
from scipy.stats import zscore, iqr
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans, DBSCAN
from sklearn.ensemble import IsolationForest
import json
from pathlib import Path
from datetime import datetime

DATA_DIR = Path("data")
INSIGHTS_DIR = Path("insights")
INSIGHTS_DIR.mkdir(exist_ok=True)

def load_data():
    """Load all datasets"""
    print("Loading datasets...")
    cpi_df = pd.read_csv(DATA_DIR / "cpi_statewise.csv", parse_dates=['Date'])
    employment_df = pd.read_csv(DATA_DIR / "employment_statewise.csv", parse_dates=['Quarter'])
    gdp_df = pd.read_csv(DATA_DIR / "sectoral_gdp.csv", parse_dates=['Quarter'])

    return cpi_df, employment_df, gdp_df

def detect_outliers_zscore(data, threshold=3):
    """Detect outliers using Z-score method"""
    z_scores = np.abs(zscore(data, nan_policy='omit'))
    return z_scores > threshold

def detect_outliers_iqr(data, multiplier=1.5):
    """Detect outliers using IQR method"""
    Q1 = np.percentile(data, 25)
    Q3 = np.percentile(data, 75)
    IQR = Q3 - Q1
    lower_bound = Q1 - multiplier * IQR
    upper_bound = Q3 + multiplier * IQR
    return (data < lower_bound) | (data > upper_bound)

def detect_outliers_isolation_forest(df, features):
    """Detect outliers using Isolation Forest"""
    iso_forest = IsolationForest(contamination=0.1, random_state=42)
    outliers = iso_forest.fit_predict(df[features])
    return outliers == -1

def analyze_cpi_data(cpi_df):
    """Comprehensive CPI analysis"""
    print("\n" + "="*80)
    print("ANALYZING CPI DATA - INFLATION DETECTIVE")
    print("="*80)

    insights = {}

    # 1. Find states with highest inflation volatility
    volatility = cpi_df.groupby('State')['Inflation_Combined'].std().sort_values(ascending=False)
    insights['high_volatility_states'] = volatility.head(10).to_dict()
    print("\n📊 TOP 10 STATES BY INFLATION VOLATILITY:")
    for state, vol in list(insights['high_volatility_states'].items())[:5]:
        print(f"   {state}: {vol:.2f}%")

    # 2. Rural-Urban inflation gap
    cpi_df['Rural_Urban_Gap'] = cpi_df['Inflation_Rural'] - cpi_df['Inflation_Urban']
    gap_analysis = cpi_df.groupby('State')['Rural_Urban_Gap'].mean().sort_values(ascending=False)
    insights['rural_urban_gap'] = gap_analysis.head(10).to_dict()
    print("\n🏘️  BIGGEST RURAL-URBAN INFLATION GAPS:")
    for state, gap in list(insights['rural_urban_gap'].items())[:5]:
        direction = "Rural higher" if gap > 0 else "Urban higher"
        print(f"   {state}: {abs(gap):.2f}% ({direction})")

    # 3. Detect inflation spikes (anomalies)
    cpi_df['Inflation_Zscore'] = cpi_df.groupby('State')['Inflation_Combined'].transform(
        lambda x: (x - x.mean()) / x.std()
    )

    anomalies = cpi_df[abs(cpi_df['Inflation_Zscore']) > 2.5].sort_values('Inflation_Zscore', ascending=False)
    insights['inflation_spikes'] = anomalies[['State', 'Date', 'Inflation_Combined', 'Inflation_Zscore']].head(20).to_dict('records')

    print("\n🚨 MAJOR INFLATION ANOMALIES DETECTED:")
    for idx, anomaly in enumerate(anomalies.head(5).itertuples(), 1):
        print(f"   {idx}. {anomaly.State} ({anomaly.Date.strftime('%b %Y')}): {anomaly.Inflation_Combined:.2f}% (Z-score: {anomaly.Inflation_Zscore:.2f})")

    # 4. Find states that bucked national trends
    national_avg = cpi_df.groupby('Date')['Inflation_Combined'].mean()
    cpi_df['Deviation_From_National'] = cpi_df.apply(
        lambda row: row['Inflation_Combined'] - national_avg[row['Date']],
        axis=1
    )

    contrarians = cpi_df.groupby('State')['Deviation_From_National'].apply(
        lambda x: (x.abs() > 2).sum()
    ).sort_values(ascending=False)

    insights['contrarian_states'] = contrarians.head(10).to_dict()
    print("\n🎯 STATES BUCKING NATIONAL TRENDS (>2% deviation):")
    for state, count in list(insights['contrarian_states'].items())[:5]:
        print(f"   {state}: {count} months")

    # 5. Time-based patterns - which months see highest inflation?
    monthly_pattern = cpi_df.groupby('Month')['Inflation_Combined'].mean().sort_values(ascending=False)
    insights['high_inflation_months'] = monthly_pattern.to_dict()
    print("\n📅 MONTHS WITH HIGHEST AVERAGE INFLATION:")
    month_names = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    for month, infl in list(monthly_pattern.items())[:6]:
        print(f"   {month_names[month]}: {infl:.2f}%")

    # 6. Find sudden changes (month-over-month shocks)
    cpi_df_sorted = cpi_df.sort_values(['State', 'Date'])
    cpi_df_sorted['MoM_Change'] = cpi_df_sorted.groupby('State')['Inflation_Combined'].diff()
    sudden_changes = cpi_df_sorted[abs(cpi_df_sorted['MoM_Change']) > 3].sort_values('MoM_Change', ascending=False)

    insights['sudden_changes'] = sudden_changes[['State', 'Date', 'Inflation_Combined', 'MoM_Change']].head(20).to_dict('records')
    print("\n⚡ SUDDEN INFLATION SHOCKS (>3% MoM change):")
    for idx, shock in enumerate(sudden_changes.head(5).itertuples(), 1):
        direction = "spike" if shock.MoM_Change > 0 else "drop"
        print(f"   {idx}. {shock.State} ({shock.Date.strftime('%b %Y')}): {shock.MoM_Change:+.2f}% {direction}")

    # 7. COVID-19 impact analysis
    covid_period = cpi_df[(cpi_df['Date'] >= '2020-03') & (cpi_df['Date'] <= '2020-12')]
    covid_impact = covid_period.groupby('State')['Inflation_Combined'].mean().sort_values(ascending=False)
    insights['covid_impact'] = covid_impact.head(10).to_dict()

    print("\n🦠 COVID-19 ERA INFLATION (Mar-Dec 2020):")
    for state, infl in list(covid_impact.items())[:5]:
        print(f"   {state}: {infl:.2f}%")

    # 8. Recent trends (2024-2025)
    recent_data = cpi_df[cpi_df['Year'] >= 2024]
    recent_avg = recent_data.groupby('State')['Inflation_Combined'].mean().sort_values(ascending=False)
    insights['recent_inflation_leaders'] = recent_avg.head(10).to_dict()

    print("\n🔥 HIGHEST INFLATION STATES (2024-2025):")
    for state, infl in list(recent_avg.items())[:5]:
        print(f"   {state}: {infl:.2f}%")

    # 9. Statistical tests - Are rural and urban inflation significantly different?
    from scipy.stats import ttest_rel
    t_stat, p_value = ttest_rel(cpi_df['Inflation_Rural'], cpi_df['Inflation_Urban'])
    insights['rural_urban_ttest'] = {
        't_statistic': float(t_stat),
        'p_value': float(p_value),
        'significant': p_value < 0.05
    }

    print(f"\n📈 PAIRED T-TEST: Rural vs Urban Inflation")
    print(f"   t-statistic: {t_stat:.4f}, p-value: {p_value:.6f}")
    print(f"   Result: {'SIGNIFICANTLY DIFFERENT' if p_value < 0.05 else 'NOT significantly different'}")

    return insights

def analyze_employment_data(employment_df):
    """Comprehensive employment analysis"""
    print("\n" + "="*80)
    print("ANALYZING EMPLOYMENT DATA - JOB MARKET DETECTIVE")
    print("="*80)

    insights = {}

    # 1. States with highest unemployment
    avg_unemployment = employment_df.groupby('State')['Unemployment_Rate_Combined'].mean().sort_values(ascending=False)
    insights['highest_unemployment'] = avg_unemployment.head(10).to_dict()

    print("\n💼 STATES WITH HIGHEST AVERAGE UNEMPLOYMENT:")
    for state, rate in list(avg_unemployment.items())[:5]:
        print(f"   {state}: {rate:.2f}%")

    # 2. Urban vs Rural unemployment gap
    employment_df['Urban_Rural_Unemp_Gap'] = employment_df['Unemployment_Rate_Urban'] - employment_df['Unemployment_Rate_Rural']
    gap_analysis = employment_df.groupby('State')['Urban_Rural_Unemp_Gap'].mean().sort_values(ascending=False)
    insights['urban_rural_unemployment_gap'] = gap_analysis.head(10).to_dict()

    print("\n🏙️  URBAN-RURAL UNEMPLOYMENT GAPS:")
    for state, gap in list(gap_analysis.items())[:5]:
        higher = "Urban" if gap > 0 else "Rural"
        print(f"   {state}: {abs(gap):.2f}% higher in {higher} areas")

    # 3. COVID-19 employment shock
    pre_covid = employment_df[employment_df['Year'] < 2020].groupby('State')['Unemployment_Rate_Combined'].mean()
    during_covid = employment_df[employment_df['Year'] == 2020].groupby('State')['Unemployment_Rate_Combined'].mean()
    covid_shock = (during_covid - pre_covid).sort_values(ascending=False)

    insights['covid_employment_shock'] = covid_shock.head(10).to_dict()

    print("\n🦠 COVID-19 EMPLOYMENT SHOCK (2020 vs pre-2020):")
    for state, shock in list(covid_shock.items())[:5]:
        print(f"   {state}: +{shock:.2f}% unemployment increase")

    # 4. Labour Force Participation Rate trends
    lfpr_trends = employment_df.groupby('State')['LFPR_Combined'].mean().sort_values(ascending=False)
    insights['lfpr_leaders'] = lfpr_trends.head(10).to_dict()

    print("\n🚀 HIGHEST LABOUR FORCE PARTICIPATION RATES:")
    for state, lfpr in list(lfpr_trends.items())[:5]:
        print(f"   {state}: {lfpr:.2f}%")

    # 5. Worker Population Ratio analysis
    wpr_trends = employment_df.groupby('State')['WPR_Combined'].mean().sort_values(ascending=False)
    insights['wpr_leaders'] = wpr_trends.head(10).to_dict()

    print("\n👷 HIGHEST WORKER POPULATION RATIOS:")
    for state, wpr in list(wpr_trends.items())[:5]:
        print(f"   {state}: {wpr:.2f}%")

    # 6. Find states with improving/worsening trends
    recent = employment_df[employment_df['Year'] >= 2023].groupby('State')['Unemployment_Rate_Combined'].mean()
    earlier = employment_df[(employment_df['Year'] >= 2020) & (employment_df['Year'] < 2023)].groupby('State')['Unemployment_Rate_Combined'].mean()
    trend = recent - earlier

    improving = trend.sort_values().head(5)
    worsening = trend.sort_values(ascending=False).head(5)

    insights['improving_states'] = improving.to_dict()
    insights['worsening_states'] = worsening.to_dict()

    print("\n📊 EMPLOYMENT TRENDS (2023+ vs 2020-2022):")
    print("   IMPROVING (unemployment down):")
    for state, change in improving.items():
        print(f"      {state}: {change:.2f}%")
    print("   WORSENING (unemployment up):")
    for state, change in list(worsening.items())[:3]:
        print(f"      {state}: +{change:.2f}%")

    # 7. Volatility in unemployment rates
    volatility = employment_df.groupby('State')['Unemployment_Rate_Combined'].std().sort_values(ascending=False)
    insights['unemployment_volatility'] = volatility.head(10).to_dict()

    print("\n📉 MOST VOLATILE UNEMPLOYMENT RATES:")
    for state, vol in list(volatility.items())[:5]:
        print(f"   {state}: σ={vol:.2f}%")

    return insights

def analyze_gdp_data(gdp_df):
    """Comprehensive GDP/GVA sectoral analysis"""
    print("\n" + "="*80)
    print("ANALYZING SECTORAL GDP - ECONOMIC STRUCTURE DETECTIVE")
    print("="*80)

    insights = {}

    # 1. Fastest growing sectors
    avg_growth = gdp_df.groupby('Sector')['YoY_Growth'].mean().sort_values(ascending=False)
    insights['fastest_growing_sectors'] = avg_growth.to_dict()

    print("\n🚀 FASTEST GROWING SECTORS (Average YoY):")
    for sector, growth in list(avg_growth.items())[:5]:
        print(f"   {sector}: {growth:.2f}%")

    # 2. Most volatile sectors
    volatility = gdp_df.groupby('Sector')['YoY_Growth'].std().sort_values(ascending=False)
    insights['most_volatile_sectors'] = volatility.to_dict()

    print("\n📊 MOST VOLATILE SECTORS:")
    for sector, vol in list(volatility.items())[:5]:
        print(f"   {sector}: σ={vol:.2f}%")

    # 3. COVID-19 sectoral impact
    pre_covid = gdp_df[(gdp_df['Year'] == 2019) | (gdp_df['Year'] == 2020) & (gdp_df['Quarter_Num'] == 1)]
    covid_q2_2020 = gdp_df[(gdp_df['Year'] == 2020) & (gdp_df['Quarter_Num'] == 2)]

    pre_covid_avg = pre_covid.groupby('Sector')['GVA_Crores'].mean()
    covid_avg = covid_q2_2020.groupby('Sector')['GVA_Crores'].mean()

    covid_impact = ((covid_avg - pre_covid_avg) / pre_covid_avg * 100).sort_values()
    insights['covid_sectoral_impact'] = covid_impact.to_dict()

    print("\n🦠 COVID-19 SECTORAL IMPACT (Q2 2020 vs baseline):")
    for sector, impact in covid_impact.items():
        emoji = "🔴" if impact < -20 else "🟡" if impact < 0 else "🟢"
        print(f"   {emoji} {sector}: {impact:+.2f}%")

    # 4. Recovery analysis
    pre_covid_gva = gdp_df[gdp_df['Year'] == 2019].groupby('Sector')['GVA_Crores'].mean()
    recent_gva = gdp_df[gdp_df['Year'] >= 2024].groupby('Sector')['GVA_Crores'].mean()

    recovery = ((recent_gva - pre_covid_gva) / pre_covid_gva * 100).sort_values(ascending=False)
    insights['sectoral_recovery'] = recovery.to_dict()

    print("\n📈 SECTORAL RECOVERY (2024+ vs 2019 baseline):")
    for sector, recov in recovery.items():
        print(f"   {sector}: {recov:+.2f}%")

    # 5. Current sector dominance
    recent_data = gdp_df[gdp_df['Year'] >= 2024]
    sector_size = recent_data.groupby('Sector')['GVA_Crores'].mean().sort_values(ascending=False)
    total_gva = sector_size.sum()
    sector_share = (sector_size / total_gva * 100)
    insights['sector_shares'] = sector_share.to_dict()

    print("\n💰 SECTORAL COMPOSITION (2024+ average):")
    for sector, share in sector_share.items():
        print(f"   {sector}: {share:.2f}% of economy")

    # 6. Find quarters with negative growth across multiple sectors
    negative_growth_quarters = gdp_df[gdp_df['YoY_Growth'] < 0].groupby('Quarter').size().sort_values(ascending=False)
    insights['crisis_quarters'] = negative_growth_quarters.head(10).to_dict()

    print("\n🚨 QUARTERS WITH MOST NEGATIVE GROWTH SECTORS:")
    for quarter, count in list(negative_growth_quarters.items())[:5]:
        print(f"   {quarter}: {count} sectors in decline")

    return insights

def cross_sectional_analysis(cpi_df, employment_df, gdp_df):
    """Find relationships between different datasets"""
    print("\n" + "="*80)
    print("CROSS-SECTIONAL ANALYSIS - CONNECTING THE DOTS")
    print("="*80)

    insights = {}

    # 1. Correlation between inflation and unemployment (by state)
    # Aggregate to state level
    cpi_state_avg = cpi_df.groupby('State')['Inflation_Combined'].mean()
    emp_state_avg = employment_df.groupby('State')['Unemployment_Rate_Combined'].mean()

    # Find common states
    common_states = set(cpi_state_avg.index) & set(emp_state_avg.index)
    cpi_common = cpi_state_avg[list(common_states)]
    emp_common = emp_state_avg[list(common_states)]

    correlation = cpi_common.corr(emp_common)
    insights['inflation_unemployment_correlation'] = float(correlation)

    print(f"\n🔗 INFLATION-UNEMPLOYMENT CORRELATION:")
    print(f"   Correlation: {correlation:.4f}")
    if abs(correlation) > 0.5:
        relationship = "Strong positive" if correlation > 0 else "Strong negative"
    elif abs(correlation) > 0.3:
        relationship = "Moderate positive" if correlation > 0 else "Moderate negative"
    else:
        relationship = "Weak"
    print(f"   Interpretation: {relationship} relationship")

    # 2. Economic paradoxes - states with high GDP growth but high unemployment
    gdp_by_state = gdp_df.groupby('Year')['YoY_Growth'].mean()  # Using as national proxy
    emp_by_year = employment_df.groupby('Year')['Unemployment_Rate_Combined'].mean()

    print(f"\n🤔 ECONOMIC PARADOXES:")
    print(f"   Years with high GDP growth but high unemployment:")
    for year in emp_by_year.index:
        if year in gdp_by_state.index:
            if gdp_by_state[year] > 5 and emp_by_year[year] > 6:
                print(f"      {year}: GDP growth {gdp_by_state[year]:.2f}%, Unemployment {emp_by_year[year]:.2f}%")

    # 3. Which states are outliers in the inflation-employment space?
    # Cluster analysis
    from sklearn.preprocessing import StandardScaler
    from sklearn.cluster import KMeans

    if len(common_states) >= 3:
        data_for_clustering = pd.DataFrame({
            'inflation': cpi_common,
            'unemployment': emp_common
        })

        scaler = StandardScaler()
        scaled_data = scaler.fit_transform(data_for_clustering)

        kmeans = KMeans(n_clusters=3, random_state=42)
        clusters = kmeans.fit_predict(scaled_data)

        data_for_clustering['cluster'] = clusters

        print(f"\n🎯 STATE CLUSTERS (Inflation-Unemployment):")
        for cluster_id in range(3):
            cluster_states = data_for_clustering[data_for_clustering['cluster'] == cluster_id]
            print(f"   Cluster {cluster_id+1}: {', '.join(cluster_states.index[:5])}")
            print(f"      Avg Inflation: {cluster_states['inflation'].mean():.2f}%")
            print(f"      Avg Unemployment: {cluster_states['unemployment'].mean():.2f}%")

        insights['state_clusters'] = {
            str(k): list(data_for_clustering[data_for_clustering['cluster'] == k].index)
            for k in range(3)
        }

    return insights

def generate_summary_report(all_insights):
    """Generate a comprehensive summary"""
    print("\n" + "="*80)
    print("SUMMARY - KEY FINDINGS")
    print("="*80)

    # Save insights to JSON
    with open(INSIGHTS_DIR / 'analysis_insights.json', 'w') as f:
        json.dump(all_insights, f, indent=2, default=str)

    print(f"\n✅ Analysis complete!")
    print(f"📊 Insights saved to: {INSIGHTS_DIR / 'analysis_insights.json'}")

    return all_insights

if __name__ == "__main__":
    print("\n" + "🔍" * 40)
    print("MOSPI DATA ANALYSIS - ANOMALY DETECTIVE")
    print("🔍" * 40)

    # Load data
    cpi_df, employment_df, gdp_df = load_data()

    # Run analyses
    all_insights = {}

    all_insights['cpi'] = analyze_cpi_data(cpi_df)
    all_insights['employment'] = analyze_employment_data(employment_df)
    all_insights['gdp'] = analyze_gdp_data(gdp_df)
    all_insights['cross_sectional'] = cross_sectional_analysis(cpi_df, employment_df, gdp_df)

    # Generate summary
    generate_summary_report(all_insights)

    print("\n" + "="*80)
    print("Next steps: Run create_visualizations.py to generate interactive charts")
    print("="*80 + "\n")
