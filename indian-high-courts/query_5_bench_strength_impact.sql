-- Query 5: Bench Strength Impact Analysis
-- How Judge Availability Affects Case Disposal

INSTALL httpfs; LOAD httpfs;
INSTALL parquet; LOAD parquet;

WITH combined AS (
    SELECT * FROM read_parquet('s3://indian-high-court-judgments/metadata/parquet/year=*/court=*/bench=*/metadata.parquet')
),
-- Extract judge information and count active judges per bench
judge_analysis AS (
    SELECT 
        court_name,
        bench_name,
        judge_names,
        TRY_CAST(decision_date AS DATE) AS decision_date,
        TRY_CAST(filing_date AS DATE) AS filing_date,
        case_number,
        EXTRACT(YEAR FROM TRY_CAST(decision_date AS DATE)) AS decision_year,
        EXTRACT(MONTH FROM TRY_CAST(decision_date AS DATE)) AS decision_month,
        -- Estimate number of judges from judge_names field
        CASE 
            WHEN judge_names IS NULL OR judge_names = '' THEN 1
            WHEN REGEXP_MATCHES(judge_names, '\sand\s|\s&\s|,', 'gi') THEN 
                CARDINALITY(STRING_SPLIT(REGEXP_REPLACE(judge_names, '\sand\s|\s&\s', ',', 'gi'), ','))
            ELSE 1
        END AS estimated_judges_count,
        -- Classify by bench type
        CASE 
            WHEN estimated_judges_count = 1 THEN 'Single_Judge'
            WHEN estimated_judges_count = 2 THEN 'Division_Bench'
            WHEN estimated_judges_count >= 3 THEN 'Full_Bench'
            ELSE 'Unknown'
        END AS bench_type,
        CASE 
            WHEN TRY_CAST(decision_date AS DATE) IS NOT NULL 
            AND TRY_CAST(filing_date AS DATE) IS NOT NULL
            THEN DATE_DIFF('day', TRY_CAST(filing_date AS DATE), TRY_CAST(decision_date AS DATE))
        END AS processing_days
    FROM combined
    WHERE TRY_CAST(decision_date AS DATE) IS NOT NULL
    AND TRY_CAST(decision_date AS DATE) >= '2020-01-01'
),
-- Calculate bench productivity metrics
bench_productivity AS (
    SELECT 
        court_name,
        bench_name,
        bench_type,
        decision_year,
        decision_month,
        AVG(estimated_judges_count) AS avg_judges_per_case,
        COUNT(*) AS cases_disposed,
        AVG(processing_days) AS avg_processing_days,
        MEDIAN(processing_days) AS median_processing_days
    FROM judge_analysis
    WHERE processing_days IS NOT NULL
    GROUP BY court_name, bench_name, bench_type, decision_year, decision_month
),
-- Court-level judge strength analysis
court_judge_strength AS (
    SELECT 
        court_name,
        decision_year,
        -- Estimate active judges (unique benches * average judges per bench)
        COUNT(DISTINCT bench_name) AS active_benches,
        AVG(avg_judges_per_case) AS avg_judges_per_bench,
        COUNT(DISTINCT bench_name) * AVG(avg_judges_per_case) AS estimated_total_judges,
        SUM(cases_disposed) AS total_cases_disposed,
        AVG(avg_processing_days) AS court_avg_processing_days,
        -- Calculate productivity per judge
        SUM(cases_disposed) / (COUNT(DISTINCT bench_name) * AVG(avg_judges_per_case)) AS cases_per_judge_per_year
    FROM bench_productivity
    GROUP BY court_name, decision_year
),
-- Bench type performance comparison
bench_type_performance AS (
    SELECT 
        bench_type,
        COUNT(*) AS total_cases,
        AVG(cases_disposed) AS avg_monthly_cases,
        AVG(avg_processing_days) AS avg_processing_days,
        STDDEV(avg_processing_days) AS stddev_processing_days,
        -- Cases per judge efficiency
        AVG(cases_disposed / avg_judges_per_case) AS cases_per_judge_per_month
    FROM bench_productivity
    GROUP BY bench_type
),
-- Correlation analysis between judge strength and efficiency
efficiency_correlation AS (
    SELECT 
        court_name,
        decision_year,
        estimated_total_judges,
        total_cases_disposed,
        cases_per_judge_per_year,
        court_avg_processing_days,
        -- Rank courts by efficiency metrics
        ROW_NUMBER() OVER (PARTITION BY decision_year ORDER BY cases_per_judge_per_year DESC) as efficiency_rank,
        ROW_NUMBER() OVER (PARTITION BY decision_year ORDER BY court_avg_processing_days ASC) as speed_rank
    FROM court_judge_strength
    WHERE estimated_total_judges > 5  -- Focus on courts with reasonable judge strength
)
-- Main output combining all analyses
SELECT 
    'Court_Judge_Strength' as analysis_type,
    court_name as entity,
    CAST(ROUND(AVG(estimated_total_judges), 1) AS VARCHAR) as avg_judges,
    CAST(ROUND(AVG(cases_per_judge_per_year), 0) AS VARCHAR) as cases_per_judge_year,
    CAST(ROUND(AVG(court_avg_processing_days), 2) AS VARCHAR) as avg_processing_days,
    CAST(ROUND(AVG(efficiency_rank), 1) AS VARCHAR) as avg_efficiency_rank
FROM efficiency_correlation
GROUP BY court_name
UNION ALL
SELECT 
    'Bench_Type_Performance' as analysis_type,
    bench_type as entity,
    CAST(total_cases AS VARCHAR) as avg_judges,
    CAST(ROUND(cases_per_judge_per_month, 1) AS VARCHAR) as cases_per_judge_year,
    CAST(ROUND(avg_processing_days, 2) AS VARCHAR) as avg_processing_days,
    CAST(ROUND(stddev_processing_days, 2) AS VARCHAR) as avg_efficiency_rank
FROM bench_type_performance
UNION ALL
SELECT 
    'Top_Efficient_Courts' as analysis_type,
    court_name as entity,
    CAST(estimated_total_judges AS VARCHAR) as avg_judges,
    CAST(cases_per_judge_per_year AS VARCHAR) as cases_per_judge_year,
    CAST(ROUND(court_avg_processing_days, 2) AS VARCHAR) as avg_processing_days,
    CAST(efficiency_rank AS VARCHAR) as avg_efficiency_rank
FROM efficiency_correlation
WHERE decision_year = (SELECT MAX(decision_year) FROM efficiency_correlation)
AND efficiency_rank <= 10
ORDER BY analysis_type, entity;