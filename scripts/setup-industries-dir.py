#!/usr/bin/env python3
"""
US-007: Copy /for/ to /industries/ and update internal self-references.

Copies all HTML files from for/ to industries/, then replaces all occurrences
of /for/ with /industries/ within the copied files (canonical URLs, og:url,
JSON-LD url/@id, and internal hrefs between industry pages).

The /for/ originals are NOT modified (that happens in US-009).
"""

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path


def get_repo_root() -> Path:
    """Return the repository root directory."""
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=True,
    )
    return Path(result.stdout.strip())


def copy_for_to_industries(repo_root: Path, dry_run: bool = False) -> list[Path]:
    """Copy all files from for/ into industries/."""
    src_dir = repo_root / "for"
    dst_dir = repo_root / "industries"

    if not src_dir.exists():
        raise FileNotFoundError(f"Source directory not found: {src_dir}")

    html_files = sorted(src_dir.glob("*.html"))
    if not html_files:
        raise ValueError(f"No HTML files found in {src_dir}")

    copied = []
    for src_file in html_files:
        dst_file = dst_dir / src_file.name
        if not dry_run:
            dst_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_file, dst_file)
        copied.append(dst_file)
        print(f"{'[DRY-RUN] ' if dry_run else ''}copy {src_file.name} → industries/{src_file.name}")

    return copied


def replace_for_references(file_path: Path, dry_run: bool = False) -> int:
    """
    Replace all /for/ references with /industries/ in the given file.

    Targets:
    - <link rel="canonical" href="...">
    - <meta property="og:url" content="...">
    - JSON-LD "url": "..." and "@id": "..." fields
    - href="...for/..." links between industry pages

    Returns the number of replacements made.
    """
    content = file_path.read_text(encoding="utf-8")
    # Simple global replace of the path segment — catches all cases at once
    new_content = content.replace("/for/", "/industries/")
    count = content.count("/for/")

    if not dry_run and count > 0:
        file_path.write_text(new_content, encoding="utf-8")

    return count


def git_add_industries(repo_root: Path, dry_run: bool = False) -> None:
    """Stage all files in industries/ with git add."""
    industries_dir = repo_root / "industries"
    if not dry_run:
        subprocess.run(
            ["git", "add", str(industries_dir)],
            check=True,
            cwd=repo_root,
        )
        print("git add industries/")
    else:
        print("[DRY-RUN] git add industries/")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Copy /for/ to /industries/ and update internal self-references."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would happen without making changes.",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Override the repo root (defaults to git rev-parse --show-toplevel).",
    )
    args = parser.parse_args(argv)

    repo_root = args.repo_root or get_repo_root()
    dry_run = args.dry_run

    # 1. Copy files
    copied_files = copy_for_to_industries(repo_root, dry_run=dry_run)
    print(f"\nCopied {len(copied_files)} file(s) to industries/")

    # 2. Replace /for/ references in each copied file
    total_replacements = 0
    for file_path in copied_files:
        if dry_run:
            # Read from source since dst doesn't exist in dry-run
            src_path = repo_root / "for" / file_path.name
            content = src_path.read_text(encoding="utf-8")
            count = content.count("/for/")
            print(f"[DRY-RUN] would replace {count} occurrence(s) in {file_path.name}")
        else:
            count = replace_for_references(file_path, dry_run=False)
            print(f"Replaced {count} occurrence(s) in {file_path.name}")
        total_replacements += count

    print(f"\nTotal replacements: {total_replacements}")

    # 3. git add
    git_add_industries(repo_root, dry_run=dry_run)

    if dry_run:
        print("\n[DRY-RUN] No files were written or staged.")
    else:
        print("\nDone. Run `git status` to confirm 6 new files under industries/.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
