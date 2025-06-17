-- Query 1: Court Efficiency and Backlog Analysis
-- Which High Courts Are Performing Best?

INSTALL httpfs; LOAD httpfs;
INSTALL parquet; LOAD parquet;

-- Merge all data across years, courts, and benches
WITH combined AS (
    SELECT * FROM read_parquet('s3://indian-high-court-judgments/metadata/parquet/year=*/court=*/bench=*/metadata.parquet')
),
processed_data AS (
    SELECT 
        court_name,
        TRY_CAST(decision_date AS DATE) AS decision_date,
        TRY_CAST(filing_date AS DATE) AS filing_date,
        case_number,
        -- Calculate processing time in days
        CASE 
            WHEN TRY_CAST(decision_date AS DATE) IS NOT NULL 
            AND TRY_CAST(filing_date AS DATE) IS NOT NULL
            THEN DATE_DIFF('day', TRY_CAST(filing_date AS DATE), TRY_CAST(decision_date AS DATE))
        END AS processing_days
    FROM combined
    WHERE TRY_CAST(decision_date AS DATE) IS NOT NULL
    AND TRY_CAST(filing_date AS DATE) IS NOT NULL
    AND TRY_CAST(decision_date AS DATE) >= '2020-01-01'  -- Focus on recent years
),
court_stats AS (
    SELECT 
        court_name,
        COUNT(*) AS total_cases_disposed,
        AVG(processing_days) AS avg_processing_days,
        MEDIAN(processing_days) AS median_processing_days,
        MIN(processing_days) AS min_processing_days,
        MAX(processing_days) AS max_processing_days,
        -- Calculate percentiles for processing time
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY processing_days) AS p25_processing_days,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY processing_days) AS p75_processing_days,
        -- Count cases by processing time categories
        SUM(CASE WHEN processing_days <= 30 THEN 1 ELSE 0 END) AS cases_within_30_days,
        SUM(CASE WHEN processing_days <= 90 THEN 1 ELSE 0 END) AS cases_within_90_days,
        SUM(CASE WHEN processing_days <= 365 THEN 1 ELSE 0 END) AS cases_within_1_year,
        SUM(CASE WHEN processing_days > 365 THEN 1 ELSE 0 END) AS cases_over_1_year
    FROM processed_data
    GROUP BY court_name
)
SELECT 
    court_name,
    total_cases_disposed,
    ROUND(avg_processing_days, 2) AS avg_processing_days,
    median_processing_days,
    ROUND((cases_within_30_days * 100.0 / total_cases_disposed), 2) AS pct_resolved_30_days,
    ROUND((cases_within_90_days * 100.0 / total_cases_disposed), 2) AS pct_resolved_90_days,
    ROUND((cases_within_1_year * 100.0 / total_cases_disposed), 2) AS pct_resolved_1_year,
    ROUND((cases_over_1_year * 100.0 / total_cases_disposed), 2) AS pct_pending_over_1_year,
    -- Create efficiency score (lower processing time = higher score)
    ROUND(100 - (avg_processing_days / 365.0 * 100), 2) AS efficiency_score
FROM court_stats
ORDER BY efficiency_score DESC;