-- Query 3: Geographic Disparities in Case Processing
-- Digital Divide in Justice: Metro vs Non-Metro High Courts

INSTALL httpfs; LOAD httpfs;
INSTALL parquet; LOAD parquet;

WITH combined AS (
    SELECT * FROM read_parquet('s3://indian-high-court-judgments/metadata/parquet/year=*/court=*/bench=*/metadata.parquet')
),
-- Classify courts as Metro/Non-Metro (based on typical classifications)
court_classification AS (
    SELECT 
        court_name,
        CASE 
            WHEN UPPER(court_name) LIKE '%DELHI%' OR
                 UPPER(court_name) LIKE '%MUMBAI%' OR
                 UPPER(court_name) LIKE '%BOMBAY%' OR
                 UPPER(court_name) LIKE '%CALCUTTA%' OR
                 UPPER(court_name) LIKE '%MADRAS%' OR
                 UPPER(court_name) LIKE '%CHENNAI%' OR
                 UPPER(court_name) LIKE '%BANGALORE%' OR
                 UPPER(court_name) LIKE '%KARNATAKA%' OR
                 UPPER(court_name) LIKE '%HYDERABAD%' OR
                 UPPER(court_name) LIKE '%TELANGANA%' OR
                 UPPER(court_name) LIKE '%ANDHRA%' OR
                 UPPER(court_name) LIKE '%GUJARAT%' OR
                 UPPER(court_name) LIKE '%PUNE%'
            THEN 'Metro'
            ELSE 'Non-Metro'
        END AS court_category
    FROM (SELECT DISTINCT court_name FROM combined) c
),
processed_cases AS (
    SELECT 
        c.court_name,
        cc.court_category,
        TRY_CAST(c.decision_date AS DATE) AS decision_date,
        TRY_CAST(c.filing_date AS DATE) AS filing_date,
        c.case_type,
        c.case_number,
        CASE 
            WHEN TRY_CAST(c.decision_date AS DATE) IS NOT NULL 
            AND TRY_CAST(c.filing_date AS DATE) IS NOT NULL
            THEN DATE_DIFF('day', TRY_CAST(c.filing_date AS DATE), TRY_CAST(c.decision_date AS DATE))
        END AS processing_days,
        EXTRACT(YEAR FROM TRY_CAST(c.decision_date AS DATE)) AS decision_year
    FROM combined c
    JOIN court_classification cc ON c.court_name = cc.court_name
    WHERE TRY_CAST(c.decision_date AS DATE) IS NOT NULL
    AND TRY_CAST(c.filing_date AS DATE) IS NOT NULL
    AND TRY_CAST(c.decision_date AS DATE) >= '2020-01-01'
),
geographic_stats AS (
    SELECT 
        court_category,
        COUNT(DISTINCT court_name) AS num_courts,
        COUNT(*) AS total_cases,
        AVG(processing_days) AS avg_processing_days,
        MEDIAN(processing_days) AS median_processing_days,
        -- Case disposal efficiency metrics
        SUM(CASE WHEN processing_days <= 90 THEN 1 ELSE 0 END) AS cases_within_90_days,
        SUM(CASE WHEN processing_days <= 365 THEN 1 ELSE 0 END) AS cases_within_1_year,
        SUM(CASE WHEN processing_days > 365 THEN 1 ELSE 0 END) AS cases_over_1_year,
        -- Annual case volume
        COUNT(*) / COUNT(DISTINCT decision_year) AS avg_annual_cases,
        -- Case type diversity
        COUNT(DISTINCT case_type) AS case_type_diversity
    FROM processed_cases
    GROUP BY court_category
),
yearly_trends AS (
    SELECT 
        court_category,
        decision_year,
        COUNT(*) AS annual_cases,
        AVG(processing_days) AS avg_processing_days,
        LAG(COUNT(*), 1) OVER (PARTITION BY court_category ORDER BY decision_year) AS prev_year_cases
    FROM processed_cases
    GROUP BY court_category, decision_year
),
efficiency_comparison AS (
    SELECT 
        court_category,
        total_cases,
        ROUND(avg_processing_days, 2) AS avg_processing_days,
        median_processing_days,
        ROUND((cases_within_90_days * 100.0 / total_cases), 2) AS pct_resolved_90_days,
        ROUND((cases_within_1_year * 100.0 / total_cases), 2) AS pct_resolved_1_year,
        ROUND((cases_over_1_year * 100.0 / total_cases), 2) AS pct_backlog_over_1_year,
        ROUND(avg_annual_cases / num_courts, 0) AS avg_cases_per_court,
        case_type_diversity
    FROM geographic_stats
)
SELECT 
    court_category,
    total_cases,
    avg_processing_days,
    median_processing_days,
    pct_resolved_90_days,
    pct_resolved_1_year,
    pct_backlog_over_1_year,
    avg_cases_per_court,
    case_type_diversity,
    -- Calculate efficiency gap
    avg_processing_days - (SELECT MIN(avg_processing_days) FROM efficiency_comparison) AS efficiency_gap_days
FROM efficiency_comparison
ORDER BY pct_resolved_90_days DESC;