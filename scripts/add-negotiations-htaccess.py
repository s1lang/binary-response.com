#!/usr/bin/env python3
"""
US-006: Add 301 redirects to .htaccess for all moved negotiations files.

Reads negotiations-mapping.json and appends (or replaces) a clearly-delimited
block of Apache Redirect 301 directives to .htaccess.

Usage:
    python3 scripts/add-negotiations-htaccess.py [--dry-run]

Options:
    --dry-run   Print the block that would be written without modifying .htaccess
"""

import json
import os
import sys
import argparse

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAPPING_FILE = os.path.join(REPO_ROOT, "negotiations-mapping.json")
HTACCESS_FILE = os.path.join(REPO_ROOT, ".htaccess")

BEGIN_MARKER = "# BEGIN negotiations-redirects"
END_MARKER = "# END negotiations-redirects"


def load_mapping(mapping_file=None):
    if mapping_file is None:
        mapping_file = MAPPING_FILE
    if not os.path.exists(mapping_file):
        raise FileNotFoundError(f"Mapping file not found: {mapping_file}")
    with open(mapping_file) as f:
        return json.load(f)


def build_redirect_block(mapping):
    """Build the delimited redirect block text for the given mapping dict."""
    lines = [BEGIN_MARKER]
    for group in sorted(mapping.keys()):
        files = mapping[group]
        lines.append(f"# {group}")
        for filename in sorted(files):
            # filename is e.g. "akira-20230529.html"
            stem = filename  # keep .html
            old_path = f"/negotiations/{stem}"
            new_path = f"/negotiations/{group}/{stem}"
            lines.append(f"Redirect 301 {old_path} {new_path}")
    lines.append(END_MARKER)
    return "\n".join(lines) + "\n"


def read_htaccess(htaccess_file=None):
    if htaccess_file is None:
        htaccess_file = HTACCESS_FILE
    if not os.path.exists(htaccess_file):
        return ""
    with open(htaccess_file) as f:
        return f.read()


def strip_existing_block(content):
    """Remove any existing negotiations-redirects block from content."""
    if BEGIN_MARKER not in content:
        return content
    before = content[: content.index(BEGIN_MARKER)]
    after_end = content.find(END_MARKER)
    if after_end == -1:
        # Malformed — truncate at BEGIN marker
        return before
    after = content[after_end + len(END_MARKER):]
    # Strip leading newline that separates the block from what follows
    if after.startswith("\n"):
        after = after[1:]
    return before.rstrip("\n") + ("\n" if before else "") + after


def write_htaccess(content, htaccess_file=None):
    if htaccess_file is None:
        htaccess_file = HTACCESS_FILE
    with open(htaccess_file, "w") as f:
        f.write(content)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true",
                        help="Print block without modifying .htaccess")
    parser.add_argument("--mapping", default=None,
                        help="Path to negotiations-mapping.json (default: repo root)")
    parser.add_argument("--htaccess", default=None,
                        help="Path to .htaccess file (default: repo root)")
    args = parser.parse_args(argv)

    mapping_file = args.mapping or MAPPING_FILE
    htaccess_file = args.htaccess or HTACCESS_FILE

    mapping = load_mapping(mapping_file)
    block = build_redirect_block(mapping)

    if args.dry_run:
        print(block)
        return 0

    existing = read_htaccess(htaccess_file)
    cleaned = strip_existing_block(existing)

    # Ensure there's exactly one trailing newline before the block
    if cleaned and not cleaned.endswith("\n"):
        cleaned += "\n"
    if cleaned:
        cleaned += "\n"

    new_content = cleaned + block

    write_htaccess(new_content, htaccess_file)

    redirect_count = block.count("Redirect 301 /negotiations/")
    print(f"Written {redirect_count} redirects to .htaccess")
    return 0


if __name__ == "__main__":
    sys.exit(main())
