import asyncio
import pyppeteer
import subprocess
import json


async def main():
    ws_data = subprocess.check_output(
        ["curl", "-s", "http://localhost:9222/json/version"], text=True
    )
    ws_url = json.loads(ws_data)["webSocketDebuggerUrl"]
    browser = await pyppeteer.connect(browserWSEndpoint=ws_url)
    pages = await browser.pages()
    target_url = "http://localhost:8000/opencode/ai_productivity_charts.html"
    page = None
    for p in pages:
        if p.url == target_url:
            page = p
            break
    if not page:
        print("Page not found")
        await browser.close()
        return
    errors = []

    def on_console(msg):
        if msg.type == "error":
            errors.append(f"Console error: {msg.text}")

    def on_error(err):
        errors.append(f"JavaScript error: {err}")

    page.on("console", on_console)
    page.on("pageerror", on_error)

    # Take screenshot
    await page.screenshot({"path": "screenshot.png"})
    await browser.close()

    if errors:
        print("Issues found:")
        for error in errors:
            print(error)
    else:
        print("No errors found")
    print("Screenshot saved as screenshot.png")


asyncio.run(main())
