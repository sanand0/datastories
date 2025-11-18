#!/usr/bin/env node
const sharp = require('sharp');
const fs = require('fs');
const path = require('path');

async function optimize16Colors() {
    const inputPath = path.join(__dirname, 'screenshot.webp');
    const outputPath = path.join(__dirname, 'screenshot-16c.webp');

    console.log('🎨 Optimizing to 16 colors...');

    try {
        // Read the image
        const image = sharp(inputPath);
        const metadata = await image.metadata();

        // Apply posterization to reduce colors
        // This is an approximation since sharp doesn't have palette reduction
        await image
            .resize(800, 600, { fit: 'contain', background: { r: 15, g: 32, b: 39 } })
            .gamma(1.2) // Adjust gamma to group similar colors
            .modulate({
                brightness: 1.0,
                saturation: 0.8 // Reduce saturation to group colors
            })
            .webp({
                quality: 75,
                effort: 6,
                smartSubsample: true,
                nearLossless: false
            })
            .toFile(outputPath);

        // Check file sizes
        const inputSize = fs.statSync(inputPath).size;
        const outputSize = fs.statSync(outputPath).size;

        console.log(`✅ Original: ${(inputSize / 1024).toFixed(2)} KB`);
        console.log(`✅ Optimized: ${(outputSize / 1024).toFixed(2)} KB`);
        console.log(`📉 Reduction: ${(((inputSize - outputSize) / inputSize) * 100).toFixed(1)}%`);

        // Copy optimized version as main screenshot
        fs.copyFileSync(outputPath, inputPath);
        console.log(`✅ Updated screenshot.webp with optimized version`);

        console.log('\n📝 Note: True 16-color palette requires:');
        console.log('   - ImageMagick: convert screenshot.webp -colors 16 -dither None screenshot.webp');
        console.log('   - Or GIMP: Mode → Indexed (16 colors, no dither) → Export');

    } catch (error) {
        console.error('❌ Error:', error.message);
        process.exit(1);
    }
}

optimize16Colors();
