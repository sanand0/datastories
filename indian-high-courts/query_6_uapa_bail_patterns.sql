-- Query 6: UAPA Bail Denial Patterns Analysis
-- Systematic Delays in Terror Cases - Tracking Individual Accused Through Multiple Hearings

INSTALL httpfs; LOAD httpfs;
INSTALL parquet; LOAD parquet;

WITH combined AS (
    SELECT * FROM read_parquet('s3://indian-high-court-judgments/metadata/parquet/year=*/court=*/bench=*/metadata.parquet')
),
-- Identify UAPA cases and extract accused names
uapa_cases AS (
    SELECT 
        *,
        TRY_CAST(decision_date AS DATE) AS decision_date_parsed,
        TRY_CAST(filing_date AS DATE) AS filing_date_parsed,
        EXTRACT(YEAR FROM TRY_CAST(decision_date AS DATE)) AS decision_year,
        EXTRACT(YEAR FROM TRY_CAST(filing_date AS DATE)) AS filing_year,
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
        -- Extract petitioner/accused names (first name before 'vs' or 'v.')
        TRIM(SPLIT_PART(SPLIT_PART(petitioner, ' vs ', 1), ' v. ', 1)) AS accused_name
    FROM combined
    WHERE (
        -- Identify UAPA cases through multiple indicators
        UPPER(subject_matter) LIKE '%UAPA%' OR
        UPPER(subject_matter) LIKE '%UNLAWFUL ACTIVITIES%' OR
        UPPER(subject_matter) LIKE '%PREVENTION ACT%' OR
        UPPER(keywords) LIKE '%UAPA%' OR
        UPPER(keywords) LIKE '%UNLAWFUL ACTIVITIES%' OR
        UPPER(case_type) LIKE '%UAPA%' OR
        -- Identify bail-related cases
        (UPPER(subject_matter) LIKE '%BAIL%' AND (
            UPPER(subject_matter) LIKE '%TERROR%' OR
            UPPER(subject_matter) LIKE '%SEDITION%' OR
            UPPER(keywords) LIKE '%TERROR%' OR
            UPPER(keywords) LIKE '%SEDITION%'
        ))
    )
    AND (
        -- Focus on bail hearings, exclude unrelated petitions
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
    AND TRY_CAST(decision_date AS DATE) IS NOT NULL
    AND TRY_CAST(decision_date AS DATE) >= '2019-01-01'  -- Focus on recent years
    AND accused_name IS NOT NULL
    AND LENGTH(accused_name) > 2
),
-- Determine bail outcomes from judgment text/keywords
bail_outcomes AS (
    SELECT 
        *,
        CASE 
            WHEN UPPER(subject_matter) LIKE '%BAIL GRANTED%' OR 
                 UPPER(keywords) LIKE '%BAIL GRANTED%' OR
                 UPPER(subject_matter) LIKE '%BAIL ALLOWED%' THEN 'Granted'
            WHEN UPPER(subject_matter) LIKE '%BAIL REJECTED%' OR 
                 UPPER(keywords) LIKE '%BAIL REJECTED%' OR
                 UPPER(subject_matter) LIKE '%BAIL DENIED%' OR
                 UPPER(subject_matter) LIKE '%BAIL DISMISSED%' THEN 'Denied'
            WHEN UPPER(subject_matter) LIKE '%ADJOURNED%' OR 
                 UPPER(keywords) LIKE '%ADJOURNED%' OR
                 UPPER(subject_matter) LIKE '%POSTPONED%' OR
                 UPPER(subject_matter) LIKE '%NEXT DATE%' THEN 'Postponed'
            ELSE 'Unknown'
        END AS bail_outcome
    FROM uapa_cases
),
-- Create sequence of hearings for each accused
hearing_sequences AS (
    SELECT 
        accused_name,
        state,
        decision_year,
        decision_date_parsed,
        bail_outcome,
        case_number,
        court_name,
        -- Create hearing sequence number for each accused
        ROW_NUMBER() OVER (
            PARTITION BY accused_name, state 
            ORDER BY decision_date_parsed
        ) AS hearing_sequence,
        -- Calculate days between consecutive hearings
        LAG(decision_date_parsed, 1) OVER (
            PARTITION BY accused_name, state 
            ORDER BY decision_date_parsed
        ) AS prev_hearing_date
    FROM bail_outcomes
    WHERE accused_name != ''
),
hearing_gaps AS (
    SELECT 
        *,
        CASE 
            WHEN prev_hearing_date IS NOT NULL 
            THEN DATE_DIFF('day', prev_hearing_date, decision_date_parsed)
            ELSE NULL
        END AS days_between_hearings
    FROM hearing_sequences
),
-- Analyze patterns by accused individual
accused_patterns AS (
    SELECT 
        accused_name,
        state,
        MIN(decision_year) AS first_hearing_year,
        MAX(decision_year) AS last_hearing_year,
        COUNT(*) AS total_hearings,
        MAX(hearing_sequence) AS max_sequence,
        AVG(days_between_hearings) AS avg_days_between_hearings,
        MIN(days_between_hearings) AS min_days_between_hearings,
        MAX(days_between_hearings) AS max_days_between_hearings,
        -- Count outcomes
        SUM(CASE WHEN bail_outcome = 'Granted' THEN 1 ELSE 0 END) AS bail_granted_count,
        SUM(CASE WHEN bail_outcome = 'Denied' THEN 1 ELSE 0 END) AS bail_denied_count,
        SUM(CASE WHEN bail_outcome = 'Postponed' THEN 1 ELSE 0 END) AS bail_postponed_count,
        -- Calculate case duration
        DATE_DIFF('day', MIN(decision_date_parsed), MAX(decision_date_parsed)) AS case_duration_days,
        -- Final outcome
        LAST_VALUE(bail_outcome) OVER (
            PARTITION BY accused_name, state 
            ORDER BY decision_date_parsed 
            ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
        ) AS final_outcome
    FROM hearing_gaps
    GROUP BY accused_name, state
),
-- State-wise and year-wise patterns
state_year_patterns AS (
    SELECT 
        state,
        decision_year,
        COUNT(DISTINCT accused_name) AS unique_accused,
        COUNT(*) AS total_hearings,
        AVG(days_between_hearings) AS avg_hearing_gap_days,
        SUM(CASE WHEN bail_outcome = 'Granted' THEN 1 ELSE 0 END) AS total_granted,
        SUM(CASE WHEN bail_outcome = 'Denied' THEN 1 ELSE 0 END) AS total_denied,
        SUM(CASE WHEN bail_outcome = 'Postponed' THEN 1 ELSE 0 END) AS total_postponed,
        -- Calculate bail grant rate
        ROUND(
            SUM(CASE WHEN bail_outcome = 'Granted' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2
        ) AS bail_grant_rate_pct
    FROM hearing_gaps
    GROUP BY state, decision_year
)
-- Main output: Individual accused hearing sequences
SELECT 
    'Individual_Accused_Patterns' as analysis_type,
    accused_name,
    state,
    CAST(total_hearings AS VARCHAR) as hearing_count,
    CAST(ROUND(avg_days_between_hearings, 1) AS VARCHAR) as avg_gap_days,
    final_outcome,
    CAST(case_duration_days AS VARCHAR) as total_case_days,
    CAST(first_hearing_year AS VARCHAR) as start_year
FROM accused_patterns
WHERE total_hearings >= 3  -- Focus on cases with multiple hearings
UNION ALL
SELECT 
    'State_Year_Summary' as analysis_type,
    state as accused_name,
    CAST(decision_year AS VARCHAR) as state,
    CAST(total_hearings AS VARCHAR) as hearing_count,
    CAST(ROUND(avg_hearing_gap_days, 1) AS VARCHAR) as avg_gap_days,
    CAST(bail_grant_rate_pct AS VARCHAR) as final_outcome,
    CAST(unique_accused AS VARCHAR) as total_case_days,
    CAST(total_postponed AS VARCHAR) as start_year
FROM state_year_patterns
ORDER BY analysis_type, accused_name, state;