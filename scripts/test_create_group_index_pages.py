#!/usr/bin/env python3
"""
Tests for scripts/create-group-index-pages.py (US-004)
"""

import importlib.util
import json
import os
import sys
import tempfile
import unittest

# Load the hyphen-named module via importlib
_SCRIPT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "create-group-index-pages.py")
_spec = importlib.util.spec_from_file_location("create_group_index_pages", _SCRIPT_PATH)
mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mod)

parse_date_from_filename = mod.parse_date_from_filename
build_index_html = mod.build_index_html
main = mod.main
MAPPING_FILE = mod.MAPPING_FILE


class TestParseDateFromFilename(unittest.TestCase):
    def test_standard_date_akira(self):
        sort_key, label = parse_date_from_filename("akira-20230529.html", "akira")
        self.assertEqual(sort_key, "20230529")
        self.assertIn("2023", label)
        self.assertIn("29", label)
        self.assertIn("May", label)

    def test_standard_date_with_hyphen_suffix(self):
        sort_key, label = parse_date_from_filename("conti-20210517-b.html", "conti")
        self.assertEqual(sort_key, "20210517")
        self.assertIn("2021", label)

    def test_standard_date_with_letter_suffix(self):
        sort_key, label = parse_date_from_filename("akira-20250425b.html", "akira")
        self.assertEqual(sort_key, "20250425")
        self.assertIn("2025", label)

    def test_trinity_numeric_index(self):
        sort_key, label = parse_date_from_filename("trinity-0001.html", "trinity")
        self.assertEqual(sort_key, "0001")
        self.assertEqual(label, "Case 0001")

    def test_trinity_numeric_index_high(self):
        sort_key, label = parse_date_from_filename("trinity-0014.html", "trinity")
        self.assertEqual(sort_key, "0014")
        self.assertEqual(label, "Case 0014")

    def test_dragonforce_guid(self):
        sort_key, label = parse_date_from_filename(
            "dragonforce-058f4b92-ae99-45c7-bf35-5d2d6754b3de.html", "dragonforce"
        )
        self.assertIn("058f4b92", label)

    def test_dragonforce_short_hex(self):
        sort_key, label = parse_date_from_filename(
            "dragonforce-29bbe03074fdbb8d.html", "dragonforce"
        )
        self.assertIn("29bbe030", label)

    def test_lockbit_domain(self):
        sort_key, label = parse_date_from_filename(
            "lockbit3-0-aguasdoporto-pt.html", "lockbit3-0"
        )
        self.assertIn("aguasdoporto", label)

    def test_lockbit_numeric_non_date(self):
        # 149576 is not a valid YYYYMMDD so it falls through to slug
        sort_key, label = parse_date_from_filename("lockbit3-0-149576.html", "lockbit3-0")
        self.assertEqual(label, "149576")


class TestBuildIndexHtml(unittest.TestCase):
    def setUp(self):
        self.akira_files = [
            "akira-20230529.html",
            "akira-20230606.html",
            "akira-20240101.html",
        ]
        self.html = build_index_html("akira", self.akira_files)

    def test_title_contains_group_name(self):
        self.assertIn("Akira Ransomware Negotiation Transcripts", self.html)

    def test_title_contains_site_name(self):
        self.assertIn("Binary Response", self.html)

    def test_canonical_url(self):
        self.assertIn(
            '<link rel="canonical" href="https://binary-response.com/negotiations/akira/">',
            self.html,
        )

    def test_og_url(self):
        self.assertIn(
            'content="https://binary-response.com/negotiations/akira/"',
            self.html,
        )

    def test_css_path(self):
        self.assertIn("../../css/style.css", self.html)

    def test_nav_js_path(self):
        self.assertIn("../../js/nav.js", self.html)

    def test_all_files_linked(self):
        for f in self.akira_files:
            self.assertIn(f, self.html)

    def test_reverse_chronological_order(self):
        # 2024 date should appear before 2023 dates in the listing
        pos_2024 = self.html.index("akira-20240101")
        pos_2023 = self.html.index("akira-20230529")
        self.assertLess(pos_2024, pos_2023)

    def test_breadcrumb_contains_negotiations(self):
        self.assertIn("Negotiations", self.html)

    def test_breadcrumb_contains_group(self):
        self.assertIn("Akira", self.html)

    def test_relative_links(self):
        self.assertIn('./akira-20230529.html"', self.html)

    def test_hunters_international_display_name(self):
        files = ["hunters-international-20240510.html"]
        html = build_index_html("hunters-international", files)
        self.assertIn("Hunters International", html)


