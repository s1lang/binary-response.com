#!/usr/bin/env python3
"""
Tests for scripts/mv-negotiations-files.py

Run from the site root:
    python3 -m pytest scripts/test_mv_negotiations_files.py -v
or:
    python3 scripts/test_mv_negotiations_files.py
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Ensure scripts dir is on path
SCRIPTS_DIR = Path(__file__).parent
SITE_ROOT = SCRIPTS_DIR.parent


class TestDryRun(unittest.TestCase):
    """Test --dry-run mode: prints operations without executing."""

    def _run_dry_run(self, mapping):
        """Run script in dry-run mode against a temp mapping file."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, dir=SITE_ROOT
        ) as f:
            json.dump(mapping, f)
            mapping_path = f.name

        original_mapping = "negotiations-mapping.json"
        mapping_backup = None

        try:
            # Swap out the real mapping with our temp one
            if os.path.exists(original_mapping):
                mapping_backup = original_mapping + ".bak"
                os.rename(original_mapping, mapping_backup)
            os.rename(mapping_path, original_mapping)

            result = subprocess.run(
                [sys.executable, "scripts/mv-negotiations-files.py", "--dry-run"],
                capture_output=True,
                text=True,
                cwd=SITE_ROOT,
            )
            return result
        finally:
            # Restore original mapping
            os.rename(original_mapping, mapping_path)
            os.unlink(mapping_path)
            if mapping_backup:
                os.rename(mapping_backup, original_mapping)

    def test_dry_run_exits_zero(self):
        """Dry-run should exit 0."""
        mapping = {"akira": ["akira-20230529.html"], "conti": ["conti-20210107.html"]}
        result = self._run_dry_run(mapping)
        self.assertEqual(result.returncode, 0, msg=result.stderr)

    def test_dry_run_prints_mkdir(self):
        """Dry-run should print mkdir operations."""
        mapping = {"akira": ["akira-20230529.html"]}
        result = self._run_dry_run(mapping)
        self.assertIn("[DRY-RUN] mkdir -p negotiations/akira", result.stdout)

    def test_dry_run_prints_git_mv(self):
        """Dry-run should print git mv operations."""
        mapping = {"akira": ["akira-20230529.html"]}
        result = self._run_dry_run(mapping)
        self.assertIn(
            "[DRY-RUN] git mv negotiations/akira-20230529.html negotiations/akira/akira-20230529.html",
            result.stdout,
        )

    def test_dry_run_counts_files(self):
        """Dry-run should report correct moved count."""
        mapping = {
            "akira": ["akira-20230529.html", "akira-20230606.html"],
            "conti": ["conti-20210107.html"],
        }
        result = self._run_dry_run(mapping)
        self.assertIn("Moved: 3", result.stdout)

    def test_dry_run_does_not_create_directories(self):
        """Dry-run must NOT create any subdirectories."""
        mapping = {"test-actor-xyz": ["test-actor-xyz-20230101.html"]}
        result = self._run_dry_run(mapping)
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        subdir = SITE_ROOT / "negotiations" / "test-actor-xyz"
        self.assertFalse(
            subdir.exists(),
            msg=f"Dry-run created directory {subdir} — it should not have.",
        )

    def test_missing_mapping_exits_nonzero(self):
        """Script should exit non-zero if negotiations-mapping.json is missing."""
        original_mapping = SITE_ROOT / "negotiations-mapping.json"
        backup = SITE_ROOT / "negotiations-mapping.json.bak2"
        if original_mapping.exists():
            os.rename(original_mapping, backup)
        try:
            result = subprocess.run(
                [sys.executable, "scripts/mv-negotiations-files.py", "--dry-run"],
                capture_output=True,
                text=True,
                cwd=SITE_ROOT,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("not found", result.stderr)
        finally:
            if backup.exists():
                os.rename(backup, original_mapping)

    def test_dry_run_all_groups_from_real_mapping(self):
        """Dry-run against the real mapping should show all 24 groups and 235 files."""
        real_mapping_path = SITE_ROOT / "negotiations-mapping.json"
        if not real_mapping_path.exists():
            self.skipTest("negotiations-mapping.json not found")

        with open(real_mapping_path) as f:
            mapping = json.load(f)

        result = subprocess.run(
            [sys.executable, "scripts/mv-negotiations-files.py", "--dry-run"],
            capture_output=True,
            text=True,
            cwd=SITE_ROOT,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)

        total_files = sum(len(v) for v in mapping.values())
        self.assertIn(f"Moved: {total_files}", result.stdout)

        for group in mapping:
            self.assertIn(f"[DRY-RUN] mkdir -p negotiations/{group}", result.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
