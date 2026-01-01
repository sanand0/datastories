# India export-import data (FTDDP) - investigative analysis notes

## Data understanding

- Source file: `export-import.parquet` (18,053,536 rows).
- Granularity: one row per Commodity x Country x Port x Year x Month x Type.
- Dimensions (categorical): Commodity, Country, Port, Unit, Type.
- Measures (numeric): Quantity, INR Value, USD Value.
- Coverage:
  - Export data: 2003-2025 (15,610,168 rows).
  - Import data: 2021-2025 only (2,443,368 rows). This is a major coverage gap for any long-run import trend work.
- Completeness: no nulls or empty strings in key fields.
- Ranges: Year 2003-2025, Month 1-12.

## Derived metrics used

- Trade balance (exports - imports) by year/country/commodity.
- Concentration metrics: HHI by year/type across commodities, countries, and ports; top-1/top-3 share by commodity and supplier.
- Year-over-year deltas and change decomposition by commodity and country; non-petroleum export growth.
- Intra-industry trade index (Grubel-Lloyd) by commodity, country, and commodity-country pairs.
- Port specialization (top commodity share per port) and SEZ share of exports.
- Port-category routing (air/sea/ICD/SEZ) and market churn in top destinations/ports.
- Unit-value metrics (USD per quantity) and price-vs-volume decomposition for single-unit commodities.
- Implied FX rate (INR Value / USD Value) distribution and outlier rates by commodity.
- Seasonality by month (average month USD value).

## What matters (audiences and questions)

- Policymakers and trade negotiators: Where do deficits concentrate by commodity or partner, and where are surplus leverage points?
- Exporters and industry groups: Which products/markets are accelerating or declining? Which markets are single-commodity dependent?
- Port and logistics planners: How concentrated is export value across ports, and what are choke points?
- Investors and supply chain risk teams: Which commodity-country pairs show outsized exposure or recent shocks?
- Journalists and researchers: Which narratives overturn common assumptions (e.g., India only imports energy) or reveal hidden dependencies?

## Key signals and story leads (numbers are from analysis datasets)

1. Deficit is extremely concentrated in a handful of commodities.
   - 2024 overall balance: -$273.7B.
   - Energy + gold alone account for 76.3% of the deficit; excluding crude, petroleum products, coal, and gold cuts the deficit to -$64.9B (`analysis/data/deficit_concentration_2024.csv`).
   - The top 5 deficit commodities (crude, gold, coal, electronics components, computer hardware) sum to 104% of the total deficit, meaning surpluses elsewhere mask the real dependence (`analysis/data/deficit_concentration_2024.csv`, `analysis/data/commodity_balance_2024.csv`).
     Why noteworthy: A tiny set of commodities explains almost the entire trade gap, which is rarer than a broad-based deficit.
     Implications: Policy or market shifts in these few categories can swing the national balance; targeted interventions could move the needle faster than broad trade policy.

2. Refinery hub story is deeper than it looks: half the petroleum exports are SEZ-driven.
   - 2024 crude imports: $147.2B (20.5% of imports) vs petroleum product exports: $71.5B (16.2% of exports).
   - SEZ ports handle ~49-58% of petroleum product exports, while SEZs overall handle only ~11-16% of total exports (`analysis/data/sez_share_petroleum_exports_by_year.csv`, `analysis/data/sez_share_exports_by_year.csv`).
   - Jamnagar (Reliance) alone ships 48.2% of petroleum product exports, a single-point-of-failure logistics story (`analysis/data/commodity_port_concentration_export_2024.csv`).
     Why noteworthy: A strategic export pillar is routed through a narrow infrastructure funnel, not a broad national network.
     Implications: SEZ policy, refinery disruptions, or sanctions constraints could have outsized effects; risk management should focus on a few physical nodes.

3. Import basket is structurally more concentrated than export basket.
   - 2024 commodity HHI: imports 0.065 vs exports 0.042 (imports are ~56% more concentrated) (`analysis/data/hhi_year_type.csv`).
   - Top-5 commodities in 2024: imports 44.3% vs exports 33.2% (`analysis/data/top5_share_2024.csv`).
     Why noteworthy: Concentration is higher despite a large supplier set, signaling dependence on specific product classes.
     Implications: Import shocks are harder to substitute; resilience planning should prioritize the top few import categories.

4. Hidden export growth: non-petroleum exports are strong, but energy masks it.
   - Total exports rose only +$11.4B in 2024, but excluding petroleum products exports rose +$25.7B (+7.4%) (`analysis/data/export_growth_ex_petroleum_2023_2024.csv`).
   - Petroleum’s share of exports fell from 19.9% (2023) to 16.2% (2024), so the headline hides broad-based gains (`analysis/data/commodity_growth_export_2023_2024.csv`, `analysis/data/year_type_totals.csv`).
     Why noteworthy: The headline narrative understates competitiveness in non-energy goods.
     Implications: Export promotion should emphasize non-petro momentum and protect it from exchange-rate or logistics headwinds.

