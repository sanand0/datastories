# Indian High Courts Data Analysis Prompts

## 17 Jun 2025, Claude Code

````
The Indian high court judgement dataset contains judgements from the Indian High Courts, downloaded from [ecourts website](https://judgments.ecourts.gov.in/). It contains judgments of 25 high courts, along with raw metadata (in json format) and structured metadata (in parquet format). Judgments from the website are further compressed to optimize for size (care has been taken to not have any loss of data either in content or in visual appearance). Judgments are available as both individual pdf files and as tar files for easier download.

- 25 high courts
- ~16M judgments
- ~1TB of data

### Structure of the data in the bucket

```
* data/pdf/year=2025/court=xyz/bench=xyz/judgment1.pdf,judgment2.pdf
* metadata/json/year=2025/court=xyz/bench=xyz/judgment1.json,judgment2.json
* metadata/parquet/year=2025/court=xyz/bench=xyz/metadata.parquet
* metadata/tar/year=2025/court=xyz/bench=xyz/metadata.tar.gz
* data/tar/year=2025/court=xyz/bench=xyz/pdfs.tar
```

### Example usage

This DuckDB query counts the number of decisions in November. Note how the query merges all the benches. You need to do this whenever required (which is often).

```sql
INSTALL httpfs; LOAD httpfs;
INSTALL parquet; LOAD parquet;

-- Merge all benches
WITH combined AS (
    SELECT * FROM
    read_parquet('s3://indian-high-court-judgments/metadata/parquet/year=2025/court=33_10/bench=hc_cis_mas/metadata.parquet')
    UNION ALL
    SELECT * FROM
    read_parquet('s3://indian-high-court-judgments/metadata/parquet/year=2025/court=33_10/bench=mdubench/metadata.parquet')
),
filtered_november AS (
    SELECT
        TRY_CAST(decision_date AS DATE) AS decision_date
    FROM combined
    WHERE TRY_CAST(decision_date AS DATE) IS NOT NULL
)
SELECT COUNT(*) AS total_november_decisions
FROM filtered_november
WHERE EXTRACT(MONTH FROM decision_date) = 11;
```

Create a indian-high-courts/README.md file that contains a data story analyzing this dataset.

Begin by inspecting and explaining the structure of the data _clearly_ to an analyst.

Include a walk through of all tables and columns, and include basic exploratory data analysis of each column (e.g. date distributions, frequency of textual columns, mean & distribution of numeric columns, etc.)

Given the following dataset & analyses, suggest 5 non-trivial questions an expert legal data journalist at The Hindu would be interested in reporting on about the Indian High Courts Judgements. These should be interesting and news-worthy. They should all be answerable just from the parquet dataset.

Then, follow this process to answer each question:

1. Write and execute DuckdB SQL code to generate the result as a table and save it as a CSV under indian-high-courts/. You can run DuckDB from the command line.
2. In case of failure or timeout, modify the query and retry up to 2 times, then give up on this question
3. Read the response and update the README.md with the question, the answer to the question based on the output, the code to answer it, a link to the output CSV

In all of this, do NOT analyze a sample. Analyze the ENTIRE dataset via the S3 bucket since DuckDB uses range headers efficiently on remote Parquet files.
````

## Additional Questions

```
Add a succinct version of this question and answer it.

Identify all accused individuals with UAPA charges whose cases involve daily bail hearings, and extract a dataset that shows a sequence of such hearings (one triangle per accused) over time, highlighting how bail is repeatedly postponed or denied. Ignore unrelated petitions (e.g. for food or facilities). Use this to find patterns like repeated delays in UAPA bail hearings. Break it down by state and year.
```

```
Execute the UAPA query and interpet the findings in the light of the question and added it to the major findings.
```

```
Extract a sample of UAPA cases with petitioner name, judge name, date of bail plea, and the respondent. Use the same code as in query 6. Also save this as a sample UAPA SQL file and the output as a sample UAPA CSV.
```
