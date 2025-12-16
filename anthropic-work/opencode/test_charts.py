import asyncio
from playwright.async_api import async_playwright
import os


async def main():
    async with async_playwright() as p:
        # Connect to existing Chrome instance
        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        pages = browser.contexts[0].pages
        target_url = "http://localhost:8000/opencode/ai_productivity_charts.html"
        page = None

        for p in pages:
            if p.url == target_url:
                page = p
                break

        if not page:
            print("Page not found, navigating to it...")
            page = await browser.contexts[0].new_page()
            await page.goto(target_url)
            await page.wait_for_selector(".container", timeout=10000)
        else:
            print("Page found, using existing tab")

        errors = []

        def on_console(msg):
            if msg.type == "error":
                errors.append(f"Console error: {msg.text}")

        def on_error(err):
            errors.append(f"JavaScript error: {err}")

        page.on("console", on_console)
        page.on("pageerror", on_error)

        # Wait for page to load completely
        await page.wait_for_function('typeof d3 !== "undefined"', timeout=30000)
        await asyncio.sleep(2)

        # Test each tab and take screenshots
        tabs = [
            ("Full-Stack Capabilities", 0, ["radial", "treemap", "force-directed"]),
            ("Accelerated Learning", 1, ["radar", "waterfall", "sankey"]),
            ("Tackling Neglected Tasks", 2, ["heat map", "spider", "chord"]),
        ]

        print("Testing xenographic charts rendering...")

        for tab_name, tab_index, chart_types in tabs:
            print(f"Switching to {tab_name} tab...")

            # Switch to tab
            await page.evaluate(f"showTab({tab_index})")

            # Wait for charts to potentially render
            await asyncio.sleep(3)

            # Take screenshot of the tab
            await page.screenshot(
                path=f"screenshot_tab_{tab_index}_{'_'.join(chart_types).replace(' ', '_')}.png",
                full_page=True,
            )
            print(f"Screenshot saved for {tab_name}")

        await browser.close()

        print("\n=== TEST REPORT ===")

        if errors:
            print("ISSUES FOUND:")
            print("Console/JavaScript Errors detected:")
            for error in errors[:5]:  # Show first 5 errors
                print(f"  - {error}")
            if len(errors) > 5:
                print(f"  ... and {len(errors) - 5} more errors")
            print(
                "\nThis indicates that the xenographic chart functions are failing to execute properly."
            )
            print(
                "The charts (radial, treemap, force-directed, radar, waterfall, sankey, heat map, spider, chord) are not rendering."
            )
        else:
            print("✓ No console or JavaScript errors detected")

        # List all screenshot files
        screenshots = [
            f
            for f in os.listdir(".")
            if f.startswith("screenshot_tab_") and f.endswith(".png")
        ]
        if screenshots:
            print(f"\nScreenshots taken: {len(screenshots)} files")
            for shot in sorted(screenshots):
                print(f"  - {shot}")

        print("\nSUMMARY:")
        if errors:
            print(
                "❌ Xenographic charts have rendering issues - JavaScript errors prevent proper display"
            )
        else:
            print(
                "✅ Page loads without errors, but manual verification of chart rendering needed"
            )


if __name__ == "__main__":
    asyncio.run(main())