5. Export growth is ultra-concentrated in a few commodities and markets.
   - Top 2 export gainers (telecom instruments + aircraft) contributed $11.9B, exceeding total export growth of $11.4B (`analysis/data/export_change_2023_2024_by_commodity.csv`).
   - The top 3 destination markets (USA, UAE, Singapore) contributed $13.8B of growth; declines elsewhere offset the rest (`analysis/data/export_change_2023_2024_by_country.csv`).
     Why noteworthy: Overall growth exists only because a few spikes counterbalanced broad declines.
     Implications: Any slowdown in those commodities or markets could reverse national growth; diversification is a direct risk hedge.

6. Import growth in 2024 is dominated by gold and crude, with a supplier story.
   - Gold alone explains 37% of the 2024 import increase; crude adds another 15% (`analysis/data/import_change_2023_2024_by_commodity.csv`).
   - Switzerland + UAE supply ~59% of gold imports, exposing a narrow sourcing corridor (`analysis/data/gold_import_suppliers_2024.csv`).
     Why noteworthy: The import surge is not broad demand; it is concentrated in a single discretionary commodity.
     Implications: Gold duty or demand shifts can materially affect the deficit; supplier concentration raises compliance and liquidity risks.

7. India is a two-way trader in big tech categories, not just a net importer.
   - Telecom instruments and electric machinery have Grubel-Lloyd indices ~0.95 and net shares near 5%, despite $42B and $26B gross flows (`analysis/data/intra_industry_commodity_2024.csv`).
   - This points to assembly/re-export or intra-industry specialization rather than one-way dependence.
     Why noteworthy: These categories behave like integrated value chains, not pure import dependence.
     Implications: Policy should target upgrading within the chain (design, components) rather than blunt import substitution.

8. Balanced trade partners hide large gross flows.
   - France and Belgium have near-perfect balance (GL > 0.99) with $13-16B total trade; Singapore and South Africa also show high two-way trade (`analysis/data/intra_industry_country_2024.csv`).
   - These partners are structurally different from China or Switzerland, where the imbalance dominates.
     Why noteworthy: Net balance statistics conceal sizable two-way interdependence.
     Implications: Disruptions with these partners could hit both export and import pipelines simultaneously; diplomacy should reflect mutual exposure.

9. Commodity dependence is extreme for certain export products and buyers.
   - Iron ore exports are 91.6% dependent on China; top three buyers account for 96.5% (`analysis/data/commodity_destination_concentration_export_2024.csv`).
   - Gems and jewelry: top three destinations account for 78.7% of exports (`analysis/data/commodity_destination_concentration_export_2024.csv`).
     Why noteworthy: A single buyer or small buyer set dominates global demand for key exports.
     Implications: Demand shocks or policy changes in one country can wipe out national export revenues in those products.

10. Supplier dependence is sharp in key tech imports.
    - Computer hardware imports are 50.5% from a single supplier (China), and electronics components’ top three suppliers account for 65.8% (`analysis/data/commodity_supplier_concentration_import_2024.csv`).
    - Crude oil’s top three suppliers provide 68.8% of imports, a strategic exposure (`analysis/data/commodity_supplier_concentration_import_2024.csv`).
      Why noteworthy: Critical import categories have concentration levels comparable to monopoly exposure.
      Implications: Supply chain resilience requires active diversification or strategic stockpiles in these categories.

11. Port specialization creates hidden choke points.
    - Among 62 ports with >$1B exports, 6 are >90% single-commodity (`analysis/data/port_specialization_2024_export.csv`).
    - Gems: 89.9% shipped via DPCC Mumbai; aircraft: 81.2% via GMR Hyderabad SEZ (`analysis/data/commodity_port_concentration_export_2024.csv`).
      Why noteworthy: Commodity supply chains are physically concentrated even when trade is economically diversified.
      Implications: Port outages or localized disruptions can cripple entire export categories; redundancy planning is essential.

12. Port concentration has fallen sharply over two decades.
    - Export port HHI dropped 6.36x from 2012 to 2024 (0.252 -> 0.0396), showing logistics diversification even as port specialization remains high (`analysis/data/hhi_year_type.csv`).
      Why noteworthy: The network diversified while individual commodities stayed concentrated.
      Implications: Infrastructure policy worked at the system level, but commodity-level risk remains.

13. Two-way commodity-country swaps show re-export dynamics.
    - High-balance pairs include petroleum products with UAE/USA, gems with Hong Kong/Belgium, and aircraft with Saudi/UAE (`analysis/data/intra_industry_pairs_2024_high_balance.csv`).
      Why noteworthy: These flows suggest re-export hubs and processing trade rather than final demand.
      Implications: Tracking these corridors is key for sanctions risk, value-added attribution, and policy targeting.

