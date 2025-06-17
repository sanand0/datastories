-- Query 4: Constitutional Cases Surge Analysis
-- Tracking Fundamental Rights Litigation Trends

INSTALL httpfs; LOAD httpfs;
INSTALL parquet; LOAD parquet;

WITH combined AS (
    SELECT * FROM read_parquet('s3://indian-high-court-judgments/metadata/parquet/year=*/court=*/bench=*/metadata.parquet')
),
constitutional_cases AS (
    SELECT 
        *,
        TRY_CAST(filing_date AS DATE) AS filing_date_parsed,
        TRY_CAST(decision_date AS DATE) AS decision_date_parsed,
        EXTRACT(YEAR FROM TRY_CAST(filing_date AS DATE)) AS filing_year,
        EXTRACT(MONTH FROM TRY_CAST(filing_date AS DATE)) AS filing_month,
        -- Identify constitutional cases through multiple indicators
        CASE 
            WHEN UPPER(case_type) LIKE '%WRIT%' OR
                 UPPER(case_type) LIKE '%CONSTITUTIONAL%' OR
                 UPPER(case_type) LIKE '%HABEAS%' OR
                 UPPER(case_type) LIKE '%MANDAMUS%' OR
                 UPPER(case_type) LIKE '%CERTIORARI%' OR
                 UPPER(case_type) LIKE '%PROHIBITION%' OR
                 UPPER(case_type) LIKE '%QUO WARRANTO%' OR
                 UPPER(subject_matter) LIKE '%FUNDAMENTAL RIGHTS%' OR
                 UPPER(subject_matter) LIKE '%ARTICLE 14%' OR
                 UPPER(subject_matter) LIKE '%ARTICLE 19%' OR
                 UPPER(subject_matter) LIKE '%ARTICLE 21%' OR
                 UPPER(keywords) LIKE '%CONSTITUTIONAL%' OR
                 UPPER(keywords) LIKE '%FUNDAMENTAL RIGHTS%'
            THEN 'Constitutional'
            ELSE 'Non-Constitutional'
        END AS case_category,
        -- Further classify constitutional cases by rights type
        CASE 
            WHEN UPPER(subject_matter) LIKE '%ARTICLE 14%' OR UPPER(keywords) LIKE '%EQUALITY%' 
                THEN 'Right to Equality'
            WHEN UPPER(subject_matter) LIKE '%ARTICLE 19%' OR UPPER(keywords) LIKE '%FREEDOM%' 
                THEN 'Freedom Rights'
            WHEN UPPER(subject_matter) LIKE '%ARTICLE 21%' OR UPPER(keywords) LIKE '%LIFE%' OR UPPER(keywords) LIKE '%LIBERTY%'
                THEN 'Right to Life & Liberty'
            WHEN UPPER(subject_matter) LIKE '%ARTICLE 32%' OR UPPER(keywords) LIKE '%CONSTITUTIONAL REMEDY%'
                THEN 'Right to Constitutional Remedies'
            WHEN UPPER(subject_matter) LIKE '%RELIGIOUS%' OR UPPER(keywords) LIKE '%RELIGION%'
                THEN 'Right to Religious Freedom'
            WHEN UPPER(subject_matter) LIKE '%EDUCATION%' OR UPPER(keywords) LIKE '%CULTURAL%'
                THEN 'Educational & Cultural Rights'
            ELSE 'Other Constitutional'
        END AS rights_category
    FROM combined
    WHERE TRY_CAST(filing_date AS DATE) IS NOT NULL
    AND TRY_CAST(filing_date AS DATE) >= '2015-01-01'
),
yearly_trends AS (
    SELECT 
        filing_year,
        case_category,
        COUNT(*) AS cases_filed,
        COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY filing_year) AS pct_of_total_cases
    FROM constitutional_cases
    GROUP BY filing_year, case_category
),
constitutional_trends AS (
    SELECT 
        filing_year,
        rights_category,
        COUNT(*) AS cases_count,
        AVG(CASE 
            WHEN decision_date_parsed IS NOT NULL AND filing_date_parsed IS NOT NULL
            THEN DATE_DIFF('day', filing_date_parsed, decision_date_parsed)
        END) AS avg_resolution_days
    FROM constitutional_cases
    WHERE case_category = 'Constitutional'
    GROUP BY filing_year, rights_category
),
court_wise_constitutional AS (
    SELECT 
        court_name,
        COUNT(*) AS total_constitutional_cases,
        COUNT(*) * 100.0 / (SELECT COUNT(*) FROM constitutional_cases WHERE case_category = 'Constitutional') AS pct_of_national_constitutional,
        AVG(CASE 
            WHEN decision_date_parsed IS NOT NULL AND filing_date_parsed IS NOT NULL
            THEN DATE_DIFF('day', filing_date_parsed, decision_date_parsed)
        END) AS avg_constitutional_resolution_days
    FROM constitutional_cases
    WHERE case_category = 'Constitutional'
    GROUP BY court_name
),
-- Analyze spikes in constitutional cases (potential correlation with major events)
monthly_constitutional AS (
    SELECT 
        filing_year,
        filing_month,
        COUNT(*) AS monthly_constitutional_cases,
        AVG(COUNT(*)) OVER (PARTITION BY filing_year ORDER BY filing_month ROWS BETWEEN 2 PRECEDING AND 2 FOLLOWING) AS rolling_avg
    FROM constitutional_cases
    WHERE case_category = 'Constitutional'
    GROUP BY filing_year, filing_month
)
-- Main output: Comprehensive constitutional case analysis
SELECT 
    'Yearly_Trends' as analysis_type,
    CAST(filing_year AS VARCHAR) as period,
    CAST(SUM(CASE WHEN case_category = 'Constitutional' THEN cases_filed ELSE 0 END) AS VARCHAR) as constitutional_cases,
    CAST(ROUND(SUM(CASE WHEN case_category = 'Constitutional' THEN pct_of_total_cases ELSE 0 END), 2) AS VARCHAR) as pct_of_total,
    '' as additional_info
FROM yearly_trends
GROUP BY filing_year
UNION ALL
SELECT 
    'Rights_Category_Distribution' as analysis_type,
    rights_category as period,
    CAST(SUM(cases_count) AS VARCHAR) as constitutional_cases,
    CAST(ROUND(AVG(avg_resolution_days), 2) AS VARCHAR) as pct_of_total,
    'avg_resolution_days' as additional_info
FROM constitutional_trends
GROUP BY rights_category
UNION ALL
SELECT 
    'Top_Courts' as analysis_type,
    court_name as period,
    CAST(total_constitutional_cases AS VARCHAR) as constitutional_cases,
    CAST(ROUND(pct_of_national_constitutional, 2) AS VARCHAR) as pct_of_total,
    CAST(ROUND(avg_constitutional_resolution_days, 2) AS VARCHAR) as additional_info
FROM court_wise_constitutional
WHERE total_constitutional_cases > 1000  -- Focus on courts with significant constitutional caseload
ORDER BY analysis_type, CAST(constitutional_cases AS INTEGER) DESC;