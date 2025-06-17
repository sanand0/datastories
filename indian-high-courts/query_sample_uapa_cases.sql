-- Sample UAPA Cases Extract
-- Petitioner name, judge name, date of bail plea, and respondent details

INSTALL httpfs; LOAD httpfs;
INSTALL parquet; LOAD parquet;

WITH combined AS (
    SELECT * FROM read_parquet('s3://indian-high-court-judgments/metadata/parquet/year=*/court=*/bench=*/metadata.parquet')
),
-- Identify UAPA cases and extract detailed information
uapa_sample_cases AS (
    SELECT 
        case_number,
        petitioner,
        respondent,
        judge_names,
        TRY_CAST(filing_date AS DATE) AS bail_plea_date,
        TRY_CAST(decision_date AS DATE) AS decision_date,
        court_name,
        subject_matter,
        keywords,
        case_type,
        -- Extract state from court name
        CASE 
            WHEN UPPER(court_name) LIKE '%DELHI%' THEN 'Delhi'
            WHEN UPPER(court_name) LIKE '%MUMBAI%' OR UPPER(court_name) LIKE '%BOMBAY%' THEN 'Maharashtra'
            WHEN UPPER(court_name) LIKE '%CALCUTTA%' THEN 'West Bengal'
            WHEN UPPER(court_name) LIKE '%MADRAS%' OR UPPER(court_name) LIKE '%CHENNAI%' THEN 'Tamil Nadu'
            WHEN UPPER(court_name) LIKE '%KARNATAKA%' OR UPPER(court_name) LIKE '%BANGALORE%' THEN 'Karnataka'
            WHEN UPPER(court_name) LIKE '%GUJARAT%' THEN 'Gujarat'
            WHEN UPPER(court_name) LIKE '%RAJASTHAN%' THEN 'Rajasthan'
            WHEN UPPER(court_name) LIKE '%PUNJAB%' THEN 'Punjab'
            WHEN UPPER(court_name) LIKE '%KERALA%' THEN 'Kerala'
            WHEN UPPER(court_name) LIKE '%ASSAM%' THEN 'Assam'
            WHEN UPPER(court_name) LIKE '%TELANGANA%' OR UPPER(court_name) LIKE '%HYDERABAD%' THEN 'Telangana'
            WHEN UPPER(court_name) LIKE '%ANDHRA%' THEN 'Andhra Pradesh'
            ELSE 'Other'
        END AS state,
        -- Extract petitioner name (clean up)
        TRIM(REGEXP_REPLACE(
            SPLIT_PART(SPLIT_PART(petitioner, ' vs ', 1), ' v. ', 1), 
            '\s+', ' ', 'g'
        )) AS petitioner_name,
        -- Extract respondent name (clean up)
        TRIM(REGEXP_REPLACE(
            CASE 
                WHEN petitioner LIKE '% vs %' THEN SPLIT_PART(petitioner, ' vs ', 2)
                WHEN petitioner LIKE '% v. %' THEN SPLIT_PART(petitioner, ' v. ', 2)
                ELSE respondent
            END,
            '\s+', ' ', 'g'
        )) AS respondent_name,
        -- Clean judge names
        TRIM(REGEXP_REPLACE(judge_names, '\s+', ' ', 'g')) AS judge_name,
        EXTRACT(YEAR FROM TRY_CAST(filing_date AS DATE)) AS filing_year
    FROM combined
    WHERE (
        -- Identify UAPA cases through multiple indicators
        UPPER(subject_matter) LIKE '%UAPA%' OR
        UPPER(subject_matter) LIKE '%UNLAWFUL ACTIVITIES%' OR
        UPPER(subject_matter) LIKE '%PREVENTION ACT%' OR
        UPPER(keywords) LIKE '%UAPA%' OR
        UPPER(keywords) LIKE '%UNLAWFUL ACTIVITIES%' OR
        UPPER(case_type) LIKE '%UAPA%' OR
        -- Identify bail-related cases with terror/sedition context
        (UPPER(subject_matter) LIKE '%BAIL%' AND (
            UPPER(subject_matter) LIKE '%TERROR%' OR
            UPPER(subject_matter) LIKE '%SEDITION%' OR
            UPPER(keywords) LIKE '%TERROR%' OR
            UPPER(keywords) LIKE '%SEDITION%'
        ))
    )
    AND (
        -- Focus on bail hearings
        UPPER(subject_matter) LIKE '%BAIL%' OR
        UPPER(case_type) LIKE '%BAIL%' OR
        UPPER(keywords) LIKE '%BAIL%'
    )
    AND NOT (
        -- Exclude facility/food/medical petitions
        UPPER(subject_matter) LIKE '%FOOD%' OR
        UPPER(subject_matter) LIKE '%MEDICAL%' OR
        UPPER(subject_matter) LIKE '%FACILITY%' OR
        UPPER(subject_matter) LIKE '%VISIT%' OR
        UPPER(keywords) LIKE '%FOOD%' OR
        UPPER(keywords) LIKE '%MEDICAL%'
    )
    AND TRY_CAST(filing_date AS DATE) IS NOT NULL
    AND TRY_CAST(filing_date AS DATE) >= '2019-01-01'  -- Focus on recent years
    AND petitioner IS NOT NULL
    AND LENGTH(TRIM(petitioner)) > 5
    AND judge_names IS NOT NULL
    AND LENGTH(TRIM(judge_names)) > 2
),
-- Clean and filter the sample
cleaned_sample AS (
    SELECT 
        case_number,
        petitioner_name,
        respondent_name,
        judge_name,
        bail_plea_date,
        decision_date,
        state,
        court_name,
        subject_matter,
        filing_year
    FROM uapa_sample_cases
    WHERE petitioner_name != ''
    AND LENGTH(petitioner_name) > 2
    AND LENGTH(petitioner_name) < 100  -- Exclude malformed entries
    AND respondent_name != ''
    AND LENGTH(respondent_name) > 2
    AND LENGTH(respondent_name) < 100
    AND judge_name != ''
    AND LENGTH(judge_name) > 5
    AND LENGTH(judge_name) < 200
    AND bail_plea_date IS NOT NULL
)
-- Final sample output
SELECT 
    case_number,
    petitioner_name,
    respondent_name,
    judge_name,
    bail_plea_date,
    decision_date,
    state,
    court_name,
    SUBSTRING(subject_matter, 1, 100) as subject_matter_summary,
    filing_year
FROM cleaned_sample
ORDER BY bail_plea_date DESC, state, case_number
LIMIT 100;