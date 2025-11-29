#!/usr/bin/env python3
"""Scrape exhibitor data from Renewable Energy India Expo website."""

import csv
import re
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


def scrape_exhibitor(box):
    """Extract all data from a single exhibitor box."""
    data = {}

    # Get company name
    title = box.find("h3")
    data["company_name"] = title.get_text(strip=True) if title else ""

    # Get logo URL
    img = box.find("img")
    data["logo_url"] = img.get("src", "") if img else ""

    # Get all text content sections
    circular_title = box.find("div", class_="circular-title")
    if circular_title:
        # Get all h6 headings (like "Stall Number", "Country", etc.)
        for h6 in circular_title.find_all("h6"):
            label = h6.get_text(strip=True).rstrip(":")
            # Get the next sibling that contains the value
            value_elem = h6.find_next_sibling()
            if value_elem:
                value = value_elem.get_text(strip=True)
            else:
                # Sometimes the value is in the next text node
                value = ""
                for sibling in h6.next_siblings:
                    if sibling.name == "h6":
                        break
                    if isinstance(sibling, str):
                        text = sibling.strip()
                        if text:
                            value = text
                            break
                    elif sibling.name and sibling.name != "br":
                        text = sibling.get_text(strip=True)
                        if text and not text.endswith(":"):
                            value = text
                            break

            if label:
                # Normalize label names
                label = label.lower().replace(" ", "_").replace(".", "")
                data[label] = value

        # Get contact info (email, phone, website)
        for a_tag in circular_title.find_all("a"):
            href = a_tag.get("href", "")
            text = a_tag.get_text(strip=True)
            if href.startswith("mailto:"):
                data["email"] = href.replace("mailto:", "")
            elif href.startswith("tel:"):
                data["phone"] = href.replace("tel:", "")
            elif href.startswith("http"):
                data["website"] = href

        # Get all paragraph text (descriptions, products, etc.)
        paragraphs = circular_title.find_all("p")
        for i, p in enumerate(paragraphs):
            # Check if this is a labeled section
            strong = p.find("strong")
            if strong:
                label = strong.get_text(strip=True).rstrip(":")
                # Get text after the strong tag
                text_parts = []
                for elem in strong.next_siblings:
                    if isinstance(elem, str):
                        text_parts.append(elem.strip())
                    elif elem.name:
                        text_parts.append(elem.get_text(strip=True))
                value = " ".join(text_parts).strip()

                if label:
                    label = label.lower().replace(" ", "_").replace(".", "")
                    data[label] = value
            else:
                # Generic paragraph text
                text = p.get_text(strip=True)
                if text and text not in data.values():
                    # Store as description or additional info
                    if "description" not in data:
                        data["description"] = text
                    else:
                        data[f"info_{i}"] = text

    # Get buttons/links at the bottom
    btns = box.find("div", class_="circular-btns")
    if btns:
        for a_tag in btns.find_all("a"):
            href = a_tag.get("href", "")
            text = a_tag.get_text(strip=True).lower()
            if "website" in text and href.startswith("http"):
                data["website"] = href
            elif "email" in text and href.startswith("mailto:"):
                data["email"] = href.replace("mailto:", "")

    return data


def scrape_page(url):
    """Scrape all exhibitors from a single page."""
    print(f"Scraping {url}...")
    response = requests.get(url, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.content, "html.parser")
    exhibitor_boxes = soup.find_all("div", class_="single-circular-box")

    exhibitors = []
    for box in exhibitor_boxes:
        data = scrape_exhibitor(box)
        if data.get("company_name"):
            exhibitors.append(data)

    print(f"  Found {len(exhibitors)} exhibitors")
    return exhibitors


def main():
    """Scrape all pages and save to CSV."""
    base_url = "https://exhibitors.renewableenergyindiaexpo.com/index.php"
    all_exhibitors = []

    # Scrape page 1
    url = f"{base_url}?&per_page=100"
    all_exhibitors.extend(scrape_page(url))

    # Scrape pages 2-6
    for page_num in range(2, 7):
        url = f"{base_url}?page={page_num}&per_page=100"
        all_exhibitors.extend(scrape_page(url))

    print(f"\nTotal exhibitors scraped: {len(all_exhibitors)}")

    # Get all unique field names
    all_fields = set()
    for exhibitor in all_exhibitors:
        all_fields.update(exhibitor.keys())

    # Sort fields for better readability
    priority_fields = [
        "company_name",
        "stall_number",
        "country",
        "email",
        "phone",
        "website",
        "logo_url",
    ]
    sorted_fields = []
    for field in priority_fields:
        if field in all_fields:
            sorted_fields.append(field)
            all_fields.remove(field)
    sorted_fields.extend(sorted(all_fields))

    # Write to CSV
    output_file = "exhibitors.csv"
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=sorted_fields)
        writer.writeheader()
        writer.writerows(all_exhibitors)

    print(f"Data saved to {output_file}")
    print(f"Fields: {', '.join(sorted_fields)}")


if __name__ == "__main__":
    main()
