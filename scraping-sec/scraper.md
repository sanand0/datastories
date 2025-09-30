# How Codex CLI Scraped the Fortune 100 Revenue

1. **Got bearings & set a plan**
   - Looked around the working folder (`ls`, including hidden files) to see what already existed. It was basically empty at the start.
   - Sketched a plan: get the Fortune 100 list, map each company to its SEC identifier (ticker/CIK), fetch the latest 10-K for each, pull the revenue number, and save everything into one JSON. Then verify with quick spot checks.
2. **Wrote a script scaffold**
   - Created `scrape.py` with a "self-contained" header (so it could fetch its own Python deps when run).
   - Declared the job in comments: "Fetch latest Fortune 100 10-K and revenues."
   - Made the script executable.
3. **First run hit a sandbox snag**
   - Tried running `./scrape.py` and the environment blocked it (a sandbox permission/exec policy issue).
   - Codex adjusted and re-ran in a way the sandbox would allow, then continued iterating on the script (no user intervention required after that).
4. **Picked data sources (kept it official & lightweight)**
   - **Fortune 100 list**: scraped a current Fortune 100 ranking (the list of the biggest U.S. companies by revenue).
   - **SEC company mapping**: used SEC's official mappings to go from _company name > ticker/CIK_:
     - `https://www.sec.gov/files/company_tickers.json`
     - `https://www.sec.gov/files/company_tickers_exchange.json`
   - **SEC company facts (financials)**: for each company with a CIK, pulled the official XBRL "Company Facts" API:
     - `https://data.sec.gov/api/xbrl/companyfacts/CIK##########.json`
   - Used a **polite User-Agent** and minimal request rate-SEC expects that.
5. **Name-matching is messy-Codex normalized names**
   - Company naming is inconsistent across Fortune lists vs SEC records (e.g., "Walgreens" vs **Walgreens Boots Alliance**; "John Deere" vs **Deere & Company**).
   - Codex **normalized** names (lowercased, removed punctuation and suffixes like "Inc.", "Corp", "Company", etc.) and tried multiple candidate forms (with/without suffixes).
   - It **tested difficult cases explicitly**:
     - Searched SEC lists for **Walgreens** variants and verified the right ticker (**WBA**).
     - Sanity-checked **Disney** and **Deere** name forms to ensure the match logic wasn't brittle.
   - For still-tricky exceptions, Codex added **manual overrides** (a tiny dictionary of "if you see X, map to Y").
6. **Figured out the _right_ revenue tag**
   - SEC's data has many revenue-like fields, and **banks/insurers** often use different tags than retailers/manufacturers.
   - Codex fetched a company's facts and **listed available GAAP keys** to see what existed (e.g., `RevenueFromContractWithCustomerExcludingAssessedTax`, `Revenues`, `RevenuesNetOfInterestExpense`, etc.).
   - It then **chose a sensible, common tag** (preferring "Revenue from contracts with customers" when present), falling back when needed.
   - It spot-checked cases like **Walgreens** and **Amazon** to confirm the chosen field held the actual annual revenue figure reported in the 10-K.
7. **Picked the _latest_ 10-K per company**
   - Pulled each company's **recent filings list** and filtered to the latest **10-K** (not 10-Q, not 8-K).
   - Extracted the filing date and matched it with the corresponding fiscal-year revenue from the facts API.
8. **Iterated until the warnings looked reasonable**
   - Early runs printed warnings like:
     - "no SEC match for <company>" (private or mutual companies without SEC filings),
     - "no revenue figure for <company>" (typically banks/insurers where the generic revenue tag didn't exist).
   - Codex improved the mapping and revenue logic, **re-ran the script several times**, and watched the warnings drop.
9. **Wrote the output and verified it**
   - Produced **`fortune100_10k.json`** with a `companies` array containing fields such as: rank, name, ticker/CIK (if available), **latest_10k_date**, and **latest_10k_revenue (USD)**.
   - Ran quick **sanity checks**:
     - Spot-checked **Amazon** and **Apple** entries and saw plausible values with recent filing dates (e.g., Amazon's latest 10-K dated **2025-02-07**; Apple's latest 10-K dated **2024-11-01**).
     - Counted **how many companies had a ticker** (> **93**).
     - Counted **how many were missing a revenue** figure (> **7**).
10. **Identified the unavoidable edge cases**
    - The **7 with no ticker** (and thus no SEC 10-K) were **private/mutual** organizations, so the SEC data path doesn't apply:
      - **State Farm**
      - **New York Life Insurance Company**
      - **Publix**
      - **Nationwide Mutual Insurance Company**
      - **Liberty Mutual**
      - **USAA**
      - **TIAA**
    - For a couple of big **financials** (e.g., **Goldman Sachs** in early runs), the chosen revenue tag wasn't present under the exact name expected; Codex adjusted logic and pushed through, but it kept warning when a clean "revenue" number wasn't explicitly available in the form it preferred.
11. **Tidied up**
    - Kept a small **backup** folder of intermediate JSONs (SEC mappings and the output), removed temporary files, and listed the directory to confirm the final outputs were present.

With this, we end up with:

- `fortune100_10k.json` summarizing, for ~**93** publicly-reporting Fortune 100 companies, their **latest 10-K filing date** and **reported annual revenue (USD)**.
- A clear list of **7** companies that **don't file with the SEC** (so they rightly remain unmatched).
