# Indian High Court Judgments

This story explores the dataset of Indian High Court judgments downloaded from the [ecourts website](https://judgments.ecourts.gov.in/). Files are hosted on S3 in separate folders for PDF content and metadata.

## Data layout

```
* data/pdf/year=2025/court=xyz/bench=xyz/judgment1.pdf
* metadata/json/year=2025/court=xyz/bench=xyz/judgment1.json
* metadata/parquet/year=2025/court=xyz/bench=xyz/metadata.parquet
* metadata/tar/year=2025/court=xyz/bench=xyz/metadata.tar.gz
* data/tar/year=2025/court=xyz/bench=xyz/pdfs.tar
```

`court` is the high court code and `bench` is its subdivision. The parquet files have one row per judgment. The dataset spans **25 high courts**, about **16 million** judgments and roughly **1TB** of compressed data.

## Columns

The parquet files share a common structure. A sample file contains these columns:

| column_name | column_type |
|-------------|-------------|
| court_code | VARCHAR |
| title | VARCHAR |
| description | VARCHAR |
| judge | VARCHAR |
| pdf_link | VARCHAR |
| cnr | VARCHAR |
| date_of_registration | VARCHAR |
| decision_date | DATE |
| disposal_nature | VARCHAR |
| court | VARCHAR |
| raw_html | VARCHAR |

The sample used for exploration contains **13,974** rows from the Madras High Court with decision dates between **2025‑01‑04** and **2025‑12‑03**.

## Exploratory data analysis

Basic summaries are provided below. Full CSV outputs are in this folder.

### Decision dates by month
```sql
COPY (
SELECT strftime(decision_date, '%Y-%m') AS month, COUNT(*) AS total
FROM read_parquet('/tmp/metadata1.parquet')
GROUP BY month
ORDER BY month
) TO 'monthly_counts.csv' WITH (HEADER, DELIMITER ',');
```
Result: [monthly_counts.csv](monthly_counts.csv)

### Top case types
```sql
COPY (
SELECT regexp_extract(title, '^(\\w+)', 1) AS type, COUNT(*) AS total
FROM read_parquet('/tmp/metadata1.parquet')
GROUP BY type
ORDER BY total DESC
LIMIT 10
) TO 'top_case_types.csv' WITH (HEADER, DELIMITER ',');
```
Result: [top_case_types.csv](top_case_types.csv)

### Disposal nature
```sql
COPY (
SELECT disposal_nature, COUNT(*) AS total
FROM read_parquet('/tmp/metadata1.parquet')
GROUP BY disposal_nature
ORDER BY total DESC
LIMIT 5
) TO 'top_disposals.csv' WITH (HEADER, DELIMITER ',');
```
Result: [top_disposals.csv](top_disposals.csv)

### Most frequent judges
```sql
COPY (
SELECT judge, COUNT(*) AS total
FROM read_parquet('/tmp/metadata1.parquet')
GROUP BY judge
ORDER BY total DESC
LIMIT 5
) TO 'top_judges.csv' WITH (HEADER, DELIMITER ',');
```
Result: [top_judges.csv](top_judges.csv)

### Filing to decision days
```sql
COPY (
SELECT MIN(days) AS min, QUANTILE_CONT(days, 0.25) AS q1, MEDIAN(days) AS median,
       QUANTILE_CONT(days, 0.75) AS q3, MAX(days) AS max, AVG(days) AS mean
FROM (
  SELECT DATEDIFF('day', STRPTIME(date_of_registration, '%d-%m-%Y'), decision_date) AS days
  FROM read_parquet('/tmp/metadata1.parquet')
)
) TO 'days_stats.csv' WITH (HEADER, DELIMITER ',');
```
Result: [days_stats.csv](days_stats.csv)


## Questions answered with SQL

The queries below use the 2025 Madras sample. Each result links to a CSV in this directory.

### 1. Which High Courts reversed the highest share of lower-court convictions in criminal appeals during 2025, and did any judge stand out?
Why it matters: The Supreme Court has warned High Courts about delays and inconsistency in criminal appeals.

Answer: In the sample **51%** of criminal appeals were reversed in the Madras High Court. Justice Sunder Mohan allowed **19** of **23** such appeals.
```sql
COPY (
WITH data AS (
  SELECT * FROM read_parquet('/tmp/metadata1.parquet')
  UNION ALL
  SELECT * FROM read_parquet('/tmp/metadata2.parquet')
)
SELECT court,
       COUNT(*) FILTER (WHERE title LIKE '%CRL A%' OR title LIKE '%CRL APPEAL%') AS total_crl_appeals,
       COUNT(*) FILTER (WHERE (title LIKE '%CRL A%' OR title LIKE '%CRL APPEAL%') AND disposal_nature IN ('ALLOWED','PARTLY ALLOWED')) AS reversals,
       ROUND(100.0 * COUNT(*) FILTER (WHERE (title LIKE '%CRL A%' OR title LIKE '%CRL APPEAL%') AND disposal_nature IN ('ALLOWED','PARTLY ALLOWED')) /
             NULLIF(COUNT(*) FILTER (WHERE title LIKE '%CRL A%' OR title LIKE '%CRL APPEAL%'),0),2) AS reversal_pct
FROM data
GROUP BY court
) TO 'q11.csv' WITH (HEADER, DELIMITER ',');
```
Result: [q11.csv](q11.csv), [q11_judges.csv](q11_judges.csv)

### 2. How often did each High Court dispose of criminal bail, anticipatory bail, and habeas corpus matters within 30 days?
Why it matters: Bail pendency is under the spotlight, yet only 15 judges per million serve India.

Answer: Only habeas corpus cases appear in the sample. **33%** were resolved within 30 days.
```sql
COPY (
WITH data AS (
  SELECT * FROM read_parquet('/tmp/metadata1.parquet')
  UNION ALL
  SELECT * FROM read_parquet('/tmp/metadata2.parquet')
),
filtered AS (
  SELECT court,
         CASE
           WHEN upper(title) LIKE 'CRM BA%' THEN 'CRM_BA'
           WHEN upper(title) LIKE 'ABA%' THEN 'ABA'
           WHEN upper(title) LIKE 'HCP%' THEN 'HCP'
         END AS kind,
         DATEDIFF('day', STRPTIME(date_of_registration,'%d-%m-%Y'), decision_date) AS days
  FROM data
  WHERE upper(title) LIKE 'CRM BA%' OR upper(title) LIKE 'ABA%' OR upper(title) LIKE 'HCP%'
)
SELECT court, kind, COUNT(*) AS total,
       COUNT(*) FILTER (WHERE days <= 30) AS within_30,
       ROUND(100.0 * COUNT(*) FILTER (WHERE days <= 30)/COUNT(*),2) AS pct_within_30
FROM filtered
GROUP BY court, kind
ORDER BY court, kind
) TO 'q12.csv' WITH (HEADER, DELIMITER ',');
```
Result: [q12.csv](q12.csv)

### 3. Are writ petitions invoking Article 226 on environmental issues rising, and which benches grant relief most often?
Why it matters: Article 226 petitions can delay infrastructure projects.

Answer: No 2025 Madras cases mention Article 226 alongside forest, mining or pollution terms, so no trend is visible.
```sql
-- zero rows matched, so a placeholder CSV was created
```
Result: [q13.csv](q13.csv)

### 4. Which courts most rely on compromise/settled disposals, and do counts spike around National Lok Adalat dates?
Why it matters: Over 3 crore cases were settled in the 2025 National Lok Adalat.

Answer: Fourteen Madras cases used compromise language with a small peak in April.
```sql
COPY (
WITH data AS (
  SELECT * FROM read_parquet('/tmp/metadata1.parquet')
  UNION ALL
  SELECT * FROM read_parquet('/tmp/metadata2.parquet')
)
SELECT court, strftime(decision_date,'%Y-%W') AS week, COUNT(*) AS total
FROM data
WHERE lower(disposal_nature) LIKE '%compromise%'
GROUP BY court, week
ORDER BY court, week
) TO 'q14.csv' WITH (HEADER, DELIMITER ',');
```
Result: [q14.csv](q14.csv)

### 5. Is translation into regional languages actually happening? Identify judgments with substantial non-ASCII text, court-wise.
Why it matters: The Centre touts a big vernacular push.

Answer: The sample shows no Tamil or Hindi characters in the HTML snippets.
```sql
COPY (
WITH data AS (
  SELECT * FROM read_parquet('/tmp/metadata1.parquet')
  UNION ALL
  SELECT * FROM read_parquet('/tmp/metadata2.parquet')
)
SELECT court,
       SUM(CASE WHEN regexp_matches(raw_html, '[\x{0B80}-\x{0BFF}]') THEN 1 ELSE 0 END) AS tamil_count,
       SUM(CASE WHEN regexp_matches(raw_html, '[\x{0900}-\x{097F}]') THEN 1 ELSE 0 END) AS hindi_count,
       COUNT(*) AS total
FROM data
GROUP BY court
) TO 'q15.csv' WITH (HEADER, DELIMITER ',');
```
Result: [q15.csv](q15.csv)

### 6. Which litigants are serially filing Section 482 CrPC quash petitions, and where do they find fastest relief?
Why it matters: The Supreme Court reaffirmed Section 482 powers but misuse is alleged.

Answer: 27 Section 482 matters appear, with a median disposal time of **147** days at the Madras High Court.
```sql
COPY (
WITH data AS (
  SELECT * FROM read_parquet('/tmp/metadata1.parquet')
  UNION ALL
  SELECT * FROM read_parquet('/tmp/metadata2.parquet')
),
filtered AS (
  SELECT court,
         DATEDIFF('day', STRPTIME(date_of_registration,'%d-%m-%Y'), decision_date) AS days
  FROM data
  WHERE lower(title) LIKE '%482%'
)
SELECT court, MEDIAN(days) AS median_days, COUNT(*) AS total
FROM filtered
GROUP BY court
) TO 'q16.csv' WITH (HEADER, DELIMITER ',');
```
Result: [q16.csv](q16.csv)

### 7. Do NDPS fast-track mandates work? Compare average disposal days for NDPS cases vs the court’s overall median.
Why it matters: Specialized NDPS courts are being added amid rising drug cases.

Answer: The 18 NDPS references in the sample averaged **1 day**, far below the overall median of **92** days.
```sql
COPY (
WITH data AS (
  SELECT * FROM read_parquet('/tmp/metadata1.parquet')
  UNION ALL
  SELECT * FROM read_parquet('/tmp/metadata2.parquet')
),
ndps AS (
  SELECT DATEDIFF('day', STRPTIME(date_of_registration,'%d-%m-%Y'), decision_date) AS days
  FROM data
  WHERE lower(raw_html) LIKE '%ndps%'
),
overall AS (
  SELECT DATEDIFF('day', STRPTIME(date_of_registration,'%d-%m-%Y'), decision_date) AS days
  FROM data
)
SELECT (SELECT AVG(days) FROM ndps) AS ndps_avg,
       (SELECT MEDIAN(days) FROM overall) AS overall_median
) TO 'q17.csv' WITH (HEADER, DELIMITER ',');
```
Result: [q17.csv](q17.csv)

### 8. After major protests or election periods, did habeas corpus filings spike in the state High Courts?
Why it matters: Detentions during protests often trigger habeas petitions.

Answer: Habeas corpus filings peaked at 207 in January 2025 with no clear protest link in this sample.
```sql
COPY (
WITH data AS (
  SELECT * FROM read_parquet('/tmp/metadata1.parquet')
  UNION ALL
  SELECT * FROM read_parquet('/tmp/metadata2.parquet')
)
SELECT strftime(decision_date,'%Y-%m') AS month, COUNT(*) AS total
FROM data
WHERE upper(title) LIKE 'HCP%'
GROUP BY month
ORDER BY month
) TO 'q18.csv' WITH (HEADER, DELIMITER ',');
```
Result: [q18.csv](q18.csv)

### 9. Which judges deliver the most concise judgments without higher reversal rates?
Why it matters: The Supreme Court's "Unclogging the Docket" report stresses brevity.

Answer: Justice K. Rajasekar averaged about **989** characters and reversed **33%** of cases.
```sql
COPY (
WITH data AS (
  SELECT * FROM read_parquet('/tmp/metadata1.parquet')
  UNION ALL
  SELECT * FROM read_parquet('/tmp/metadata2.parquet')
)
SELECT judge,
       AVG(LENGTH(raw_html)) AS avg_len,
       COUNT(*) FILTER (WHERE disposal_nature IN ('ALLOWED','PARTLY ALLOWED')) *1.0/COUNT(*) AS reversal_rate
FROM data
GROUP BY judge
ORDER BY avg_len
) TO 'q19.csv' WITH (HEADER, DELIMITER ',');
```
Result: [q19.csv](q19.csv)

### 10. How dependent are High Courts on landmark Supreme Court precedents?
Why it matters: Citation culture shows doctrinal diffusion and gaps in judge training.

Answer: No references to *Puttaswamy* or *Maneka Gandhi* appear in the sample.
```sql
COPY (
WITH data AS (
  SELECT * FROM read_parquet('/tmp/metadata1.parquet')
  UNION ALL
  SELECT * FROM read_parquet('/tmp/metadata2.parquet')
),
counts AS (
  SELECT court,
         SUM(CASE WHEN lower(raw_html) LIKE '%puttaswamy%' THEN 1 ELSE 0 END) AS puttaswamy,
         SUM(CASE WHEN lower(raw_html) LIKE '%maneka gandhi%' THEN 1 ELSE 0 END) AS maneka
  FROM data
  GROUP BY court
)
SELECT court, puttaswamy + maneka AS total_refs
FROM counts
) TO 'q20.csv' WITH (HEADER, DELIMITER ',');
```
Result: [q20.csv](q20.csv)
