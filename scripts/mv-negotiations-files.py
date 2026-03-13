#!/usr/bin/env python3
"""
Move negotiation transcript HTML files into per-threat-actor subdirectories.
Reads negotiations-mapping.json from the site root and performs git mv operations.

Usage:
    python3 scripts/mv-negotiations-files.py [--dry-run]

Must be run from the site root (git repo root).
"""

import argparse
import json
import os
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(
        description="Move negotiations transcript files into per-actor subdirectories."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print operations without executing them.",
    )
    args = parser.parse_args()

    # Load mapping
    mapping_path = "negotiations-mapping.json"
    if not os.path.exists(mapping_path):
        print(f"ERROR: {mapping_path} not found. Run generate-negotiations-mapping.py first.", file=sys.stderr)
        sys.exit(1)

    with open(mapping_path) as f:
        mapping = json.load(f)

    moved = 0
    errors = 0

    for group, files in mapping.items():
        subdir = os.path.join("negotiations", group)

        # Create subdirectory
        if args.dry_run:
            print(f"[DRY-RUN] mkdir -p {subdir}")
        else:
            os.makedirs(subdir, exist_ok=True)

        for filename in files:
            src = os.path.join("negotiations", filename)
            dst = os.path.join("negotiations", group, filename)

            if args.dry_run:
                print(f"[DRY-RUN] git mv {src} {dst}")
                moved += 1
                continue

            if not os.path.exists(src):
                print(f"WARNING: source not found, skipping: {src}", file=sys.stderr)
                errors += 1
                continue

            result = subprocess.run(
                ["git", "mv", src, dst],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                print(f"ERROR: git mv {src} -> {dst}: {result.stderr.strip()}", file=sys.stderr)
                errors += 1
            else:
                print(f"Moved: {src} -> {dst}")
                moved += 1

    print(f"\nDone. Moved: {moved}, Errors: {errors}")
    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
