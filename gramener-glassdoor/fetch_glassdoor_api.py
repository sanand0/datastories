#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["websockets>=15"]
# ///
"""Cache Glassdoor's authenticated first-party JSON responses without credentials."""

import asyncio
import json
import urllib.request
from pathlib import Path

import websockets

CDP_HTTP = "http://localhost:9222"
CACHE = Path("cache/api")


def glassdoor_target() -> dict:
    with urllib.request.urlopen(f"{CDP_HTTP}/json/list") as response:
        pages = json.load(response)
    return next(
        page
        for page in pages
        if "glassdoor.co.in" in page["url"] and page["title"] != "Just a moment..."
    )


class CDP:
    def __init__(self, ws):
        self.ws = ws
        self.request_id = 0

    async def evaluate(self, expression: str):
        self.request_id += 1
        request_id = self.request_id
        await self.ws.send(
            json.dumps(
                {
                    "id": request_id,
                    "method": "Runtime.evaluate",
                    "params": {"expression": expression, "awaitPromise": True, "returnByValue": True},
                }
            )
        )
        while True:
            message = json.loads(await self.ws.recv())
            if message.get("id") == request_id:
                result = message["result"]["result"]
                if result.get("subtype") == "error":
                    raise RuntimeError(result.get("description"))
                return result.get("value")

    async def post(self, url: str, payload: dict) -> dict:
        options = {
            "method": "POST",
            "headers": {"content-type": "application/json"},
            "body": json.dumps(payload),
        }
        value = await self.evaluate(
            f"fetch({json.dumps(url)},{json.dumps(options)}).then(async r=>"
            "JSON.stringify({status:r.status,body:await r.json()}))"
        )
        response = json.loads(value)
        if response["status"] != 200:
            raise RuntimeError(f"POST {url} returned {response['status']}: {response['body']}")
        return response["body"]


async def main() -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    target = glassdoor_target()
    async with websockets.connect(target["webSocketDebuggerUrl"], max_size=None) as ws:
        cdp = CDP(ws)
        review_payload = {
            "applyDefaultCriteria": False,
            "employerId": 942627,
            "employmentStatuses": [],
            "jobTitle": None,
            "goc": None,
            "location": {},
            "defaultLanguage": "eng",
            "language": "eng",
            "mlHighlightSearch": None,
            "onlyCurrentEmployees": False,
            "overallRating": None,
            "pageSize": 100,
            "page": 1,
            "preferredTldId": 0,
            "reviewCategories": [],
            "sort": "DATE",
            "textSearch": "",
            "worldwideFilter": False,
            "dynamicProfileId": 1118979,
            "useRowProfileTldForRatings": False,
            "enableKeywordSearch": False,
        }
        for page in range(1, 4):
            print(f"Fetching all employee reviews page {page}", flush=True)
            body = await cdp.post(
                "/bff/employer-profile-mono/employer-reviews", review_payload | {"page": page}
            )
            (CACHE / f"employee-reviews-{page}.json").write_text(
                json.dumps(body, indent=2, ensure_ascii=False)
            )

        print("Fetching all aggregate salaries", flush=True)
        salaries = await cdp.post(
            "/bff/employer-profile-mono/agg-salary-estimates",
            {
                "sort": "UGC_SALARY_COUNT_DESC",
                "sgoc": None,
                "payPeriod": "ANNUAL",
                "pageSize": 200,
                "page": 1,
                "jobTitle": "",
                "employerId": 942627,
            },
        )
        (CACHE / "salary-estimates.json").write_text(json.dumps(salaries, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
