#!/usr/bin/env python3
"""
Create a minimal WebP placeholder
"""
import base64

# This is a minimal valid WebP file (16x16 solid color)
# Generated from a simple image and base64 encoded
# Dark blue color to match the story theme
minimal_webp_base64 = """
UklGRiQAAABXRUJQVlA4IBgAAAAwAQCdASoQABAAAwA0JaQAA3AA/vuUAAA=
"""

# Decode and write
webp_data = base64.b64decode(minimal_webp_base64.strip())

with open('/home/user/datastories/frontiers-2024/screenshot-placeholder.webp', 'wb') as f:
    f.write(webp_data)

print("Created minimal WebP placeholder: screenshot-placeholder.webp")
print("This is a 16x16 placeholder. For production, please:")
print("1. Open frontiers-2024/index.html in a browser")
print("2. Take a screenshot of the hero section or strategic pivot chart")
print("3. Save as screenshot.webp with 16 colors using:")
print("   - https://squoosh.app/ (online optimizer)")
print("   - GIMP: Mode → Indexed (16 colors) → Export as WebP")
print("   - ImageMagick: convert image.png -colors 16 screenshot.webp")
