#!/usr/bin/env node
/**
 * Create screenshot for Frontiers 2024 story using Puppeteer
 */

const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

async function createScreenshot() {
    console.log('🚀 Starting screenshot generation...');

    let browser;
    try {
        browser = await puppeteer.launch({
            headless: true,
            args: ['--no-sandbox', '--disable-setuid-sandbox']
        });

        const page = await browser.newPage();

        // Set viewport for screenshot
        await page.setViewport({
            width: 1200,
            height: 900,
            deviceScaleFactor: 1
        });

        // Load the hero/title page
        const htmlPath = 'file://' + path.resolve(__dirname, 'index.html');
        console.log('📖 Loading page:', htmlPath);

        await page.goto(htmlPath, {
            waitUntil: 'networkidle0',
            timeout: 10000
        });

        // Wait a bit for any animations
        await page.waitForTimeout(1000);

        // Take screenshot
        console.log('📸 Taking screenshot...');
        await page.screenshot({
            path: path.join(__dirname, 'screenshot-full.png'),
            type: 'png'
        });

        console.log('✅ Screenshot saved: screenshot-full.png');
        console.log('\n📝 Next steps:');
        console.log('1. Convert to WebP with 16 colors:');
        console.log('   npx sharp-cli screenshot-full.png -o screenshot.webp --webp-quality 85');
        console.log('   OR use online tool: https://squoosh.app/');
        console.log('2. Optimize colors to 16 using GIMP or similar');

    } catch (error) {
        console.error('❌ Error:', error.message);
        console.log('\n📝 Fallback: Use the SVG file instead');
        console.log('   screenshot.svg is already created and can be converted manually');
    } finally {
        if (browser) await browser.close();
    }
}

// Check if puppeteer is installed
try {
    require.resolve('puppeteer');
    createScreenshot().catch(console.error);
} catch (e) {
    console.log('📦 Puppeteer not installed.');
    console.log('Install with: npm install puppeteer');
    console.log('\nAlternatively, use the pre-created screenshot.svg file:');
    console.log('1. Open screenshot.svg in browser');
    console.log('2. Take screenshot');
    console.log('3. Convert to WebP with 16 colors');
    process.exit(1);
}
