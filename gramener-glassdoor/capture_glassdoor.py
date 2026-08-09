#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["websockets>=15"]
# ///
"""Cache authenticated Glassdoor pages through a single live CDP tab."""

import asyncio
import json
import re
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

import websockets

CDP_HTTP = "http://localhost:9222"
CACHE = Path("cache/pages")
OVERVIEW = "https://www.glassdoor.co.in/Overview/Working-at-Gramener-EI_IE942627.11,19.htm"
PAY = "https://www.glassdoor.co.in/pay-and-benefits/Gramener-E942627"
REVIEWS = "https://www.glassdoor.co.in/Reviews/Gramener-Reviews-E942627{page}.htm"
INTERVIEWS = "https://www.glassdoor.co.in/Interview/Gramener-Interview-Questions-E942627{page}.htm"


class CDP:
    """Minimal request/response client for one page target."""

    def __init__(self, ws):
        self.ws = ws
        self.request_id = 0

    async def call(self, method: str, params: dict | None = None) -> dict:
        self.request_id += 1
        request_id = self.request_id
        await self.ws.send(json.dumps({"id": request_id, "method": method, "params": params or {}}))
        while True:
            message = json.loads(await self.ws.recv())
            if message.get("id") == request_id:
                if "error" in message:
                    raise RuntimeError(message["error"])
                return message["result"]

    async def evaluate(self, expression: str, *, await_promise: bool = False):
        result = await self.call(
            "Runtime.evaluate",
            {"expression": expression, "returnByValue": True, "awaitPromise": await_promise},
        )
        return result["result"].get("value")


def new_target() -> dict:
    request = urllib.request.Request(f"{CDP_HTTP}/json/new?about:blank", method="PUT")
    with urllib.request.urlopen(request) as response:
        return json.load(response)


def slug(section: str, page: int | None = None) -> str:
    return f"{section}-{page:02d}" if page is not None else section


async def ready(cdp: CDP, expected: str | None) -> dict:
    """Wait for hydrated content, not just the browser load event."""
    for _ in range(90):
        state = json.loads(
            await cdp.evaluate(
                "JSON.stringify({ready:document.readyState,url:location.href,title:document.title,"
                "textLength:document.body?.innerText.length||0,expected:"
                f"{json.dumps(expected)}?document.querySelectorAll({json.dumps(expected)}).length:1}})"
            )
        )
        if state["ready"] == "complete" and state["textLength"] > 1000 and state["expected"]:
            return state
        await asyncio.sleep(0.5)
    raise TimeoutError(f"Page did not hydrate: {state}")


async def expand(cdp: CDP) -> dict:
    """Collect tooltip-only subratings and expand truncation controls."""
    return json.loads(
        await cdp.evaluate(
            """(async()=>{
              scrollTo(0,document.body.scrollHeight); await new Promise(r=>setTimeout(r,300));
              const clickText=/^(show|read|see) more$/i;
              for(const button of document.querySelectorAll('button')) {
                if(clickText.test(button.innerText.trim())) button.click();
              }
              const subratings=[];
              for(const caret of document.querySelectorAll('[data-test="review-subratings-caret-tooltip"]')) {
                const review=caret.closest('[data-test="review-detail"]');
                caret.click(); await new Promise(r=>setTimeout(r,80));
                const candidates=[...document.querySelectorAll('[role="tooltip"], [data-radix-popper-content-wrapper]')];
                const tooltip=candidates.at(-1);
                subratings.push({review_id:review?.dataset.brandviews?.match(/review_id=(\\d+)/)?.[1]??null,
                  text:tooltip?.innerText.trim()??null,html:tooltip?.innerHTML??null});
                caret.click();
              }
              scrollTo(0,0);
              return JSON.stringify({subratings});
            })()""",
            await_promise=True,
        )
    )


async def capture(cdp: CDP, section: str, url: str, expected: str | None, page: int | None = None) -> dict:
    print(f"Capturing {section}{f' page {page}' if page else ''}: {url}", flush=True)
    await cdp.call("Page.navigate", {"url": url})
    state = await ready(cdp, expected)
    expanded = await expand(cdp)
    html = await cdp.evaluate("document.documentElement.outerHTML")
    record_ids = sorted(set(re.findall(r"(?:review_id=|Review|Interview)(\d{7,})", html)))
    name = slug(section, page)
    CACHE.mkdir(parents=True, exist_ok=True)
    (CACHE / f"{name}.html").write_text(html)
    metadata = {
        **state,
        "requested_url": url,
        "captured_at": datetime.now(UTC).isoformat(),
        "bytes": len(html.encode()),
        "record_ids": record_ids,
        "expanded": expanded,
    }
    (CACHE / f"{name}.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False))
    return metadata


async def main() -> None:
    target = new_target()
    async with websockets.connect(target["webSocketDebuggerUrl"], max_size=None) as ws:
        cdp = CDP(ws)
        await cdp.call("Page.enable")
        manifest = [
            await capture(cdp, "overview", OVERVIEW, "h1"),
            await capture(cdp, "pay-benefits", PAY, '[data-test="overall-benefit-rating"]'),
        ]
        for page in range(1, 39):
            suffix = "" if page == 1 else f"_P{page}"
            manifest.append(
                await capture(cdp, "reviews", REVIEWS.format(page=suffix), '[data-test="review-detail"]', page)
            )
        for page in range(1, 10):
            suffix = "" if page == 1 else f"_P{page}"
            manifest.append(
                await capture(
                    cdp,
                    "interviews",
                    INTERVIEWS.format(page=suffix),
                    '[data-brandviews*="interview_id="]',
                    page,
                )
            )
        (CACHE / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
        print(f"Captured {len(manifest)} pages in {CACHE}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