class TestBuildIndexHtmlDragonForce(unittest.TestCase):
    def setUp(self):
        self.df_files = [
            "dragonforce-058f4b92-ae99-45c7-bf35-5d2d6754b3de.html",
            "dragonforce-29bbe03074fdbb8d.html",
        ]
        self.html = build_index_html("dragonforce", self.df_files)

    def test_all_dragonforce_files_linked(self):
        for f in self.df_files:
            self.assertIn(f, self.html)

    def test_dragonforce_slug_labels_readable(self):
        self.assertIn("058f4b92", self.html)
        self.assertIn("29bbe030", self.html)


class TestBuildIndexHtmlTrinity(unittest.TestCase):
    def setUp(self):
        self.trinity_files = [f"trinity-{i:04d}.html" for i in range(1, 5)]
        self.html = build_index_html("trinity", self.trinity_files)

    def test_case_labels(self):
        self.assertIn("Case 0001", self.html)
        self.assertIn("Case 0004", self.html)

    def test_all_files_linked(self):
        for f in self.trinity_files:
            self.assertIn(f, self.html)


class TestMainScript(unittest.TestCase):
    def test_main_with_real_mapping(self):
        """Integration test: run main() against real mapping in a temp dir."""
        if not os.path.exists(MAPPING_FILE):
            self.skipTest("negotiations-mapping.json not found")

        with open(MAPPING_FILE) as f:
            mapping = json.load(f)

        with tempfile.TemporaryDirectory() as tmpdir:
            for group in mapping:
                os.makedirs(os.path.join(tmpdir, group), exist_ok=True)

            orig_dir = mod.NEGOTIATIONS_DIR
            try:
                mod.NEGOTIATIONS_DIR = tmpdir
                result = main(dry_run=False)
                self.assertEqual(result, 0)

                # Verify all 24 index pages exist
                created = [
                    g for g in mapping
                    if os.path.exists(os.path.join(tmpdir, g, "index.html"))
                ]
                self.assertEqual(len(created), 24)

                # Verify akira index contains all akira filenames
                akira_index = os.path.join(tmpdir, "akira", "index.html")
                with open(akira_index) as f:
                    content = f.read()
                for fname in mapping["akira"]:
                    self.assertIn(fname, content, f"Missing {fname} in akira/index.html")

                # Verify dragonforce index links all its files
                df_index = os.path.join(tmpdir, "dragonforce", "index.html")
                with open(df_index) as f:
                    df_content = f.read()
                for fname in mapping["dragonforce"]:
                    self.assertIn(fname, df_content)

            finally:
                mod.NEGOTIATIONS_DIR = orig_dir

    def test_main_dry_run_creates_no_files(self):
        """Dry run should not write any files."""
        if not os.path.exists(MAPPING_FILE):
            self.skipTest("negotiations-mapping.json not found")

        with open(MAPPING_FILE) as f:
            mapping = json.load(f)

        with tempfile.TemporaryDirectory() as tmpdir:
            for group in mapping:
                os.makedirs(os.path.join(tmpdir, group), exist_ok=True)

            orig_dir = mod.NEGOTIATIONS_DIR
            try:
                mod.NEGOTIATIONS_DIR = tmpdir
                result = main(dry_run=True)
                self.assertEqual(result, 0)
                for group in mapping:
                    self.assertFalse(
                        os.path.exists(os.path.join(tmpdir, group, "index.html")),
                        f"dry-run should not create {group}/index.html",
                    )
            finally:
                mod.NEGOTIATIONS_DIR = orig_dir

    def test_main_missing_mapping_file(self):
        """Should return exit code 1 if mapping file missing."""
        orig = mod.MAPPING_FILE
        try:
            mod.MAPPING_FILE = "/tmp/nonexistent-mapping-xyzzy.json"
            result = main()
            self.assertEqual(result, 1)
        finally:
            mod.MAPPING_FILE = orig


if __name__ == "__main__":
    unittest.main()
