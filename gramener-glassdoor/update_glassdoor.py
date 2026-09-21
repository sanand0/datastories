#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["lxml>=6", "websockets>=15"]
# ///
"""Refresh the cached Glassdoor data and rebuild glassdoor.json safely.

Each page and API response is a checkpoint.  A failed run leaves the previous
cache and glassdoor.json usable; resume it with the run id printed at start.
"""

import argparse
import asyncio
import json
import os
import tempfile
import uuid
from datetime import UTC, datetime
from pathlib import Path

import capture_glassdoor
import fetch_glassdoor_api
from extract_glassdoor import build
import websockets

ROOT = Path(__file__).parent
CACHE = ROOT / "cache"
STATE_PATH = CACHE / "update-state.json"
OVERVIEW = "https://www.glassdoor.co.in/Overview/Working-at-Gramener-EI_IE942627.11,19.htm"
PAY = "https://www.glassdoor.co.in/pay-and-benefits/Gramener-E942627"
REVIEWS = "https://www.glassdoor.co.in/Reviews/Gramener-Reviews-E942627{page}.htm"
INTERVIEWS = "https://www.glassdoor.co.in/Interview/Gramener-Interview-Questions-E942627{page}.htm"
EMPLOYER_REVIEWS = "https://www.glassdoor.co.in/employers/ec/reviews/employeeReviews.htm?currentPartnerId=205714&selectedEmployerId=942627&profileId=1118979"
GRAPH_QUERY = """
query GetEmployerReviews($language: String!, $languageOverrides: [String], $employerId: Int!, $employmentStatuses: [EmploymentStatusEnum], $onlyCurrentEmployees: Boolean, $onlyFormerEmployees: Boolean, $location: LocationIdent, $overallRating: FiveStarRatingEnum, $page: Int!, $pageSize: Int!, $sort: ReviewsSortOrderEnum, $ceoApprovalCriteria: [CeoRatingEnum], $businessOutlookCriteria: [SentimentEnum], $hasEmployerResponse: Boolean, $recommendToFriendCriteria: [RecommendToFriendEnum], $textSearch: String, $dynamicProfileId: Int) {
  employerReviews: employerReviewsRG(employerReviewsInput: {language: $language, languageOverrides: $languageOverrides, employer: {id: $employerId}, employmentStatuses: $employmentStatuses, onlyCurrentEmployees: $onlyCurrentEmployees, onlyFormerEmployees: $onlyFormerEmployees, location: $location, overallRating: $overallRating, page: {num: $page, size: $pageSize}, sort: $sort, ceoApprovalCriteria: $ceoApprovalCriteria, businessOutlookCriteria: $businessOutlookCriteria, hasEmployerResponse: $hasEmployerResponse, recommendToFriendCriteria: $recommendToFriendCriteria, textSearch: $textSearch, dynamicProfileId: $dynamicProfileId}) {
    allReviewsCount currentPage numberOfPages filteredReviewsCount reviews {
      advice adviceOriginal cons consOriginal countHelpful countNotHelpful employmentStatus featured flaggingDisabled isCurrentJob languageId lengthOfEmployment originalLanguageId pros prosOriginal ratingBusinessOutlook ratingCareerOpportunities ratingCeo ratingCompensationAndBenefits ratingCultureAndValues ratingDiversityAndInclusion ratingOverall ratingRecommendToFriend ratingSeniorLeadership ratingWorkLifeBalance reviewDateTime reviewId summary summaryOriginal viewsCount
      employer { id largeLogoUrl: squareLogoUrl(size: LARGE) regularLogoUrl: squareLogoUrl(size: REGULAR) shortName }
      employerResponses { id countHelpful countNotHelpful languageId originalLanguageId response responseDateTime(format: ISO) responseOriginal translationMethod }
      jobTitle { id text } location { id type name }
    }
  }
}
"""


def atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w") as stream:
            json.dump(value, stream, indent=2, ensure_ascii=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise


def log(message: str) -> None:
    print(message, flush=True)


def task_names() -> list[str]:
    return ["overview", "pay-benefits"] + [f"reviews-{p}" for p in range(1, 39)] + [
        f"interviews-{p}" for p in range(1, 10)
    ]


def new_state() -> dict:
    run_id = uuid.uuid4().hex[:12]
    return {
        "run_id": run_id,
        "started_at": datetime.now(UTC).isoformat(),
        "tasks": {task: "pending" for task in task_names()},
        "api": {"employee": {}, "employer": {}, "salary": "pending"},
        "build": "pending",
    }


def load_state(run_id: str | None, *, persist: bool = True) -> dict:
    if run_id is None:
        state = new_state()
        if persist:
            atomic_json(STATE_PATH, state)
        log(f"Starting Glassdoor update run {state['run_id']}")
        return state
    state = json.loads(STATE_PATH.read_text())
    if state.get("run_id") != run_id:
        raise SystemExit(f"Cannot resume {run_id}: {STATE_PATH} contains {state.get('run_id')!r}")
    log(f"Resuming Glassdoor update run {run_id}")
    return state


def save_state(state: dict) -> None:
    atomic_json(STATE_PATH, state)


async def capture_pages(state: dict, dry_run: bool) -> None:
    if dry_run:
        for name in state["tasks"]:
            if state["tasks"][name] != "done":
                log(f"Would capture {name}")
        return
    target = capture_glassdoor.new_target()
    async with websockets.connect(target["webSocketDebuggerUrl"], max_size=None) as ws:
        cdp = capture_glassdoor.CDP(ws)
        await cdp.call("Page.enable")
        pages = [
            ("overview", OVERVIEW, "h1", None),
            ("pay-benefits", PAY, '[data-test="overall-benefit-rating"]', None),
        ]
        pages += [
            (f"reviews-{page}", REVIEWS.format(page="" if page == 1 else f"_P{page}"), '[data-test="review-detail"]', page)
            for page in range(1, 39)
        ]
        pages += [
            (f"interviews-{page}", INTERVIEWS.format(page="" if page == 1 else f"_P{page}"), '[data-brandviews*="interview_id="]', page)
            for page in range(1, 10)
        ]
        stopped_groups = set()
        for name, url, expected, page in pages:
            group = name.split("-", 1)[0]
            if group in stopped_groups:
                continue
            if state["tasks"][name] == "done":
                continue
            log(f"Capturing {name}: {url}")
            try:
                section = {"overview": "overview-expanded", "pay-benefits": "pay-benefits-current"}.get(
                    name, name.split("-")[0]
                )
                await capture_glassdoor.capture(cdp, section, url, expected, page)
            except TimeoutError:
                if name.startswith("reviews-") or name.startswith("interviews-"):
                    log(f"No more {name.split('-')[0]} pages after {name}; leaving later pages pending")
                    stopped_groups.add(group)
                    continue
                raise
            state["tasks"][name] = "done"
            save_state(state)


async def fetch_api(state: dict, dry_run: bool) -> None:
    if dry_run:
        log("Would refresh employee/employer review API pages and salary estimates")
        return
    target = capture_glassdoor.new_target()
    async with websockets.connect(target["webSocketDebuggerUrl"], max_size=None) as ws:
        cdp = fetch_glassdoor_api.CDP(ws)
        await cdp.evaluate(f"location.href={json.dumps(OVERVIEW)}")
        await capture_glassdoor.ready(cdp, "h1")
        payload = {
            "applyDefaultCriteria": False, "employerId": 942627, "employmentStatuses": [],
            "jobTitle": None, "goc": None, "location": {}, "defaultLanguage": "eng",
            "language": "eng", "mlHighlightSearch": None, "onlyCurrentEmployees": False,
            "overallRating": None, "pageSize": 100, "preferredTldId": 0, "page": 1,
            "reviewCategories": [], "sort": "DATE", "textSearch": "", "worldwideFilter": False,
            "dynamicProfileId": 1118979, "useRowProfileTldForRatings": False,
            "enableKeywordSearch": False,
        }
        token = await cdp.evaluate(
            "(document.documentElement.outerHTML.match(/\\\\?\"gdToken\\\\?\":\\\\?\"([^\"\\\\]+)/)||[])[1]||null"
        )
        if not token:
            log("Checking Employer Centre for the GraphQL review token")
            await cdp.evaluate(f"location.href={json.dumps(EMPLOYER_REVIEWS)}")
            try:
                await capture_glassdoor.ready(cdp, "body")
            except TimeoutError:
                pass
            token = await cdp.evaluate(
                "(document.documentElement.outerHTML.match(/\\\\?\"gdToken\\\\?\":\\\\?\"([^\"\\\\]+)/)||[])[1]||null"
            )
        if not token:
            log("Employer GraphQL source is not authenticated; preserving its existing cache")
        await cdp.evaluate(f"location.href={json.dumps(OVERVIEW)}")
        await capture_glassdoor.ready(cdp, "h1")
        graph_variables = {
                "language": "eng", "languageOverrides": ["eng", "fra", "deu", "nld", "por", "spa", "ita"],
                "employerId": 942627, "employmentStatuses": [], "onlyCurrentEmployees": False,
                "onlyFormerEmployees": False, "location": None, "overallRating": None,
                "pageSize": 100, "sort": "DATE", "ceoApprovalCriteria": [],
                "businessOutlookCriteria": [], "hasEmployerResponse": None,
                "recommendToFriendCriteria": [], "textSearch": "", "dynamicProfileId": 1118979,
            }
        for page in range(1, 11):
                requests = [("employee", "/bff/employer-profile-mono/employer-reviews", payload | {"page": page})]
                if token:
                    requests.append(("employer", "/graph", {"query": GRAPH_QUERY, "variables": graph_variables | {"page": page}}))
                for kind, endpoint, body in requests:
                    if state["api"][kind].get(str(page)) == "done":
                        continue
                    log(f"Fetching {kind} reviews page {page}")
                    if kind == "employer":
                        result = json.loads(await cdp.evaluate(
                            f"fetch('/graph',{json.dumps({'method': 'POST', 'headers': {'content-type': 'application/json', 'gd-csrf-token': token}, 'body': json.dumps(body)})}).then(async r=>JSON.stringify(await r.json()))"
                        ))
                    else:
                        result = await cdp.post(endpoint, body)
                    atomic_json(CACHE / "api" / f"{kind}-reviews-{page}.json", result)
                    state["api"][kind][str(page)] = "done"
                    save_state(state)
                    if not result.get("data", {}).get("employerReviews", {}).get("reviews"):
                        break
                else:
                    continue
                break
        log("Fetching aggregate salaries")
        if state["api"]["salary"] != "done":
            result = await cdp.post("/bff/employer-profile-mono/agg-salary-estimates", {
                "sort": "UGC_SALARY_COUNT_DESC", "sgoc": None, "payPeriod": "ANNUAL",
                "pageSize": 200, "page": 1, "jobTitle": "", "employerId": 942627,
            })
            atomic_json(CACHE / "api" / "salary-estimates.json", result)
            state["api"]["salary"] = "done"
            save_state(state)


def rebuild(state: dict, dry_run: bool) -> None:
    log("Rebuilding glassdoor.json from the completed cache")
    if dry_run:
        return
    value = build()
    atomic_json(ROOT / "glassdoor.json", value)
    state["build"] = "done"
    save_state(state)


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resume", metavar="RUN_ID", help="resume the run id printed by an earlier invocation")
    parser.add_argument("--dry-run", action="store_true", help="show planned actions without writing cache or output")
    parser.add_argument("--skip-capture", action="store_true")
    parser.add_argument("--skip-api", action="store_true")
    args = parser.parse_args()
    state = load_state(args.resume, persist=not args.dry_run)
    if not args.skip_capture:
        await capture_pages(state, args.dry_run)
    if not args.skip_api:
        await fetch_api(state, args.dry_run)
    rebuild(state, args.dry_run)
    log(f"Update run {state['run_id']} finished")


if __name__ == "__main__":
    asyncio.run(main())
