#!/usr/bin/env python3
"""
US-009: Create /for/ redirect files and add .htaccess redirect /for/* → /industries/*

Replaces content of /for/*.html with meta-refresh redirect stubs pointing to /industries/
equivalents, and adds a RedirectMatch 301 block to .htaccess.
"""

import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FOR_FILES = [
    "index.html",
    "healthcare.html",
    "legal.html",
    "manufacturing.html",
    "financial-services.html",
    "education.html",
]

REDIRECT_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta http-equiv="refresh" content="0;url=/industries/{filename}">
<link rel="canonical" href="https://binary-response.com/industries/{filename}">
<title>Redirecting...</title>
</head>
<body>
<p>This page has moved. <a href="/industries/{filename}">Click here</a>.</p>
</body>
</html>
"""

HTACCESS_BLOCK = """\

# BEGIN for-redirects
RedirectMatch 301 ^/for/(.*)$ /industries/$1
# END for-redirects
"""


def create_redirect_files(repo_root=None, dry_run=False):
    """Replace /for/*.html files with meta-refresh redirect stubs."""
    if repo_root is None:
        repo_root = REPO_ROOT

    for_dir = os.path.join(repo_root, "for")
    if not os.path.isdir(for_dir):
        print(f"ERROR: /for/ directory not found at {for_dir}", file=sys.stderr)
        return False

    for filename in FOR_FILES:
        filepath = os.path.join(for_dir, filename)
        content = REDIRECT_TEMPLATE.format(filename=filename)
        if dry_run:
            print(f"[dry-run] Would write redirect stub: for/{filename} → /industries/{filename}")
        else:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"Written redirect stub: for/{filename} → /industries/{filename}")

    return True


def update_htaccess(repo_root=None, dry_run=False):
    """Add RedirectMatch 301 block to .htaccess for /for/ → /industries/."""
    if repo_root is None:
        repo_root = REPO_ROOT

    htaccess_path = os.path.join(repo_root, ".htaccess")

    if os.path.exists(htaccess_path):
        with open(htaccess_path, "r", encoding="utf-8") as f:
            content = f.read()
    else:
        content = ""

    if "# BEGIN for-redirects" in content:
        print("NOTE: .htaccess already contains for-redirects block, skipping.")
        return True

    new_content = content + HTACCESS_BLOCK

    if dry_run:
        print("[dry-run] Would append to .htaccess:")
        print(HTACCESS_BLOCK)
    else:
        with open(htaccess_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        print("Updated .htaccess with for-redirects block.")

    return True


def main():
    dry_run = "--dry-run" in sys.argv

    repo_root = REPO_ROOT

    ok1 = create_redirect_files(repo_root, dry_run=dry_run)
    ok2 = update_htaccess(repo_root, dry_run=dry_run)

    if ok1 and ok2:
        print("Done.")
        sys.exit(0)
    else:
        print("ERROR: One or more steps failed.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
