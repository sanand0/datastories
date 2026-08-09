#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["lxml>=6"]
# ///
"""Merge cached Gramener Glassdoor HTML and first-party API responses."""

import copy
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urljoin

from lxml import html

ROOT = Path(__file__).parent
BASE = "https://www.glassdoor.co.in"


def load_json(path: str):
    return json.loads((ROOT / path).read_text())


def document(path: str):
    return html.parse(ROOT / path)


def text(node) -> str:
    return " ".join(node.text_content().split()) if node is not None else ""


def first(node, xpath: str):
    values = node.xpath(xpath)
    return values[0] if values else None


def first_text(node, xpath: str) -> str | None:
    value = first(node, xpath)
    if value is None:
        return None
    result = text(value) if hasattr(value, "text_content") else str(value).strip()
    return result or None


def visible_text(tree) -> str:
    root = copy.deepcopy(tree.getroot())
    for element in root.xpath("//script|//style|//noscript"):
        element.drop_tree()
    return "\n".join(line.strip() for line in root.text_content().splitlines() if line.strip())


def json_ld(tree, kind: str) -> dict | None:
    for value in tree.xpath('//script[@type="application/ld+json"]/text()'):
        try:
            data = json.loads(value)
        except json.JSONDecodeError:
            continue
        if data.get("@type") == kind:
            return data
    return None


def flight_text(tree) -> str:
    chunks = []
    for script in tree.xpath("//script/text()"):
        if "self.__next_f.push" not in script:
            continue
        for match in re.finditer(r"self\.__next_f\.push\((\[.*?\])\)\s*;?", script, re.DOTALL):
            try:
                payload = json.loads(match.group(1))
            except json.JSONDecodeError:
                continue
            if len(payload) > 1 and isinstance(payload[1], str):
                chunks.append(payload[1])
    return "".join(chunks)


def json_after(source: str, marker: str):
    position = source.find(marker)
    if position < 0:
        return None
    position += len(marker)
    while position < len(source) and source[position] not in "[{":
        position += 1
    opening = source[position]
    closing = "}" if opening == "{" else "]"
    depth = 0
    quoted = False
    escaped = False
    for end in range(position, len(source)):
        char = source[end]
        if quoted:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quoted = False
            continue
        if char == '"':
            quoted = True
        elif char == opening:
            depth += 1
        elif char == closing:
            depth -= 1
            if depth == 0:
                return json.loads(source[position : end + 1])
    raise ValueError(f"Unbalanced JSON after {marker}")


def json_objects_after(source: str, marker: str) -> list[dict]:
    values = []
    offset = 0
    while (position := source.find(marker, offset)) >= 0:
        try:
            value = json_after(source[position:], marker)
            if isinstance(value, dict):
                values.append(value)
        except (ValueError, json.JSONDecodeError):
            pass
        offset = position + len(marker)
    return values


def merge_missing(base: dict, extra: dict) -> dict:
    result = copy.deepcopy(base)
    for key, value in extra.items():
        if isinstance(result.get(key), dict) and isinstance(value, dict):
            result[key] = merge_missing(result[key], value)
        elif key not in result or result[key] is None:
            result[key] = copy.deepcopy(value)
    return result


def faqs(tree) -> list[dict]:
    data = json_ld(tree, "FAQPage") or {}
    return [
        {
            "question": item.get("name"),
            "answer_html": item.get("acceptedAnswer", {}).get("text"),
        }
        for item in data.get("mainEntity", [])
    ]


def parse_benefit_review(element) -> dict:
    review_id = int(re.search(r"benefit_review_id=(\d+)", element.get("data-brandviews")).group(1))
    rating = first_text(element, './/*[contains(@class,"BenefitReview_benefitRatingContainer")]//span[1]')
    helpful = first_text(element, './/button[@aria-label="Helpful"]')
    return {
        "id": review_id,
        "rating": float(rating) if rating else None,
        "date": first_text(element, './/*[contains(@class,"Timestamp_reviewDate")]'),
        "role": first_text(element, './/*[@data-test="content-avatar-label"]'),
        "tags": [text(tag) for tag in element.xpath('.//*[@data-test="content-avatar-tag"]')],
        "comment": first_text(element, './/*[contains(@class,"BenefitReview_benefitReviewText")]'),
        "helpful_display": helpful,
        "raw_text": text(element),
    }


