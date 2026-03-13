#!/usr/bin/env python3
"""update-sitemap.py: Update sitemap.xml to reflect new site structure.

Changes:
1. Remove flat /negotiations/{file}.html entries, add grouped URLs:
   - /negotiations/{group}/  (priority 0.7, changefreq monthly)
   - /negotiations/{group}/{file}.html  (priority 0.5, changefreq yearly)
2. Replace /for/ entries with /industries/ equivalents
3. Update lastmod dates to today (2026-03-13)
"""

import json
import sys
import argparse
import xml.etree.ElementTree as ET
from pathlib import Path

BASE_URL = "https://binary-response.com"
TODAY = "2026-03-13"
NS = "http://www.sitemaps.org/schemas/sitemap/0.9"


def make_tag(name):
    return f"{{{NS}}}{name}"


def load_mapping(mapping_path):
    with open(mapping_path) as f:
        return json.load(f)


def build_url_element(loc, lastmod, priority, changefreq):
    url = ET.Element(make_tag("url"))
    ET.SubElement(url, make_tag("loc")).text = loc
    ET.SubElement(url, make_tag("lastmod")).text = lastmod
    ET.SubElement(url, make_tag("priority")).text = str(priority)
    ET.SubElement(url, make_tag("changefreq")).text = changefreq
    return url


def update_sitemap(sitemap_path, mapping_path, output_path=None, dry_run=False):
    """Read sitemap.xml and mapping, produce updated sitemap.

    Returns the new ElementTree.
    """
    if output_path is None:
        output_path = sitemap_path

    mapping = load_mapping(mapping_path)

    ET.register_namespace("", NS)
    tree = ET.parse(sitemap_path)
    root = tree.getroot()

    # Build set of flat negotiations locs to remove
    flat_negotiations_locs = set()
    for group, files in mapping.items():
        for filename in files:
            flat_negotiations_locs.add(f"{BASE_URL}/negotiations/{filename}")

    new_urls = []
    seen_locs = set()

    # Process existing URLs: skip flat negotiations, replace /for/ -> /industries/
    for url_elem in root.findall(make_tag("url")):
        loc_elem = url_elem.find(make_tag("loc"))
        if loc_elem is None:
            continue
        loc = loc_elem.text

        # Drop flat negotiations transcript URLs
        if loc in flat_negotiations_locs:
            continue

        # Replace /for/ with /industries/
        if f"{BASE_URL}/for" in loc:
            new_loc = loc.replace(f"{BASE_URL}/for", f"{BASE_URL}/industries")
            if new_loc not in seen_locs:
                seen_locs.add(new_loc)
                priority = url_elem.find(make_tag("priority")).text
                changefreq = url_elem.find(make_tag("changefreq")).text
                new_urls.append(build_url_element(new_loc, TODAY, priority, changefreq))
            continue

        # Keep everything else (updating lastmod for negotiations index)
        if loc not in seen_locs:
            seen_locs.add(loc)
            if loc == f"{BASE_URL}/negotiations/":
                url_elem.find(make_tag("lastmod")).text = TODAY
            new_urls.append(url_elem)

    # Ensure /industries/ entries are present (in case /for/ wasn't in original sitemap)
    industries_pages = [
        ("", "0.7", "monthly"),
        ("education.html", "0.7", "monthly"),
        ("financial-services.html", "0.7", "monthly"),
        ("healthcare.html", "0.7", "monthly"),
        ("legal.html", "0.7", "monthly"),
        ("manufacturing.html", "0.7", "monthly"),
    ]
    for page, priority, changefreq in industries_pages:
        new_loc = f"{BASE_URL}/industries/{page}" if page else f"{BASE_URL}/industries/"
        if new_loc not in seen_locs:
            seen_locs.add(new_loc)
            new_urls.append(build_url_element(new_loc, TODAY, priority, changefreq))

    # Add new negotiations group + transcript URLs
    for group in sorted(mapping.keys()):
        files = mapping[group]

        # Group index page
        group_index_loc = f"{BASE_URL}/negotiations/{group}/"
        if group_index_loc not in seen_locs:
            seen_locs.add(group_index_loc)
            new_urls.append(build_url_element(group_index_loc, TODAY, "0.7", "monthly"))

        # Individual transcripts
        for filename in sorted(files):
            transcript_loc = f"{BASE_URL}/negotiations/{group}/{filename}"
            if transcript_loc not in seen_locs:
                seen_locs.add(transcript_loc)
                new_urls.append(build_url_element(transcript_loc, TODAY, "0.5", "yearly"))

    # Build new urlset
    new_root = ET.Element(make_tag("urlset"))
    for url_elem in new_urls:
        new_root.append(url_elem)

    new_tree = ET.ElementTree(new_root)
    ET.indent(new_tree, space="  ")

    if dry_run:
        print(f"Dry run: would write {len(new_urls)} URLs to {output_path}")
        return new_tree

    with open(output_path, "wb") as f:
        new_tree.write(f, xml_declaration=True, encoding="UTF-8")

    print(f"Written {len(new_urls)} URLs to {output_path}")
    return new_tree


def main():
    parser = argparse.ArgumentParser(description="Update sitemap.xml for new site structure")
    parser.add_argument("--sitemap", default="sitemap.xml", help="Path to sitemap.xml")
    parser.add_argument("--mapping", default="negotiations-mapping.json", help="Path to negotiations-mapping.json")
    parser.add_argument("--output", default=None, help="Output path (defaults to sitemap path)")
    parser.add_argument("--dry-run", action="store_true", help="Print URL count without writing")
    args = parser.parse_args()

    update_sitemap(args.sitemap, args.mapping, args.output, args.dry_run)


if __name__ == "__main__":
    main()
