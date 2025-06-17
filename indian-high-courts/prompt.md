# Indian High Courts Data Analysis Prompts

## 17 Jun 2025, Codex

[Codex](https://chatgpt.com/codex/tasks/task_e_6851330b2a74832cbc458f39e372b9df)

### Add Indian High Court data story

[Commited](https://github.com/sanand0/datastories/pull/1/commits/4112837aa0c40eab470329e6fb8d184dfedc0199) from this prompt:

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

This DuckDB query counts the number of decisions in November

```sql
INSTALL httpfs; LOAD httpfs;
INSTALL parquet; LOAD parquet;

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

Then identify 10 interesting questions that could be answered from this data.

Then, follow this process to answer each question:

1. Write and execute DuckdB SQL code to generate the result as a table and save it as a CSV
2. In case of failure or timeout, modify the query and retry up to 2 times, then give up on this question
3. Read the response and update the README.md with the question, the answer to the question based on the output, the code to answer it, a link to the output CSV
````

### Expand Indian High Court EDA

[Commited](https://github.com/sanand0/datastories/pull/1/commits/8c9058f91fd956463b1e18daa0b5f9f50b14b7a6) from this prompt:

```
Begin indian-high-courts/README.md with a walk through of all tables and columns, and include basic exploratory data analysis (e.g. date distributions, frequency of textual columns, mean & distribution of numeric columns, etc.)
```

### Rewrite HC dataset README with new questions

I generated the following prompt by passing the generated [README.md](https://github.com/sanand0/datastories/blob/8c9058f91fd956463b1e18daa0b5f9f50b14b7a6/indian-high-courts/README.md) to [O3](https://chatgpt.com/?model=o3) with this question:

> Given the following dataset & analyses, suggest 10 non-trivial questions an expert legal data journalist at The Hindu would be interested in reporting on about the Indian High Courts Judgements. These should be interesting and news-worthy. They should all be answerable just from the parquet dataset.

[Here is the ChatGPT conversation](https://chatgpt.com/share/68513e3f-d3cc-800c-adc3-daf02883eddb).

[Committed](https://github.com/sanand0/datastories/pull/1/commits/59c97eaeadada05e5cf4cdff999c88662d117de6) from this prompt:

```
Rewrite README.md to have the question, answer, then SQL (instead of the current question, SQL, answer) for each question.

Answer these 10 questions in the same way as before and append to README.md. After the question, mention why it matters, then the answer, then the SQL.

| #  | Question to dig                                                                                                                                                        | Why it matters (news hook)                                                                                                                            | How the parquet gives you the answer                                                                                                       |
| -- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| 1  | **Which High Courts reversed the highest share of lower-court convictions in criminal appeals during 2025, and did any judge stand out?**                              | SC has warned HCs about decade-long criminal-appeal delays and consistency issues ([hindustantimes.com][1]).                                          | Filter `title` for “CRL A”/“CRL APPEAL”; use `disposal_nature` to tag “Allowed/Partly Allowed” as reversals; group by `court` and `judge`. |
| 2  | **How often did each High Court dispose of criminal bail, anticipatory bail, and habeas corpus matters within the 30-day ‘urgent liberty’ window?**                    | Bail pendency is under the spotlight; only 15 judges per million amplify delay concerns ([m.economictimes.com][2]).                                   | `title` begins “CRM BA”, “ABA”, “HCP” → compute `DATEDIFF(date_of_registration, decision_date)` ≤ 30; aggregate.                           |
| 3  | **Are writ petitions invoking Article 226 on environmental issues rising, and which benches grant relief most often?**                                                 | Article 226 used to block projects; SC’s own curbs on environmental review draw attention ([scotusblog.com][3]).                                      | `raw_html` LIKE ‘%article 226%’ AND (‘forest’ OR ‘mining’ OR ‘pollution’ keywords); compare `disposal_nature`.                             |
| 4  | **Which courts most rely on Lok Adalat-style ‘compromise/settled’ disposals—and does that spike around the National Lok Adalat dates?**                                | Over 3 crore cases settled in the 2025 National Lok Adalat ([lawbhoomi.com][4]).                                                                      | `disposal_nature` \~ ‘Compromise Settlement’; plot by `decision_date` weeks.                                                               |
| 5  | **Is translation into regional languages actually happening? Identify judgments with substantial non-ASCII text, court-wise.**                                         | Centre touts vernacular push; 47k SC judgments already translated ([pib.gov.in][5], [sansad.in][6]).                                                  | Regex on `raw_html` for Unicode blocks (e.g., Tamil `\u0B80-\u0BFF`, Hindi `\u0900-\u097F`); compute percentages per `court`.              |
| 6  | **Which litigants (identify via repeating party names in `description`) are serially filing Section 482 CrPC quash petitions, and where do they find fastest relief?** | SC reaffirmed HCs’ 482 powers; high misuse alleged ([bonumlex.com][7]).                                                                               | Filter `title` LIKE ‘Crl.OP’ OR contains ‘482’; fuzzy-cluster petitioner strings; calculate median disposal days by court.                 |
| 7  | **Do NDPS fast-track mandates work? Compare average disposal days for NDPS cases vs the court’s overall median.**                                                      | NDPS courts being added amid rising drug cases ([timesofindia.indiatimes.com][8]).                                                                    | `title` OR `raw_html` contains ‘NDPS’; compute time-to-dispose metrics.                                                                    |
| 8  | **After major protests/election periods, did habeas corpus filings spike in the relevant state High Courts?**                                                          | Detentions during protests often trigger HCPs; civil-liberty groups watch closely ([aclu.org][9]).                                                    | Identify `title` starting ‘HCP’; plot counts around known protest dates (can align with external timeline).                                |
| 9  | **Which judges deliver the most concise judgments (shortest `raw_html` length) without higher reversal rates?**                                                        | Efficiency vs thoroughness debate; SC’s “Unclogging the Docket” report stresses brevity ([courtbook.in][10]).                                         | `LENGTH(raw_html)` for size; link judge to appeal outcomes via `disposal_nature`.                                                          |
| 10 | **How dependent are High Courts on landmark SC precedents? Count references to top-10 cited SC cases (e.g., *Puttaswamy*, *Maneka Gandhi*) and rank courts.**          | Citation culture shows doctrinal diffusion; judge-training question given only 15 judges per million ([m.economictimes.com][2], [scobserver.in][11]). | Keyword search inside `raw_html` for case names; tally per `court`.                                                                        |
```

### Terminate analysis

I realized this analysis was done on a small, sample dataset of ~14K rows from the Madras High Court between Jan - Dec 2025 (which is effectively Jan - May 2025).

That's not as helpful. I'll start again.
