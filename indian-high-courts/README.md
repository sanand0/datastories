# Indian High Court Judgments

This story explores the dataset of Indian High Court judgments available from the [ecourts website](https://judgments.ecourts.gov.in/). The data is hosted on S3 in several folders.

## Data layout

```
* data/pdf/year=2025/court=xyz/bench=xyz/judgment1.pdf,judgment2.pdf
* metadata/json/year=2025/court=xyz/bench=xyz/judgment1.json,judgment2.json
* metadata/parquet/year=2025/court=xyz/bench=xyz/metadata.parquet
* metadata/tar/year=2025/court=xyz/bench=xyz/metadata.tar.gz
* data/tar/year=2025/court=xyz/bench=xyz/pdfs.tar
```

`court` is the high court code and `bench` is its sub-division. The parquet files contain a row per judgment with fields such as the decision date and case type. The PDF and JSON files provide the full text and raw metadata.

The dataset covers **25 high courts** with roughly **16 million** judgments. The total size is about **1TB** compressed.

## Columns

The parquet files share a common structure. A sample file contains the following columns:

| column_name | column_type |
|-------------|-------------|
| court_code  | VARCHAR     |
| title       | VARCHAR     |
| description | VARCHAR     |
| judge       | VARCHAR     |
| pdf_link    | VARCHAR     |
| cnr         | VARCHAR     |
| date_of_registration | VARCHAR |
| decision_date | DATE |
| disposal_nature | VARCHAR |
| court | VARCHAR |
| raw_html | VARCHAR |

The sample used for analysis contains **13,974** rows from the Madras High Court with decision dates between **2025‑01‑04** and **2025‑12‑03**.

## Exploratory data analysis

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

## Questions

Below are 10 questions that can be answered using the metadata. Each question would typically involve joining or filtering the parquet files.

1. How many judgments were issued by each high court in 2025?
2. What is the distribution of decision dates across months for a chosen court?
3. Which case types appear most frequently for a specific bench?
4. How many judgments mention the phrase "Article 226" in the PDF text?
5. What percentage of judgments are criminal vs civil matters per court?
6. What was the median decision time (from filing to decision) per court?
7. How many judgments were uploaded each month in 2025 across all courts?
8. Which courts have the highest proportion of judgments in regional languages?
9. What is the average length in pages of judgments for a court?
10. How many cases were disposed of within 30 days in each court?

## Answers

### 1. Judgments per high court

```sql
COPY (
SELECT court, SUM(total) AS total
FROM (
  SELECT court, COUNT(*) AS total FROM read_parquet('/tmp/metadata.parquet') GROUP BY court
  UNION ALL
  SELECT court, COUNT(*) AS total FROM read_parquet('/tmp/metadata2.parquet') GROUP BY court
) t
GROUP BY court
) TO 'q1.csv' WITH (HEADER, DELIMITER ',');
```

Result: [q1.csv](q1.csv)

*Madras High Court issued **21,583** judgments in 2025 (sample from two benches).* 

### 2. Monthly decision counts

```sql
COPY (
SELECT month, SUM(total) AS total
FROM (
  SELECT strftime(decision_date, '%Y-%m') AS month, COUNT(*) AS total FROM read_parquet('/tmp/metadata.parquet') GROUP BY month
  UNION ALL
  SELECT strftime(decision_date, '%Y-%m') AS month, COUNT(*) AS total FROM read_parquet('/tmp/metadata2.parquet') GROUP BY month
) t
GROUP BY month
ORDER BY month
) TO 'q2.csv' WITH (HEADER, DELIMITER ',');
```

Result: [q2.csv](q2.csv)

*January had the highest activity with **9,041** judgments.*

### 3. Top case types (bench hc_cis_mas)

```sql
COPY (
SELECT type, COUNT(*) AS total
FROM (
  SELECT regexp_extract(title, '^(\\w+)', 1) AS type FROM read_parquet('/tmp/metadata.parquet')
)
GROUP BY type
ORDER BY total DESC
LIMIT 10
) TO 'q3.csv' WITH (HEADER, DELIMITER ',');
```

Result: [q3.csv](q3.csv)

*Most cases were **CRL** (5666) and **WP** (3515).* 

### 4. Mentions of "Article 226"

```sql
COPY (
SELECT COUNT(*) AS total
FROM (
  SELECT * FROM read_parquet('/tmp/metadata.parquet')
  UNION ALL
  SELECT * FROM read_parquet('/tmp/metadata2.parquet')
) t
WHERE lower(raw_html) LIKE '%article 226%'
) TO 'q4.csv' WITH (HEADER, DELIMITER ',');
```

Result: [q4.csv](q4.csv)

*Only **69** records mention the phrase.* 

### 5. Criminal vs civil split

```sql
COPY (
SELECT court,
       SUM(CAST(is_criminal AS INTEGER)) AS criminal,
       SUM(CAST(NOT is_criminal AS INTEGER)) AS civil,
       ROUND(SUM(CAST(is_criminal AS DOUBLE))*100.0/COUNT(*), 2) AS criminal_pct,
       ROUND(SUM(CAST(NOT is_criminal AS DOUBLE))*100.0/COUNT(*), 2) AS civil_pct
FROM (
  SELECT court, CASE WHEN upper(title) LIKE 'CRL%' OR upper(title) LIKE 'CRP%' OR upper(title) LIKE 'HCP%' THEN TRUE ELSE FALSE END AS is_criminal
  FROM read_parquet('/tmp/metadata.parquet')
  UNION ALL
  SELECT court, CASE WHEN upper(title) LIKE 'CRL%' OR upper(title) LIKE 'CRP%' OR upper(title) LIKE 'HCP%' THEN TRUE ELSE FALSE END AS is_criminal
  FROM read_parquet('/tmp/metadata2.parquet')
) t
GROUP BY court
) TO 'q5.csv' WITH (HEADER, DELIMITER ',');
```

Result: [q5.csv](q5.csv)

*Criminal matters were about **43%** of the sample.*

### 6. Median days from filing to decision

```sql
COPY (
SELECT court, MEDIAN(DATEDIFF('day', STRPTIME(date_of_registration, '%d-%m-%Y'), decision_date)) AS median_days
FROM (
  SELECT * FROM read_parquet('/tmp/metadata.parquet')
  UNION ALL
  SELECT * FROM read_parquet('/tmp/metadata2.parquet')
) t
GROUP BY court
) TO 'q6.csv' WITH (HEADER, DELIMITER ',');
```

Result: [q6.csv](q6.csv)

*Median time to resolve a case was **92 days**.*

### 7. Monthly uploads across courts

```sql
COPY (
SELECT month, COUNT(*) AS total
FROM (
  SELECT strftime('%Y-%m', decision_date) AS month FROM read_parquet('/tmp/metadata.parquet')
  UNION ALL
  SELECT strftime('%Y-%m', decision_date) AS month FROM read_parquet('/tmp/metadata2.parquet')
) t
GROUP BY month
ORDER BY month
) TO 'q7.csv' WITH (HEADER, DELIMITER ',');
```

Result: [q7.csv](q7.csv)

*The trend mirrors the single-court chart since only Madras data was sampled.*

### 8. Judgments in Tamil

```sql
COPY (
SELECT court,
       SUM(CASE WHEN raw_html ~ '[\u0B80-\u0BFF]' THEN 1 ELSE 0 END) AS tamil_count,
       COUNT(*) AS total,
       ROUND(SUM(CASE WHEN raw_html ~ '[\u0B80-\u0BFF]' THEN 1 ELSE 0 END)*100.0/COUNT(*), 2) AS tamil_pct
FROM (
  SELECT * FROM read_parquet('/tmp/metadata.parquet')
  UNION ALL
  SELECT * FROM read_parquet('/tmp/metadata2.parquet')
) t
GROUP BY court
) TO 'q8.csv' WITH (HEADER, DELIMITER ',');
```

Result: [q8.csv](q8.csv)

*No Tamil text was detected in the HTML snippets.* 

### 9. Average judgment length

Attempted to fetch PDFs from `https://judgments.ecourts.gov.in/` using the `pdf_link` field, but the server returned **403 Forbidden**. Without the documents we cannot compute page counts.

### 10. Fast disposals (within 30 days)

```sql
COPY (
SELECT court, COUNT(*) AS fast_disposals
FROM (
  SELECT court, DATEDIFF('day', STRPTIME(date_of_registration, '%d-%m-%Y'), decision_date) AS days
  FROM read_parquet('/tmp/metadata.parquet')
  UNION ALL
  SELECT court, DATEDIFF('day', STRPTIME(date_of_registration, '%d-%m-%Y'), decision_date) AS days
  FROM read_parquet('/tmp/metadata2.parquet')
) t
WHERE days <= 30
GROUP BY court
) TO 'q10.csv' WITH (HEADER, DELIMITER ',');
```

Result: [q10.csv](q10.csv)

*About **6,939** cases were disposed of within 30 days.*