14. Data quality signal: FX outliers concentrate in a few commodity categories.
    - Certain metals/chemicals show >10% of rows with implied INR/USD outside 40-100, worth auditing before publication (`analysis/data/fx_outliers_by_commodity.csv`).
      Why noteworthy: Outliers are not random noise; they cluster in specific commodities.
      Implications: Any analysis on those commodities should apply cleaning rules or robustness checks.

15. Air cargo is a silent backbone of high-value exports.
    - Air handles 15.5% of export value, comparable to SEZ share (14.1%), despite smaller physical volumes (`analysis/data/port_category_share_2024.csv`).
    - Telecom instruments are 77.6% air-routed; aircraft exports are 85% SEZ-routed (`analysis/data/commodity_port_category_export_2024.csv`).
      Why noteworthy: High-value export competitiveness depends on air logistics more than commonly assumed.
      Implications: Airport capacity, customs speed, and air freight pricing are strategic trade levers.

16. Market churn shows non-obvious rerouting in specific commodities.
    - Computer hardware exports flipped top buyer from UAE (17%) to Russia (38%) in one year, a large directional shift (`analysis/data/commodity_market_churn_export_2023_2024.csv`).
    - Petroleum products’ top port share collapsed from 57.5% to 33.7%, in part due to naming splits and possible routing shifts (`analysis/data/commodity_port_churn_export_2023_2024.csv`).
      Why noteworthy: Sudden switches in top destinations or ports are rare and signal structural change.
      Implications: These shifts can reflect geopolitical realignments or policy shocks; monitoring is necessary for risk forecasting.

17. Value growth sometimes hides quantity decline (price-led trade).
    - Non-basmati rice export value rose 11.7% while quantity fell 6.6% (unit value +19.5%); sugar value fell 38.7% but unit value rose 8.8% (`analysis/data/commodity_price_volume_decomp_export_2023_2024.csv`).
    - Paint/varnish exports doubled in value with only ~10% quantity growth, implying a sharp price/mix shift (`analysis/data/commodity_price_volume_decomp_export_2023_2024.csv`).
      Why noteworthy: Apparent demand gains can be price effects, not volume expansion.
      Implications: Revenue resilience may vanish if prices normalize; sector planning should separate volume from price drivers.

18. Unit value gaps reveal specialization vs dependency.
    - Petroleum products export unit value is 1.42x import unit value, consistent with refinery value-add.
    - Drug formulations show the opposite: export unit value is ~24% of import unit value, implying imports skew to higher-end biologics while exports skew to generics (`analysis/data/commodity_unit_value_export_import_2024.csv`).
      Why noteworthy: The unit-value gaps quantify where India adds value vs where it buys high-end inputs.
      Implications: R&D and industrial policy could target upgrading in categories with persistent import premium.

19. “UNSPECIFIED” exports show a historical spike that vanishes later.
    - Exports to UNSPECIFIED reached 6.3% of total exports in 2011, but sit below 1% from 2021 onward (`analysis/data/unspecified_share_by_year_type.csv`).
    - This suggests a classification change or data-policy shift that can distort long-run comparisons.
      Why noteworthy: A structural data change can masquerade as a trade shock.
      Implications: Long-run trend narratives must adjust for classification breaks to avoid false inferences.

20. Seasonality is concentrated in a few commodities.
    - Bulk minerals/ores, fresh fruits, and iron ore show very high seasonal CV (>0.46), suggesting strong harvest or policy timing effects (`analysis/data/commodity_seasonality_export_2021_2024.csv`).
      Why noteworthy: Seasonal volatility is not uniform; it is concentrated in a few high-value products.
      Implications: Logistics and policy interventions should be timed around these commodities’ peak windows.

## Segment and discover (ideas for deeper cuts)

- Commodity-country networks: identify re-export hubs (Netherlands, UAE, Singapore) vs final-demand markets.
- Intra-industry vs net-trade clustering: group commodities and partners by GL index to separate processing trade from true deficits.
- Port-commodity specialization: find ports dominated by a single commodity; test vulnerability to demand shocks.
- Country clusters by basket concentration (HHI) and balance: single-commodity suppliers (Iraq, Switzerland) vs diversified partners (China, USA).
- Commodity lifecycle trends: use change-point detection to spot structural breaks (pandemic, policy, sanctions).

## Leverage points (actionable hypotheses)

- Diversify crude sources or refine product mix to reduce deficit dependence on a few suppliers (Russia/Iraq/Saudi).
- Strengthen electronics supply chain resilience; imports remain highly concentrated in a few suppliers.
- Reduce single-port exposure in key commodities (petroleum, gems, aircraft).
- Target export promotion in markets where India is already near single-commodity dominance (easier marginal gains).
- Port capacity/efficiency: concentration means a small number of ports drive half of exports; disruptions have outsized effects.

