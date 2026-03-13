#!/usr/bin/env python3
"""
US-008: Update all internal /for/ links to /industries/ site-wide.

Finds all HTML and JS files outside the /for/ directory that reference /for/
and replaces those references with /industries/.

Matching rule: replace the exact string '/for/' with '/industries/'
to avoid false positives (e.g. won't match 'before/' or 'comfort/').
"""
import os
import sys
import argparse


def find_files_with_for_refs(repo_root, extensions=('.html', '.js')):
    """Return list of files outside /for/ that contain '/for/'."""
    matches = []
    for dirpath, dirnames, filenames in os.walk(repo_root):
        # Skip the /for/ directory entirely
        rel_dir = os.path.relpath(dirpath, repo_root)
        if rel_dir == 'for' or rel_dir.startswith('for' + os.sep):
            dirnames[:] = []
            continue
        # Skip .git
        dirnames[:] = [d for d in dirnames if d != '.git']

        for fname in filenames:
            if any(fname.endswith(ext) for ext in extensions):
                fpath = os.path.join(dirpath, fname)
                try:
                    with open(fpath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    if '/for/' in content:
                        matches.append(fpath)
                except (UnicodeDecodeError, OSError):
                    pass
    return sorted(matches)


def update_file(fpath, dry_run=False):
    """Replace /for/ with /industries/ in the given file. Returns (old, new) content."""
    with open(fpath, 'r', encoding='utf-8') as f:
        old = f.read()
    new = old.replace('/for/', '/industries/')
    if not dry_run and old != new:
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(new)
    changed = old != new
    count = old.count('/for/')
    return changed, count


def main(argv=None):
    parser = argparse.ArgumentParser(description='Replace /for/ with /industries/ in site files')
    parser.add_argument('--dry-run', action='store_true', help='Show what would change, but do not modify files')
    parser.add_argument('--repo-root', default=None, help='Path to repository root (default: parent of scripts/)')
    args = parser.parse_args(argv)

    if args.repo_root:
        repo_root = args.repo_root
    else:
        # Default: scripts/ is one level below repo root
        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    files = find_files_with_for_refs(repo_root)

    if not files:
        print('No files outside /for/ contain /for/ references. Nothing to do.')
        return 0

    total_changes = 0
    for fpath in files:
        changed, count = update_file(fpath, dry_run=args.dry_run)
        rel = os.path.relpath(fpath, repo_root)
        action = 'Would update' if args.dry_run else 'Updated'
        if changed:
            print(f'{action}: {rel} ({count} occurrence{"s" if count != 1 else ""})')
            total_changes += 1

    if args.dry_run:
        print(f'\nDry run: {total_changes} file(s) would be updated.')
    else:
        print(f'\nDone: {total_changes} file(s) updated.')

    # Verify: no files outside /for/ should still contain /for/
    remaining = find_files_with_for_refs(repo_root)
    if remaining and not args.dry_run:
        print('\nWARNING: These files still contain /for/ references:')
        for f in remaining:
            print(f'  {os.path.relpath(f, repo_root)}')
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
