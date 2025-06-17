-- Query 2: Seasonal Justice Analysis
-- How Court Vacation Periods Affect Case Resolution

INSTALL httpfs; LOAD httpfs;
INSTALL parquet; LOAD parquet;

WITH combined AS (
    SELECT * FROM read_parquet('s3://indian-high-court-judgments/metadata/parquet/year=*/court=*/bench=*/metadata.parquet')
),
seasonal_data AS (
    SELECT 
        TRY_CAST(decision_date AS DATE) AS decision_date,
        court_name,
        case_number,
        EXTRACT(YEAR FROM TRY_CAST(decision_date AS DATE)) AS decision_year,
        EXTRACT(MONTH FROM TRY_CAST(decision_date AS DATE)) AS decision_month,
        EXTRACT(DOW FROM TRY_CAST(decision_date AS DATE)) AS day_of_week,
        -- Classify months by vacation periods (typical Indian court calendar)
        CASE 
            WHEN EXTRACT(MONTH FROM TRY_CAST(decision_date AS DATE)) IN (12, 1) THEN 'Winter_Vacation'
            WHEN EXTRACT(MONTH FROM TRY_CAST(decision_date AS DATE)) IN (5, 6) THEN 'Summer_Vacation'
            WHEN EXTRACT(MONTH FROM TRY_CAST(decision_date AS DATE)) IN (10) THEN 'Puja_Vacation'
            ELSE 'Regular_Period'
        END AS vacation_period,
        -- Classify by quarter
        CASE 
            WHEN EXTRACT(MONTH FROM TRY_CAST(decision_date AS DATE)) IN (1,2,3) THEN 'Q1'
            WHEN EXTRACT(MONTH FROM TRY_CAST(decision_date AS DATE)) IN (4,5,6) THEN 'Q2'
            WHEN EXTRACT(MONTH FROM TRY_CAST(decision_date AS DATE)) IN (7,8,9) THEN 'Q3'
            WHEN EXTRACT(MONTH FROM TRY_CAST(decision_date AS DATE)) IN (10,11,12) THEN 'Q4'
        END AS quarter
    FROM combined
    WHERE TRY_CAST(decision_date AS DATE) IS NOT NULL
    AND TRY_CAST(decision_date AS DATE) >= '2020-01-01'
),
monthly_stats AS (
    SELECT 
        decision_year,
        decision_month,
        vacation_period,
        COUNT(*) AS judgments_delivered,
        COUNT(*) / 
            (SELECT COUNT(*) FROM seasonal_data WHERE decision_year = s.decision_year) * 100 
            AS pct_of_annual_judgments
    FROM seasonal_data s
    GROUP BY decision_year, decision_month, vacation_period
),
vacation_impact AS (
    SELECT 
        vacation_period,
        COUNT(*) AS total_judgments,
        AVG(judgments_delivered) AS avg_monthly_judgments,
        STDDEV(judgments_delivered) AS stddev_monthly_judgments
    FROM monthly_stats
    GROUP BY vacation_period
),
-- Analysis of pre and post vacation periods
vacation_spillover AS (
    SELECT 
        decision_year,
        decision_month,
        vacation_period,
        judgments_delivered,
        -- Compare with previous month
        LAG(judgments_delivered, 1) OVER (PARTITION BY decision_year ORDER BY decision_month) AS prev_month_judgments,
        -- Compare with next month  
        LEAD(judgments_delivered, 1) OVER (PARTITION BY decision_year ORDER BY decision_month) AS next_month_judgments
    FROM monthly_stats
)
SELECT 
    'Monthly_Distribution' as analysis_type,
    CAST(decision_month AS VARCHAR) as period,
    CAST(AVG(judgments_delivered) AS INTEGER) as avg_judgments,
    CAST(STDDEV(judgments_delivered) AS INTEGER) as stddev_judgments,
    vacation_period
FROM monthly_stats
GROUP BY decision_month, vacation_period
UNION ALL
SELECT 
    'Vacation_Impact' as analysis_type,
    vacation_period as period,
    CAST(avg_monthly_judgments AS INTEGER) as avg_judgments,
    CAST(stddev_monthly_judgments AS INTEGER) as stddev_judgments,
    vacation_period
FROM vacation_impact
ORDER BY analysis_type, period;