def overview() -> dict:
    tree = document("cache/pages/overview-expanded.html")
    flight = flight_text(tree)
    employer_candidates = [
        value for value in json_objects_after(flight, '"employer":') if value.get("id") == 942627
    ]
    employer = {}
    for candidate in sorted(employer_candidates, key=len, reverse=True):
        employer = merge_missing(employer, candidate)
    employer["locationCount"] = len(employer.get("officeAddresses", []))
    employer["revenueDisplay"] = employer.get("revenue", "").removeprefix("$") or None
    ratings = json_after(flight, '"ratings":')
    benchmarks = json_after(flight, '"industryBenchmarkRatings":')
    distribution = json_after(flight, '"ratingCountDistribution":')

    awards = []
    for item in tree.xpath('//*[@data-test="employerAwardsModule"]//li'):
        year = first_text(item, 'preceding::p[contains(@class,"Awards_year")][1]')
        awards.append({"year": int(year), "text": text(item)})

    updates = []
    for card in tree.xpath('//*[@data-test="update-card"]'):
        brand = card.get("data-brandviews", "")
        match = re.search(r"(?:update_id=|card-)(\d+)", brand)
        updates.append(
            {
                "id": int(match.group(1)) if match else None,
                "text": text(card),
                "links": [urljoin(BASE, href) for href in card.xpath('.//a/@href')],
                "images": card.xpath('.//img/@src'),
            }
        )

    photos = []
    for card in tree.xpath('//*[@data-test and starts-with(@data-test,"photo-")]'):
        image = first(card, ".//img")
        photos.append(
            {
                "id": int(card.get("data-test").split("-")[1]),
                "caption": image.get("alt") if image is not None else None,
                "image_url": image.get("src") if image is not None else None,
            }
        )

    mini_reviews = []
    for card in tree.xpath('//*[@data-test and starts-with(@data-test,"reviewsModuleCarousel-card-")]'):
        href = first(card, './/a[contains(@href,"RVW")]/@href')
        mini_reviews.append({"text": text(card), "url": urljoin(BASE, href) if href else None})

    links = {}
    for name, needle in {
        "offices": "/Location/All-Gramener-Office-Locations",
        "company_updates": "/Updates/Gramener-Company-Updates",
        "photos": "/Photos/Gramener-Office-Photos",
        "reviews": "/Reviews/Gramener-Reviews",
    }.items():
        href = first(tree, f'//a[contains(@href,"{needle}")]/@href')
        links[name] = urljoin(BASE, href) if href else None

    return {
        "source_url": "https://www.glassdoor.co.in/Overview/Working-at-Gramener-EI_IE942627.11,19.htm",
        "company": employer,
        "organization": json_ld(tree, "Organization"),
        "aggregate_rating": json_ld(tree, "EmployerAggregateRating"),
        "ratings": ratings,
        "industry_benchmark_ratings": benchmarks,
        "rating_count_distribution": distribution,
        "faqs": faqs(tree),
        "awards": awards,
        "company_updates": updates,
        "photos": photos,
        "featured_employee_reviews": mini_reviews,
        "related_gramener_links": links,
    }


def merge_questions(employer_questions: list, public_questions: list) -> list:
    merged = []
    for index in range(max(len(employer_questions), len(public_questions))):
        base = copy.deepcopy(employer_questions[index]) if index < len(employer_questions) else {}
        extra = public_questions[index] if index < len(public_questions) else {}
        for key, value in extra.items():
            if key not in base or base[key] is None:
                base[key] = value
        merged.append(base)
    return merged


