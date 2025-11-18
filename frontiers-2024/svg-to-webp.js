#!/usr/bin/env node
const sharp = require('sharp');
const fs = require('fs');
const path = require('path');

async function convertSvgToWebP() {
    const svgPath = path.join(__dirname, 'screenshot.svg');
    const webpPath = path.join(__dirname, 'screenshot.webp');

    console.log('🎨 Converting SVG to WebP...');
    console.log('Input:', svgPath);
    console.log('Output:', webpPath);

    try {
        await sharp(svgPath, { density: 150 })
            .resize(800, 600)
            .webp({
                quality: 85,
                effort: 6
            })
            .toFile(webpPath);

        const stats = fs.statSync(webpPath);
        console.log(`✅ Created ${webpPath}`);
        console.log(`📦 Size: ${(stats.size / 1024).toFixed(2)} KB`);

        // Note: sharp doesn't directly support color reduction
        // The 16-color constraint would need additional processing
        console.log('\n📝 Note: For 16-color optimization, use:');
        console.log('   - https://squoosh.app/');
        console.log('   - ImageMagick: convert screenshot.webp -colors 16 screenshot-16c.webp');
        console.log('   - GIMP: Open → Mode → Indexed (16 colors) → Export');

    } catch (error) {
        console.error('❌ Error:', error.message);
        process.exit(1);
    }
}

convertSvgToWebP();
