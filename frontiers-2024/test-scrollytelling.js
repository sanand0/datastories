/**
 * Test script for Frontiers scrollytelling story
 * Uses Playwright to test scroll behavior and take screenshots
 */

const { chromium } = require('playwright');
const path = require('path');

async function testScrollytelling() {
    console.log('🚀 Starting scrollytelling test...');

    const browser = await chromium.launch({ headless: true });
    const context = await browser.newContext({
        viewport: { width: 1920, height: 1080 }
    });
    const page = await context.newPage();

    // Enable console logging from the page
    page.on('console', msg => console.log('PAGE LOG:', msg.text()));
    page.on('pageerror', error => console.error('PAGE ERROR:', error));

    try {
        // Load the page
        const filePath = 'file://' + path.resolve(__dirname, 'index.html');
        console.log('📖 Loading page:', filePath);
        await page.goto(filePath, { waitUntil: 'networkidle' });

        // Wait for visualization libraries to load
        await page.waitForTimeout(2000);

        // Take hero screenshot
        console.log('📸 Taking hero screenshot...');
        await page.screenshot({
            path: path.join(__dirname, 'screenshot-hero.png'),
            fullPage: false
        });

        // Check that steps exist
        const stepCount = await page.locator('.step').count();
        console.log(`✅ Found ${stepCount} step elements`);

        if (stepCount === 0) {
            throw new Error('No .step elements found!');
        }

        // Test scrolling through each step
        const steps = ['intro', 'crisis', 'choice', 'weapon', 'resistance', 'results',
                      'impact', 'institutional', 'broader', 'industry', 'future', 'caveats', 'conclusion'];

        for (let i = 0; i < steps.length; i++) {
            const stepName = steps[i];
            console.log(`\n📜 Testing step ${i + 1}/${steps.length}: ${stepName}`);

            // Scroll to the step
            await page.locator(`[data-step="${stepName}"]`).scrollIntoViewIfNeeded();
            await page.waitForTimeout(800); // Wait for animation

            // Check if step is active
            const isActive = await page.locator(`[data-step="${stepName}"]`).evaluate(
                el => el.classList.contains('active')
            );
            console.log(`  ${isActive ? '✅' : '❌'} Step is ${isActive ? 'active' : 'NOT active'}`);

            // Check if chart container has content
            const chartHasContent = await page.locator('#chart-container').evaluate(
                el => el.innerHTML.trim().length > 0
            );
            console.log(`  ${chartHasContent ? '✅' : '❌'} Chart has ${chartHasContent ? 'content' : 'NO content'}`);

            // Take screenshot
            const screenshotPath = path.join(__dirname, `screenshot-${stepName}.png`);
            await page.screenshot({ path: screenshotPath, fullPage: false });
            console.log(`  📸 Screenshot saved: screenshot-${stepName}.png`);
        }

        // Scroll to bottom to test methodology and footer
        console.log('\n📜 Scrolling to methodology section...');
        await page.locator('.methodology').scrollIntoViewIfNeeded();
        await page.waitForTimeout(500);
        await page.screenshot({
            path: path.join(__dirname, 'screenshot-methodology.png'),
            fullPage: false
        });

        // Create the main screenshot for config.json
        console.log('\n📸 Creating main screenshot for listing...');
        await page.locator('.hero').scrollIntoViewIfNeeded();
        await page.waitForTimeout(500);
        await page.screenshot({
            path: path.join(__dirname, 'screenshot.webp'),
            type: 'webp',
            quality: 85,
            fullPage: false
        });

        console.log('\n✅ All tests completed successfully!');
        console.log('📁 Screenshots saved in frontiers-2024/');

    } catch (error) {
        console.error('❌ Test failed:', error);
        throw error;
    } finally {
        await browser.close();
    }
}

// Run tests if executed directly
if (require.main === module) {
    testScrollytelling()
        .then(() => {
            console.log('\n🎉 Testing complete!');
            process.exit(0);
        })
        .catch(error => {
            console.error('\n💥 Testing failed:', error);
            process.exit(1);
        });
}

module.exports = { testScrollytelling };