def reviews() -> dict:
    public_pages = [load_json(f"cache/api/employee-reviews-{page}.json") for page in range(1, 4)]
    graph_pages = [load_json(f"cache/api/employer-reviews-{page}.json") for page in range(1, 4)]
    public_summary = copy.deepcopy(public_pages[0]["data"]["employerReviews"])
    public_summary.pop("reviews", None)
    default_summary = load_json("cache/recon-review-api/redacted-response-samples.json")["public_bff"]["data"][
        "employerReviews"
    ]
    default_summary = {key: value for key, value in default_summary.items() if key != "reviews"}
    public = {
        row["reviewId"]: row
        for page in public_pages
        for row in page["data"]["employerReviews"]["reviews"]
    }
    graph = {
        row["reviewId"]: row
        for page in graph_pages
        for row in page["data"]["employerReviews"]["reviews"]
    }
    items = []
    for review_id in sorted(public, key=lambda key: public[key]["reviewDateTime"], reverse=True):
        item = copy.deepcopy(graph[review_id])
        for key, value in public[review_id].items():
            if key not in item or item[key] is None:
                item[key] = value
        item["url"] = f"{BASE}/Reviews/Employee-Review-Gramener-E942627-RVW{review_id}.htm"
        item["included_in_public_default_190"] = item.get("employmentStatus") not in {"INTERN", "CONTRACT"}
        item["lengthOfEmploymentDisplay"] = {
            0: "Not specified",
            1: "Less than 1 year",
            2: "1-2 years",
            4: "3-4 years",
            6: "5-7 years",
            9: "8-10 years",
            20: "More than 10 years",
        }.get(item.get("lengthOfEmployment"))
        items.append(item)
    return {
        "source_urls": {
            "public": f"{BASE}/Reviews/Gramener-Reviews-E942627.htm",
            "employer_view": f"{BASE}/employers/ec/reviews/employeeReviews.htm?currentPartnerId=205714&selectedEmployerId=942627&profileId=1118979",
        },
        "public_default_summary": default_summary,
        "all_reviews_summary": public_summary,
        "count_note": "The public default has 190 reviews; the unfiltered first-party endpoint has 208, adding 16 INTERN and 2 CONTRACT records.",
        "items": items,
    }


def interviews() -> dict:
    public_data = load_json("cache/interviews-recon/public-all.json")["data"]["employerInterviews"]
    public = {row["id"]: row for row in public_data["interviews"]}
    employer_pages = load_json("cache/interviews-recon/employer-all-pages.json")
    employer = {
        row["id"]: row
        for page in employer_pages
        for row in page["data"]["interviewReviews"]["interviews"]
    }
    items = []
    for interview_id in sorted(public, key=lambda key: public[key]["reviewDateTime"], reverse=True):
        item = copy.deepcopy(employer[interview_id])
        extra = public[interview_id]
        item["userQuestions"] = merge_questions(item.get("userQuestions", []), extra.get("userQuestions", []))
        for key, value in extra.items():
            if key == "userQuestions":
                continue
            if key not in item or item[key] is None:
                item[key] = value
            elif key == "location" and value:
                item[key] = item[key] | {k: v for k, v in value.items() if k not in item[key]}
        item["url"] = f"{BASE}/Interview/Gramener-Interview-E942627-RVW{interview_id}.htm"
        items.append(item)

    summary = {key: value for key, value in public_data.items() if key != "interviews"}
    summary["computed_average_difficulty"] = summary["difficultySum"] / summary["difficultySubmissionCount"]
    public_tree = document(
        "cache/initial/https-www-glassdoor-co-in-interview-gramener-interview-questions-e942627-htm.html"
    )
    return {
        "source_urls": {
            "public": f"{BASE}/Interview/Gramener-Interview-Questions-E942627.htm",
            "employer_view": f"{BASE}/employers/ec/reviews/interviewReviews.htm?currentPartnerId=205714&selectedEmployerId=942627&profileId=1118979",
        },
        "summary": summary,
        "displayed_summary": {
            "total_count": first_text(public_tree, '//*[@data-test="interview-total-count"]'),
            "difficulty": first_text(public_tree, '//*[@data-test="interview-difficulty-score"]'),
            "experience": first_text(public_tree, '//*[@data-test="interview-experience-container"]'),
            "sources": first_text(public_tree, '//*[@data-test="interview-source-container"]'),
        },
        "faqs": faqs(public_tree),
        "items": items,
    }


