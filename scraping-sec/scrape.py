#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["httpx>=0.27", "lxml>=5.2", "orjson>=3.10"]
# ///
"""Fetch latest Fortune 100 10-K filing dates and revenues."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import re
import time
from typing import Any, Iterable

import httpx
import orjson
from lxml import html

FORTUNE_URL = "https://en.wikipedia.org/wiki/List_of_largest_companies_in_the_United_States_by_revenue"
SEC_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
SEC_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik:010d}.json"
SEC_FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json"
USER_AGENT = "sec-fortune100-scraper/0.1 (contact: ops@example.com)"
REVENUE_CONCEPTS = (
    "RevenueFromContractWithCustomerExcludingAssessedTax",
    "RevenueFromContractWithCustomerIncludingAssessedTax",
    "Revenues",
    "RevenuesNetOfInterestExpense",
    "SalesRevenueNet",
    "SalesRevenueNetOfReturnsAndAllowances",
    "NetSales",
    "TotalRevenues",
)
SEC_UNITS = ("USD", "USDm", "USD millions")

_last_sec_call = 0.0
client = httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=30.0, follow_redirects=True)


def normalize(token: str) -> str:
    token = token.lower().strip()
    token = re.sub(r"^the ", "", token)
    token = token.replace("&", "and")
    token = token.replace("companies", "company")
    token = token.replace("incorporated", "inc")
    token = token.replace("corporation", "corp")
    token = token.replace("co.", "company")
    token = token.replace("cos", "companies")
    token = token.replace("'s", "s")
    token = re.sub(r"[^a-z0-9]", "", token)
    return token


OVERRIDES = {
    normalize("Fannie Mae"): normalize("Federal National Mortgage Association"),
    normalize("Freddie Mac"): normalize("Federal Home Loan Mortgage Corporation"),
    normalize("Publix"): normalize("Publix Super Markets Inc"),
    normalize("State Farm"): normalize("State Farm Mutual Automobile Insurance Company"),
    normalize("Ford Motor Company"): normalize("Ford Motor Co"),
    normalize("Walgreens Boots Alliance"): normalize("Walgreens Boots Alliance Inc"),
    normalize("The Walt Disney Company"): normalize("Walt Disney Co"),
    normalize("Energy Transfer Partners"): normalize("Energy Transfer LP"),
    normalize("John Deere"): normalize("DEERE & CO"),
}

MANUAL_SEC = {
    normalize("Walgreens Boots Alliance"): {"cik_str": "1618921", "ticker": "WBA", "title": "Walgreens Boots Alliance, Inc."},
    normalize("The Walt Disney Company"): {"cik_str": "1744489", "ticker": "DIS", "title": "Walt Disney Co"},
    normalize("John Deere"): {"cik_str": "315189", "ticker": "DE", "title": "DEERE & CO"},
    normalize("Goldman Sachs"): {"cik_str": "886982", "ticker": "GS", "title": "GOLDMAN SACHS GROUP INC"},
}

NO_SEC = {
    normalize("USAA"),
    normalize("TIAA"),
    normalize("State Farm"),
    normalize("Publix"),
    normalize("Liberty Mutual"),
    normalize("Nationwide Mutual Insurance Company"),
    normalize("New York Life Insurance Company"),
}


def throttle_sec() -> None:
    global _last_sec_call
    now = time.perf_counter()
    wait = 0.21 - (now - _last_sec_call)
    if wait > 0:
        time.sleep(wait)
    _last_sec_call = time.perf_counter()


def fetch_fortune100() -> list[dict[str, Any]]:
    resp = client.get(FORTUNE_URL)
    resp.raise_for_status()
    tree = html.fromstring(resp.text)
    tables = tree.xpath('(//table[contains(@class, "wikitable")])[1]')
    if not tables:
        raise RuntimeError("Fortune table not found")
    table = tables[0]
    companies: list[dict[str, Any]] = []
    for row in table.xpath(".//tr"):
        cols = row.xpath("./td")
        if len(cols) < 4:
            continue
        rank_text = cols[0].text_content().strip()
        if not rank_text.isdigit():
            continue
        name = " ".join(cols[1].text_content().strip().split())
        revenue_text = re.sub(r"[^0-9.]", "", cols[3].text_content())
        companies.append(
            {
                "rank": int(rank_text),
                "name": name,
                "fortune_revenue_musd": float(revenue_text) if revenue_text else None,
            }
        )
        if len(companies) == 100:
            break
    if len(companies) < 100:
        raise RuntimeError("Fortune list shorter than expected")
    return companies


def fetch_sec_tickers() -> dict[str, dict[str, Any]]:
    throttle_sec()
    resp = client.get(SEC_TICKERS_URL)
    resp.raise_for_status()
    raw = resp.json()
    mapping: dict[str, dict[str, Any]] = {}
    for entry in raw.values():
        mapping.setdefault(normalize(entry["title"]), entry)
        mapping.setdefault(normalize(entry["ticker"]), entry)
    return mapping


def candidate_norms(norm: str) -> list[str]:
    suffixes = ("", "inc", "corp", "company", "group", "co", "inccompany", "corpcompany")
    return [norm + suffix for suffix in suffixes]


def resolve_company(name: str, mapping: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    norm = normalize(name)
    if norm in NO_SEC:
        return None
    manual = MANUAL_SEC.get(norm)
    if manual:
        return manual
    for candidate in candidate_norms(norm):
        if candidate in mapping:
            return mapping[candidate]
    override = OVERRIDES.get(norm)
    if override and override in mapping:
        return mapping[override]
    hits = [entry for key, entry in mapping.items() if norm and norm in key]
    if hits:
        hits.sort(key=lambda item: len(normalize(item["title"])))
        return hits[0]
    return None

def recent_field(recent: dict[str, list[Any]], field: str, idx: int) -> Any:
    values = recent.get(field, [])
    return values[idx] if idx < len(values) else None


def fetch_latest_10k(cik: int | None) -> dict[str, Any] | None:
    if cik is None:
        return None
    throttle_sec()
    resp = client.get(SEC_SUBMISSIONS_URL.format(cik=cik))
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    data = resp.json()
    recent = data.get("filings", {}).get("recent", {})
    forms = recent.get("form", [])
    if not forms:
        return None
    indices = [i for i, form in enumerate(forms) if form == "10-K"]
    if not indices:
        indices = [i for i, form in enumerate(forms) if form.startswith("10-K")]
    if not indices:
        return None
    idx = indices[0]
    fy_raw = recent_field(recent, "fy", idx)
    fy = int(fy_raw) if fy_raw and str(fy_raw).isdigit() else None
    return {
        "cik": cik,
        "ticker": data.get("tickers", [None])[0],
        "filing_date": recent_field(recent, "filingDate", idx),
        "fy": fy,
        "accession": recent_field(recent, "accessionNumber", idx),
        "document": recent_field(recent, "primaryDocument", idx),
    }


def fetch_revenue(filing: dict[str, Any] | None) -> float | None:
    if not filing:
        return None
    throttle_sec()
    resp = client.get(SEC_FACTS_URL.format(cik=filing["cik"]))
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    facts = resp.json().get("facts", {}).get("us-gaap", {})

    def pick(points: list[dict[str, Any]]) -> float | None:
        if not points:
            return None
        ordered = sorted(points, key=lambda p: (p.get("end") or "", p.get("filed") or ""))
        return float(ordered[-1]["val"])

    for concept in REVENUE_CONCEPTS:
        units = facts.get(concept, {}).get("units", {})
        for unit in SEC_UNITS:
            points = units.get(unit, [])
            if not points:
                continue
            preferred = [p for p in points if p.get("form", "").startswith("10-K")]
            if not preferred:
                continue
            target_year = filing.get("fy")
            if target_year:
                fy_full = [p for p in preferred if p.get("fy") == target_year and p.get("fp") == "FY"]
                value = pick(fy_full)
                if value is not None:
                    return value
                fy_any = [p for p in preferred if p.get("fy") == target_year]
                value = pick(fy_any)
                if value is not None:
                    return value
            fy_points = [p for p in preferred if p.get("fp") == "FY"]
            value = pick(fy_points)
            if value is not None:
                return value
            value = pick(preferred)
            if value is not None:
                return value
    return None


def build_filing_url(filing: dict[str, Any] | None) -> str | None:
    if not filing or not filing.get("accession") or not filing.get("document"):
        return None
    accession = filing["accession"].replace("-", "")
    return f"https://www.sec.gov/Archives/edgar/data/{filing['cik']:010d}/{accession}/{filing['document']}"


def enrich(records: Iterable[dict[str, Any]], mapping: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    enriched: list[dict[str, Any]] = []
    for entry in records:
        sec_entry = resolve_company(entry["name"], mapping)
        cik = int(sec_entry["cik_str"]) if sec_entry else None
        filing = fetch_latest_10k(cik)
        revenue = fetch_revenue(filing)
        enriched.append(
            {
                "rank": entry["rank"],
                "name": entry["name"],
                "ticker": sec_entry["ticker"] if sec_entry else None,
                "cik": cik,
                "fortune_revenue_musd": entry["fortune_revenue_musd"],
                "latest_10k_date": filing["filing_date"] if filing else None,
                "latest_10k_revenue_usd": revenue,
                "latest_10k_url": build_filing_url(filing),
            }
        )
        if not sec_entry:
            print(f"warn: no SEC match for {entry['name']}")
        elif not filing:
            print(f"warn: no 10-K for {entry['name']}")
        elif revenue is None:
            print(f"warn: no revenue figure for {entry['name']}")
    return enriched


def main() -> None:
    fortune = fetch_fortune100()
    tickers = fetch_sec_tickers()
    enriched = enrich(fortune, tickers)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "fortune_source": FORTUNE_URL,
        "sec_sources": {
            "tickers": SEC_TICKERS_URL,
            "submissions": SEC_SUBMISSIONS_URL,
            "facts": SEC_FACTS_URL,
        },
        "companies": enriched,
    }
    out_file = Path("fortune100_10k.json")
    out_file.write_bytes(orjson.dumps(payload, option=orjson.OPT_INDENT_2))
    print(f"wrote {len(enriched)} companies to {out_file}")
    client.close()


if __name__ == "__main__":
    main()
