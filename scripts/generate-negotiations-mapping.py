#!/usr/bin/env python3
"""
Generate a mapping of negotiations HTML files to their threat-actor groups.

Outputs negotiations-mapping.json at the site root and prints a summary table.
"""

import json
import os
import re
import sys
from pathlib import Path


def get_group(filename: str) -> str:
    """
    Determine the threat-actor group for a given filename.

    Grouping rules (first match wins):
    1. Starts with 'lockbit3-0-'       → 'lockbit3-0'
    2. Equals 'royal-mail-lockbit-3.html' → 'lockbit3-0'
    3. Starts with 'dragonforce-'      → 'dragonforce'
    4. Starts with 'trinity-'          → 'trinity'
    5. Starts with 'hunters-international-' → 'hunters-international'
    6. Otherwise: everything before the first '-YYYYMMDD' segment
    """
    if filename.startswith("lockbit3-0-"):
        return "lockbit3-0"
    if filename == "royal-mail-lockbit-3.html":
        return "lockbit3-0"
    if filename.startswith("dragonforce-"):
        return "dragonforce"
    if filename.startswith("trinity-"):
        return "trinity"
    if filename.startswith("hunters-international-"):
        return "hunters-international"

    # General rule: group = everything before the first '-YYYYMMDD' segment
    # A YYYYMMDD segment is 8 digits (possibly followed by more chars like 'b', '-2', etc.)
    stem = filename[: -len(".html")] if filename.endswith(".html") else filename
    match = re.search(r"-\d{8}", stem)
    if match:
        return stem[: match.start()]

    # Fallback: return the stem as-is (shouldn't normally happen)
    return stem


def generate_mapping(site_root: Path) -> dict:
    """Scan negotiations/*.html and build group → [files] mapping."""
    negotiations_dir = site_root / "negotiations"
    if not negotiations_dir.is_dir():
        print(f"ERROR: negotiations directory not found at {negotiations_dir}", file=sys.stderr)
        sys.exit(1)

    mapping: dict = {}
    for html_file in sorted(negotiations_dir.glob("*.html")):
        filename = html_file.name
        if filename == "index.html":
            continue
        group = get_group(filename)
        mapping.setdefault(group, []).append(filename)

    # Sort files within each group
    for group in mapping:
        mapping[group].sort()

    # Sort groups alphabetically
    mapping = dict(sorted(mapping.items()))
    return mapping


def print_summary(mapping: dict) -> None:
    """Print a summary table of group name | count."""
    print(f"\n{'Group':<40} {'Count':>5}")
    print("-" * 47)
    total = 0
    for group, files in sorted(mapping.items()):
        count = len(files)
        total += count
        print(f"{group:<40} {count:>5}")
    print("-" * 47)
    print(f"{'TOTAL':<40} {total:>5}")


def main():
    # Site root is two directories up from this script (scripts/ → site root)
    script_dir = Path(__file__).resolve().parent
    site_root = script_dir.parent

    mapping = generate_mapping(site_root)

    # Write JSON output
    output_path = site_root / "negotiations-mapping.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(mapping, f, indent=2)
    print(f"Written: {output_path}")

    print_summary(mapping)

    total = sum(len(v) for v in mapping.values())
    print(f"\nTotal files mapped: {total}")
    print(f"Total groups: {len(mapping)}")


if __name__ == "__main__":
    main()