def pay_and_benefits() -> dict:
    pay_tree = document("cache/pages/pay-benefits-current.html")
    pay_flight = flight_text(pay_tree)
    categories = json_after(pay_flight, '"benefitsCategoryToStatisticAggregates":')
    card_urls = {}
    for card in pay_tree.xpath('//*[@data-test="benefit-category-card"]'):
        href = first(card, ".//a/@href") if card.tag != "a" else card.get("href")
        match = re.search(r"BNFT(\d+)", href or "")
        if match:
            card_urls[int(match.group(1))] = urljoin(BASE, href)
    benefit_categories = []
    for category in categories:
        benefits = []
        for statistic in category["benefitStatisticAggregateList"]:
            benefit = statistic["benefit"] | {
                key: value for key, value in statistic.items() if key != "benefit"
            }
            benefit["rating"] = (
                statistic["benefitRatingNumerator"] / statistic["benefitRatingDenominator"]
                if statistic["benefitRatingDenominator"]
                else None
            )
            benefit["url"] = card_urls.get(benefit["id"])
            benefits.append(benefit)
        benefit_categories.append({**category["benefitCategory"], "benefits": benefits})

    benefit_overview_pages = [
        document("cache/pages/benefits-overview-01.html"),
        document("cache/pages/benefits-overview-02.html"),
    ]
    general_reviews = []
    for tree in benefit_overview_pages:
        general_reviews.extend(
            parse_benefit_review(element)
            for element in tree.xpath(
                '//*[@data-brandviews and starts-with(@data-brandviews,"MODULE:n=benefits-reviews:eid=942627")]'
            )
        )

    details = []
    for path in sorted((ROOT / "cache/pages/benefit-details").glob("benefit-*.html")):
        tree = html.parse(path)
        benefit_id = int(path.stem.split("-")[1])
        aggregate = json_ld(tree, "EmployerAggregateRating")
        breadcrumb = json_ld(tree, "BreadcrumbList")
        info = [text(element) for element in tree.xpath('//*[contains(@class,"AboutBenefitsData_aboutOurDataItem")]')]
        reported = next((int(m.group(1)) for value in info if (m := re.search(r"(\d+) employees? reported", value))), None)
        updated = next((value.removeprefix("Updated ") for value in info if value.startswith("Updated ")), None)
        detail_reviews = [
            parse_benefit_review(element)
            for element in tree.xpath(
                '//*[@data-brandviews and starts-with(@data-brandviews,"MODULE:n=benefits-reviews:eid=942627")]'
            )
        ]
        details.append(
            {
                "id": benefit_id,
                "name": breadcrumb["itemListElement"][-1]["name"].removeprefix("Gramener ") if breadcrumb else None,
                "url": breadcrumb["itemListElement"][-1]["item"] if breadcrumb else card_urls.get(benefit_id),
                "aggregate_rating": aggregate,
                "employer_verified": "Employer Verified" in info,
                "updated": updated,
                "employees_reported": reported,
                "reviews": detail_reviews,
            }
        )

    salaries = load_json("cache/api/salary-estimates.json")["data"]["aggregatedSalaryEstimates"]
    pay_visible = visible_text(pay_tree)
    salary_count = re.search(r"([\d,]+) salaries in India", pay_visible)
    benefit_overview = json_ld(benefit_overview_pages[0], "EmployerAggregateRating")
    return {
        "source_url": f"{BASE}/pay-and-benefits/Gramener-E942627",
        "salary_summary": {
            "reported_salary_count_india": int(salary_count.group(1).replace(",", "")) if salary_count else None,
            "job_title_count": salaries["jobTitleCount"],
            "currency": "INR",
            "pay_period": "ANNUAL",
            "salary_page_url": f"{BASE}/Salary/Gramener-Salaries-E942627.htm",
        },
        "salary_estimates": salaries["results"],
        "benefits_summary": benefit_overview,
        "benefit_faqs": faqs(benefit_overview_pages[0]),
        "benefit_categories": benefit_categories,
        "general_benefit_reviews": general_reviews,
        "benefit_details": details,
    }


def build() -> dict:
    return {
        "extraction_metadata": {
            "company": "Gramener",
            "employer_id": 942627,
            "profile_id": 1118979,
            "extracted_at": datetime.now(UTC).isoformat(),
            "method": "Authenticated CDP-rendered HTML plus the same first-party JSON endpoints used by Glassdoor pages",
            "cache_directory": "cache",
            "excluded_content": [
                "global navigation/footer/account chrome",
                "generic Community/Fishbowl modules",
                "unrelated recommended/top-companies cards",
            ],
        },
        "overview": overview(),
        "reviews": reviews(),
        "pay_and_benefits": pay_and_benefits(),
        "interviews": interviews(),
    }


if __name__ == "__main__":
    (ROOT / "glassdoor.json").write_text(json.dumps(build(), indent=2, ensure_ascii=False) + "\n")