## Verification and stress tests

- External cross-checks to run:
  - RBI or Ministry of Commerce annual trade stats for total exports/imports.
  - IEA/OPEC or BP statistics for crude import volumes and sources.
  - UN Comtrade or ITC for country-commodity cross-validation.
  - LBMA/customs data for gold import sources and volumes.
  - Port authority or SEZ reports for petroleum export routing.
- Robustness tests:
  - Repeat concentration and balance metrics on 2021-2024 only (to align import/export coverage).
  - Normalize port names and recompute port concentration.
  - Exclude "UNSPECIFIED" country and compare results.
  - Try USD-only vs INR-only totals to check for currency conversion artifacts.
  - Recompute GL indices after collapsing similar commodity labels to test sensitivity.

## Limitations and caveats

- Import coverage starts only in 2021, so long-run import trend analysis is not valid.
- 2025 is likely a partial year; treat 2025 comparisons as incomplete.
- Commodity labels are coarse (204 categories) and include a residual "OTHER COMMODITIES" bucket.
- Units vary by commodity; quantity comparisons across units are not meaningful.
- Port naming inconsistencies can split volumes unless normalized.
- Port category bucketing is heuristic (based on name substrings) and should be validated on key ports.
- Unit-value metrics assume consistent units within a commodity; interpret cautiously where unit codes or quantity definitions may vary.

## Assets generated (supporting datasets and code)

- Queries: `analysis/queries.sql`
- Outputs:
  - `analysis/data/summary_basic.csv`
  - `analysis/data/missingness.csv`
  - `analysis/data/type_coverage.csv`
  - `analysis/data/year_type_totals.csv`
  - `analysis/data/year_trade_balance.csv`
  - `analysis/data/top5_share_2024.csv`
  - `analysis/data/top_commodities_export.csv`
  - `analysis/data/top_commodities_import.csv`
  - `analysis/data/top_countries_export.csv`
  - `analysis/data/top_countries_import.csv`
  - `analysis/data/country_balance_2024.csv`
  - `analysis/data/ports_export_2024.csv`
  - `analysis/data/top_pairs_export_2024.csv`
  - `analysis/data/seasonality_by_month.csv`
  - `analysis/data/fx_implied_by_year.csv`
  - `analysis/data/hhi_year_type.csv`
  - `analysis/data/commodity_growth_export_2023_2024.csv`
  - `analysis/data/commodity_growth_import_2022_2023.csv`
  - `analysis/data/export_change_2023_2024_by_commodity.csv`
  - `analysis/data/export_change_2023_2024_by_country.csv`
  - `analysis/data/import_change_2023_2024_by_commodity.csv`
  - `analysis/data/import_change_2023_2024_by_country.csv`
  - `analysis/data/country_concentration_export_2024.csv`
  - `analysis/data/commodity_destination_concentration_export_2024.csv`
  - `analysis/data/commodity_supplier_concentration_import_2024.csv`
  - `analysis/data/country_export_diversity_2024.csv`
  - `analysis/data/country_import_diversity_2024.csv`
  - `analysis/data/commodity_balance_2024.csv`
  - `analysis/data/deficit_concentration_2024.csv`
  - `analysis/data/export_growth_ex_petroleum_2023_2024.csv`
  - `analysis/data/intra_industry_commodity_2024.csv`
  - `analysis/data/intra_industry_country_2024.csv`
  - `analysis/data/intra_industry_pairs_2024_top200.csv`
  - `analysis/data/intra_industry_pairs_2024_high_balance.csv`
  - `analysis/data/sez_share_exports_by_year.csv`
  - `analysis/data/sez_share_petroleum_exports_by_year.csv`
  - `analysis/data/port_specialization_2024_export.csv`
  - `analysis/data/port_name_variants_2024_export.csv`
  - `analysis/data/commodity_port_concentration_export_2024.csv`
  - `analysis/data/port_category_share_2024.csv`
  - `analysis/data/commodity_port_category_export_2024.csv`
  - `analysis/data/commodity_market_churn_export_2023_2024.csv`
  - `analysis/data/commodity_port_churn_export_2023_2024.csv`
  - `analysis/data/commodity_seasonality_export_2021_2024.csv`
  - `analysis/data/commodity_unit_value_export_import_2024.csv`
  - `analysis/data/commodity_price_volume_decomp_export_2023_2024.csv`
  - `analysis/data/unspecified_share_by_year_type.csv`
  - `analysis/data/unit_diversity_by_commodity.csv`
  - `analysis/data/fx_outliers_by_commodity.csv`
  - `analysis/data/gold_import_suppliers_2024.csv`

## How to regenerate

- Run:
  - `duckdb -c ".read analysis/queries.sql"`
