#!/usr/bin/env python3
"""
US-003: Create meta-refresh redirect files at old flat negotiations URLs.

Reads negotiations-mapping.json and creates a redirect HTML stub at
negotiations/{filename}.html for each file that was moved to
negotiations/{group}/{filename}.html in US-002.
"""

import json
import os
import sys

REDIRECT_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta http-equiv="refresh" content="0;url=/negotiations/{group}/{filename}">
<link rel="canonical" href="https://binary-response.com/negotiations/{group}/{filename}">
<title>Redirecting...</title>
</head>
<body>
<p>This page has moved. <a href="/negotiations/{group}/{filename}">Click here</a>.</p>
</body>
</html>
"""


def create_redirects(repo_root: str, dry_run: bool = False) -> int:
    """Create redirect stubs for all moved negotiations files.

    Returns the count of redirect files created (or that would be created).
    """
    mapping_path = os.path.join(repo_root, "negotiations-mapping.json")
    if not os.path.exists(mapping_path):
        print(f"ERROR: negotiations-mapping.json not found at {mapping_path}", file=sys.stderr)
        sys.exit(1)

    with open(mapping_path) as f:
        mapping = json.load(f)

    negotiations_dir = os.path.join(repo_root, "negotiations")
    created = 0
    errors = 0

    for group, files in sorted(mapping.items()):
        for filename in sorted(files):
            dest_path = os.path.join(negotiations_dir, filename)
            content = REDIRECT_TEMPLATE.format(group=group, filename=filename)

            if dry_run:
                print(f"[dry-run] Would create {dest_path} -> /negotiations/{group}/{filename}")
                created += 1
                continue

            # Verify the target file actually exists in the new location
            target_path = os.path.join(negotiations_dir, group, filename)
            if not os.path.exists(target_path):
                print(f"WARNING: target file does not exist: {target_path}", file=sys.stderr)
                errors += 1
                continue

            with open(dest_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"Created: negotiations/{filename} -> /negotiations/{group}/{filename}")
            created += 1

    print(f"\nDone. Created {created} redirect files, {errors} errors.")
    if errors > 0:
        sys.exit(1)
    return created


def main():
    dry_run = "--dry-run" in sys.argv
    # Run from repo root
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    create_redirects(repo_root, dry_run=dry_run)


if __name__ == "__main__":
    main()
