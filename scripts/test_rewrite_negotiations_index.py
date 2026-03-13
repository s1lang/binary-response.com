#!/usr/bin/env python3
"""
Tests for US-005: rewrite-negotiations-index.py
"""

import importlib.util
import json
import os
import sys
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path

# Load module with hyphenated filename
_spec = importlib.util.spec_from_file_location(
    "rewrite_negotiations_index",
    Path(__file__).parent / "rewrite-negotiations-index.py",
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

load_mapping = _mod.load_mapping
build_groups = _mod.build_groups
generate_index_html = _mod.generate_index_html
main = _mod.main
GROUP_DISPLAY_NAMES = _mod.GROUP_DISPLAY_NAMES

# Minimal mapping that matches real structure: 24 groups
SAMPLE_MAPPING = {
    "akira": [f"akira-2023{i:04d}.html" for i in range(1, 61)],   # 60
    "conti": [f"conti-2021{i:04d}.html" for i in range(1, 33)],    # 32
    "lockbit3-0": [f"lockbit3-0-{i}.html" for i in range(1, 44)],  # 43
    "revil": [f"revil-2021{i:04d}.html" for i in range(1, 21)],    # 20
    "dragonforce": [f"dragonforce-{i}.html" for i in range(1, 15)], # 14
    "trinity": [f"trinity-{i:04d}.html" for i in range(1, 15)],    # 14
    "hive": [f"hive-{i}.html" for i in range(1, 9)],               # 8
    "avaddon": [f"avaddon-{i}.html" for i in range(1, 8)],         # 7
    "fog": [f"fog-{i}.html" for i in range(1, 7)],                  # 6
    "blackbasta": [f"blackbasta-{i}.html" for i in range(1, 6)],   # 5
    "darkside": [f"darkside-{i}.html" for i in range(1, 6)],       # 5
    "mallox": [f"mallox-{i}.html" for i in range(1, 4)],           # 3
    "qilin": [f"qilin-{i}.html" for i in range(1, 3)],             # 2
    "blackmatter": [f"blackmatter-{i}.html" for i in range(1, 3)], # 2
    "babuk": [f"babuk-{i}.html" for i in range(1, 3)],             # 2
    "cloak": [f"cloak-{i}.html" for i in range(1, 3)],             # 2
    "noescape": [f"noescape-{i}.html" for i in range(1, 3)],       # 2
    "ranzy": [f"ranzy-{i}.html" for i in range(1, 3)],             # 2
    "avos": ["avos-20210903.html"],                                  # 1
    "hunters-international": ["hunters-international-20240510.html"], # 1
    "mount-locker": ["mount-locker-20201016.html"],                  # 1
    "pear": ["pear-20250720.html"],                                  # 1
    "ransomhub": ["ransomhub-20240810.html"],                        # 1
    "runsomewares": ["runsomewares-20250411.html"],                  # 1
}


def _make_temp_repo(mapping: dict) -> Path:
    """Create a temp dir acting as repo root with negotiations-mapping.json."""
    tmp = Path(tempfile.mkdtemp())
    (tmp / "negotiations").mkdir()
    (tmp / "negotiations-mapping.json").write_text(
        json.dumps(mapping), encoding="utf-8"
    )
    return tmp


class TestBuildGroups(unittest.TestCase):
    def test_returns_24_groups_for_full_mapping(self):
        groups = build_groups(SAMPLE_MAPPING)
        self.assertEqual(len(groups), 24)

    def test_sorted_by_count_descending(self):
        groups = build_groups(SAMPLE_MAPPING)
        counts = [c for _, _, c in groups]
        self.assertEqual(counts, sorted(counts, reverse=True))

    def test_total_matches_sum(self):
        groups = build_groups(SAMPLE_MAPPING)
        total = sum(c for _, _, c in groups)
        expected = sum(len(v) for v in SAMPLE_MAPPING.values())
        self.assertEqual(total, expected)

    def test_display_names_used(self):
        groups = build_groups(SAMPLE_MAPPING)
        display_map = {slug: display for slug, display, _ in groups}
        self.assertEqual(display_map["akira"], "Akira")
        self.assertEqual(display_map["lockbit3-0"], "LockBit 3.0")
        self.assertEqual(display_map["hunters-international"], "Hunters International")
        self.assertEqual(display_map["revil"], "REvil")

    def test_alphabetical_tiebreaker(self):
        mapping = {"beta": ["b.html"], "alpha": ["a.html"]}
        groups = build_groups(mapping)
        slugs = [s for s, _, _ in groups]
        self.assertEqual(slugs, ["alpha", "beta"])


class TestGenerateIndexHtml(unittest.TestCase):
    def setUp(self):
        groups = build_groups(SAMPLE_MAPPING)
        self.total = sum(c for _, _, c in groups)
        self.html = generate_index_html(groups, self.total)
        self.groups = groups

    def test_parses_without_error(self):
        """html.parser should parse the file without error."""
        parser = HTMLParser()
        # Should not raise
        parser.feed(self.html)

    def test_contains_24_group_links(self):
        """All 24 group index links present as /negotiations/{group}/ hrefs."""
        count = 0
        for slug, _, _ in self.groups:
            link = f'href="{slug}/"'
            if link in self.html:
                count += 1
        self.assertEqual(count, 24, f"Expected 24 group links, found {count}")

    def test_each_group_shows_transcript_count(self):
        for slug, display, transcript_count in self.groups:
            self.assertIn(str(transcript_count), self.html,
                          f"Count {transcript_count} for {slug} not in HTML")

    def test_title_reflects_grouped_structure(self):
        self.assertIn("24 Groups", self.html)
        self.assertIn(str(self.total), self.html)

    def test_meta_description_reflects_groups(self):
        self.assertIn('name="description"', self.html)
        self.assertIn("24 groups", self.html)

    def test_css_link_uses_relative_path(self):
        self.assertIn('href="../css/style.css"', self.html)

    def test_js_link_uses_relative_path(self):
        self.assertIn('src="../js/main.js"', self.html)

    def test_structured_data_has_hasPart(self):
        self.assertIn('"hasPart"', self.html)
        self.assertIn('"CollectionPage"', self.html)

    def test_structured_data_total_count(self):
        self.assertIn(str(self.total), self.html)

    def test_canonical_url_present(self):
        self.assertIn('href="https://binary-response.com/negotiations/"', self.html)

    def test_no_old_flat_transcript_rows(self):
        """Should not contain old data-group= attributes from the flat list."""
        self.assertNotIn('data-group="akira"', self.html)

    def test_hero_stat_total(self):
        self.assertIn(f'<span class="stat-value">{self.total}</span>', self.html)


class TestLoadMapping(unittest.TestCase):
    def test_loads_valid_mapping(self):
        tmp = _make_temp_repo(SAMPLE_MAPPING)
        mapping = load_mapping(tmp)
        self.assertEqual(len(mapping), 24)

    def test_raises_on_missing_mapping(self):
        tmp = Path(tempfile.mkdtemp())
        with self.assertRaises(FileNotFoundError):
            load_mapping(tmp)


class TestMain(unittest.TestCase):
    def test_dry_run_does_not_write(self):
        tmp = _make_temp_repo(SAMPLE_MAPPING)
        output = tmp / "negotiations" / "index.html"
        result = main(dry_run=True, repo_root=tmp)
        self.assertEqual(result, 0)
        self.assertFalse(output.exists(), "dry-run should not write file")

    def test_main_writes_file(self):
        tmp = _make_temp_repo(SAMPLE_MAPPING)
        output = tmp / "negotiations" / "index.html"
        result = main(dry_run=False, repo_root=tmp)
        self.assertEqual(result, 0)
        self.assertTrue(output.exists())
        content = output.read_text(encoding="utf-8")
        # Basic sanity: 24 links
        link_count = sum(1 for slug in SAMPLE_MAPPING if f'href="{slug}/"' in content)
        self.assertEqual(link_count, 24)

    def test_main_missing_mapping_returns_1(self):
        tmp = Path(tempfile.mkdtemp())
        (tmp / "negotiations").mkdir()
        result = main(dry_run=False, repo_root=tmp)
        self.assertEqual(result, 1)

    def test_real_repo_total_is_235(self):
        """Integration test against the real repo's negotiations-mapping.json."""
        repo_root = Path(__file__).parent.parent
        mapping_path = repo_root / "negotiations-mapping.json"
        if not mapping_path.exists():
            self.skipTest("negotiations-mapping.json not found")
        mapping = load_mapping(repo_root)
        total = sum(len(v) for v in mapping.values())
        self.assertEqual(total, 235, f"Expected 235 total transcripts, got {total}")

    def test_real_repo_has_24_groups(self):
        """Integration test: real mapping has 24 groups."""
        repo_root = Path(__file__).parent.parent
        mapping_path = repo_root / "negotiations-mapping.json"
        if not mapping_path.exists():
            self.skipTest("negotiations-mapping.json not found")
        mapping = load_mapping(repo_root)
        self.assertEqual(len(mapping), 24)


class TestAcceptanceCriteria(unittest.TestCase):
    """Tests matching the US-005 acceptance criteria."""

    def setUp(self):
        """Run main against real repo and load output."""
        self.repo_root = Path(__file__).parent.parent
        if not (self.repo_root / "negotiations-mapping.json").exists():
            self.skipTest("negotiations-mapping.json not found")

    def test_ac1_contains_24_group_index_links(self):
        """AC1: negotiations/index.html contains links to all 24 group index pages."""
        output_path = self.repo_root / "negotiations" / "index.html"
        if not output_path.exists():
            self.skipTest("negotiations/index.html not yet generated")
        content = output_path.read_text(encoding="utf-8")
        mapping = load_mapping(self.repo_root)
        found = 0
        for slug in mapping:
            if f'href="{slug}/"' in content:
                found += 1
        self.assertEqual(found, 24)

    def test_ac2_each_link_shows_count(self):
        """AC2: Each group link shows the transcript count."""
        output_path = self.repo_root / "negotiations" / "index.html"
        if not output_path.exists():
            self.skipTest("negotiations/index.html not yet generated")
        content = output_path.read_text(encoding="utf-8")
        mapping = load_mapping(self.repo_root)
        for slug, files in mapping.items():
            self.assertIn(str(len(files)), content,
                          f"Count {len(files)} for {slug} not found in index")

    def test_ac3_title_and_meta_reflect_grouped(self):
        """AC3: Title and meta description reflect grouped structure."""
        output_path = self.repo_root / "negotiations" / "index.html"
        if not output_path.exists():
            self.skipTest("negotiations/index.html not yet generated")
        content = output_path.read_text(encoding="utf-8")
        self.assertIn("24 Group", content)

    def test_ac4_no_broken_relative_links(self):
        """AC4: CSS/JS links use ../css/ and ../js/ relative paths."""
        output_path = self.repo_root / "negotiations" / "index.html"
        if not output_path.exists():
            self.skipTest("negotiations/index.html not yet generated")
        content = output_path.read_text(encoding="utf-8")
        self.assertIn('../css/style.css', content)
        self.assertIn('../js/main.js', content)

    def test_ac5_total_is_235(self):
        """AC5: Total transcript count displayed on page equals 235."""
        output_path = self.repo_root / "negotiations" / "index.html"
        if not output_path.exists():
            self.skipTest("negotiations/index.html not yet generated")
        content = output_path.read_text(encoding="utf-8")
        self.assertIn("235", content)

    def test_ac6_html_parses_without_error(self):
        """AC6: html.parser parses the file without error."""
        output_path = self.repo_root / "negotiations" / "index.html"
        if not output_path.exists():
            self.skipTest("negotiations/index.html not yet generated")
        content = output_path.read_text(encoding="utf-8")
        parser = HTMLParser()
        parser.feed(content)  # no exception = pass


if __name__ == "__main__":
    unittest.main()
