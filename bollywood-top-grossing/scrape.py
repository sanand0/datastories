#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "beautifulsoup4",
#     "httpx",
# ]
# ///
from __future__ import annotations

import csv
import sys
import re
from pathlib import Path
from typing import Iterable, Tuple
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

BASE_URL = "https://en.wikipedia.org/api/rest_v1/page/html/"
WIKIPEDIA_ROOT = "https://en.wikipedia.org/wiki/"
SECTION_KEYWORDS = ("grossing", "box office")
HEADERS = {"user-agent": "bollywood-top-grossing/0.1"}


RANK_TERMS = ("rank", "no.", "no", "number", "position", "#")
TITLE_TERMS = ("title", "film")
GROSS_TERMS = (
    "worldwide gross",
    "worldwide collection",
    "world gross",
    "box office worldwide",
    "worldwide box office",
    "global gross",
    "worldwide",
    "gross",
    "box office",
)


def normalize_gross_to_crore(value: str) -> float:
    primary = value.replace(" ", " ").strip()
    if not primary:
        raise ValueError("Empty gross value")
    primary = re.split(r"\s*\(", primary, maxsplit=1)[0].strip()
    primary = (
        primary.replace("–", "-")
        .replace("—", "-")
        .replace("−", "-")
        .replace(" to ", "-")
        .replace(" To ", "-")
    )
    primary = re.sub(r"\[[^\]]*\]", "", primary)
    primary = re.sub(r"\s+", " ", primary)
    lower = primary.lower()

    number_strings = re.findall(r"\d[\d,]*\.?\d*", primary)
    if not number_strings:
        raise ValueError(f"Could not parse gross value: {value!r}")
    numbers = [float(token.replace(",", "")) for token in number_strings]
    if not numbers:
        raise ValueError(f"Could not interpret numbers in gross value: {value!r}")

    if "billion" in lower:
        converted = [num * 100 for num in numbers]
    elif "million" in lower:
        converted = [num * 0.1 for num in numbers]
    elif "lakh" in lower:
        converted = [num / 100 for num in numbers]
    elif "crore" in lower or re.search(r"\bcr\b", lower):
        converted = numbers
    else:
        converted = [num / 10_000_000 for num in numbers]

    if "-" in primary and len(converted) > 1:
        return sum(converted) / len(converted)

    return converted[0]


def format_crore(value: float) -> str:
    return format(value, ".2f").rstrip("0").rstrip(".")


def iter_years(start: int = 1994, end: int = 2024) -> Iterable[int]:
    return range(start, end + 1)


def find_target_table(soup: BeautifulSoup):
    for section in soup.find_all("section"):
        heading = section.find(["h2", "h3", "h4"])
        if not heading:
            continue
        heading_text = heading.get_text(" ", strip=True).lower()
        if any(keyword in heading_text for keyword in SECTION_KEYWORDS):
            for table in section.find_all("table"):
                if table_matches(table):
                    return table
    for table in soup.find_all("table"):
        if table_matches(table):
            return table
    return None


def header_indices(table) -> Tuple[object, int | None, int | None, int | None]:
    header_row = None
    for row in table.find_all("tr"):
        cells = row.find_all(["th", "td"])
        if not cells:
            continue
        if any(cell.name == "th" for cell in cells):
            header_row = row
            break
    if header_row is None:
        return header_row, None, None, None
    header_texts = [
        cell.get_text(" ", strip=True).lower() for cell in header_row.find_all(["th", "td"])
    ]

    def find_index(terms):
        for term in terms:
            for idx, text in enumerate(header_texts):
                if term in text:
                    return idx
        return None

    rank_idx = find_index(RANK_TERMS)
    title_idx = find_index(TITLE_TERMS)
    gross_idx = find_index(GROSS_TERMS)
    return header_row, rank_idx, title_idx, gross_idx


def table_matches(table) -> bool:
    header_row, rank_idx, title_idx, gross_idx = header_indices(table)
    return header_row is not None and all(
        idx is not None for idx in (rank_idx, title_idx, gross_idx)
    )


def extract_rows(table, year: int):
    header_row, rank_idx, title_idx, gross_idx = header_indices(table)
    if header_row is None:
        raise ValueError("Missing table header")
    required = (rank_idx, title_idx, gross_idx)
    if any(index is None for index in required):
        raise ValueError("Missing required columns in table")

    for row in table.find_all("tr"):
        if row is header_row:
            continue
        for sup in row.find_all("sup"):
            sup.decompose()
        cells = row.find_all(["td", "th"])
        if not cells or all(cell.name == "th" for cell in cells):
            continue

        title_cell = None
        if title_idx is not None and title_idx < len(cells):
            title_cell = cells[title_idx]
        if title_cell is None:
            title_cell = next(
                (cell for cell in cells if cell.find("a")),
                cells[1] if len(cells) > 1 else cells[0],
            )
        link = title_cell.find("a", href=True)
        title = (link or title_cell).get_text(" ", strip=True)
        href = urljoin(WIKIPEDIA_ROOT, link["href"]) if link else ""

        rank_cell = None
        if rank_idx is not None and rank_idx < len(cells):
            rank_cell = cells[rank_idx]
        if rank_cell is None:
            rank_cell = cells[0]
        rank_text = rank_cell.get_text(" ", strip=True)

        candidate_cells = []
        if gross_idx is not None and gross_idx < len(cells):
            candidate_cells.append(cells[gross_idx])
        for cell in cells:
            if cell not in candidate_cells:
                candidate_cells.append(cell)

        gross_value = None
        for candidate in candidate_cells:
            text_value = candidate.get_text(" ", strip=True)
            if not text_value:
                continue
            lower_value = text_value.lower()
            if not any(
                keyword in lower_value
                for keyword in ("₹", "crore", "cr", "million", "billion", "lakh")
            ) and not re.search(r"\d,\d", text_value):
                continue
            try:
                gross_value = normalize_gross_to_crore(text_value)
                break
            except ValueError:
                continue

        if gross_value is None:
            raise ValueError(f"Could not locate gross value for {year} - {title}")

        yield {
            "year": year,
            "rank": rank_text,
            "title": title,
            "link": href,
            "worldwide_gross": format_crore(gross_value),
        }


def scrape_year(client: httpx.Client, year: int):
    url = f"{BASE_URL}List_of_Hindi_films_of_{year}"
    response = client.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    table = find_target_table(soup)
    if not table:
        raise RuntimeError(f"No matching table found for {year}")
    rows = list(extract_rows(table, year))
    if not rows:
        raise RuntimeError(f"Table for {year} contained no rows")
    return rows


def main(output_path: str):
    records = []
    with httpx.Client(headers=HEADERS, timeout=30.0) as client:
        for year in iter_years():
            rows = scrape_year(client, year)
            records.extend(rows)
            print(f"{year}: {len(rows)} rows", file=sys.stderr)

    with Path(output_path).open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=["year", "rank", "title", "link", "worldwide_gross"])
        writer.writeheader()
        writer.writerows(records)


if __name__ == "__main__":
    output = sys.argv[1] if len(sys.argv) > 1 else "highest_grossing.csv"
    main(output)
