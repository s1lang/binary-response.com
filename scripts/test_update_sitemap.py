#!/usr/bin/env python3
"""Tests for scripts/update-sitemap.py"""

import importlib.util
import json
import os
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

# Load module with hyphen in filename
SCRIPTS_DIR = Path(__file__).parent
spec = importlib.util.spec_from_file_location(
    "update_sitemap", SCRIPTS_DIR / "update-sitemap.py"
)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

NS = "http://www.sitemaps.org/schemas/sitemap/0.9"
BASE_URL = "https://binary-response.com"


def make_minimal_sitemap(entries):
    """Build a minimal sitemap XML string from a list of loc strings."""
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             f'<urlset xmlns="{NS}">']
    for loc in entries:
        lines.append(
            f'  <url><loc>{loc}</loc>'
            f'<lastmod>2026-01-01</lastmod>'
            f'<priority>0.7</priority>'
            f'<changefreq>monthly</changefreq></url>'
        )
    lines.append('</urlset>')
    return "\n".join(lines)


def make_minimal_mapping():
    """Return a minimal negotiations mapping (2 groups, 3 files)."""
    return {
        "akira": ["akira-20230529.html", "akira-20230606.html"],
        "conti": ["conti-20210107.html"],
    }


class TestUpdateSitemap(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def _write_mapping(self, mapping=None):
        path = os.path.join(self.tmpdir, "negotiations-mapping.json")
        if mapping is None:
            mapping = make_minimal_mapping()
        with open(path, "w") as f:
            json.dump(mapping, f)
        return path

    def _write_sitemap(self, entries):
        path = os.path.join(self.tmpdir, "sitemap.xml")
        with open(path, "w") as f:
            f.write(make_minimal_sitemap(entries))
        return path

    def _get_locs(self, sitemap_path):
        tree = ET.parse(sitemap_path)
        root = tree.getroot()
        return [
            e.find(f"{{{NS}}}loc").text
            for e in root.findall(f"{{{NS}}}url")
        ]

    # ------------------------------------------------------------------ #
    # 1. Valid XML output
    # ------------------------------------------------------------------ #
    def test_output_is_valid_xml(self):
        sitemap = self._write_sitemap([f"{BASE_URL}/"])
        mapping = self._write_mapping()
        mod.update_sitemap(sitemap, mapping)
        # Should not raise
        ET.parse(sitemap)

    # ------------------------------------------------------------------ #
    # 2. Flat negotiations URLs removed
    # ------------------------------------------------------------------ #
    def test_flat_negotiations_removed(self):
        sitemap = self._write_sitemap([
            f"{BASE_URL}/",
            f"{BASE_URL}/negotiations/akira-20230529.html",
            f"{BASE_URL}/negotiations/conti-20210107.html",
        ])
        mapping = self._write_mapping()
        mod.update_sitemap(sitemap, mapping)
        locs = self._get_locs(sitemap)
        self.assertNotIn(f"{BASE_URL}/negotiations/akira-20230529.html", locs)
        self.assertNotIn(f"{BASE_URL}/negotiations/conti-20210107.html", locs)

    # ------------------------------------------------------------------ #
    # 3. Grouped negotiations URLs added
    # ------------------------------------------------------------------ #
    def test_group_index_urls_added(self):
        sitemap = self._write_sitemap([f"{BASE_URL}/"])
        mapping = self._write_mapping()
        mod.update_sitemap(sitemap, mapping)
        locs = self._get_locs(sitemap)
        self.assertIn(f"{BASE_URL}/negotiations/akira/", locs)
        self.assertIn(f"{BASE_URL}/negotiations/conti/", locs)

    def test_transcript_urls_added(self):
        sitemap = self._write_sitemap([f"{BASE_URL}/"])
        mapping = self._write_mapping()
        mod.update_sitemap(sitemap, mapping)
        locs = self._get_locs(sitemap)
        self.assertIn(f"{BASE_URL}/negotiations/akira/akira-20230529.html", locs)
        self.assertIn(f"{BASE_URL}/negotiations/akira/akira-20230606.html", locs)
        self.assertIn(f"{BASE_URL}/negotiations/conti/conti-20210107.html", locs)

    # ------------------------------------------------------------------ #
    # 4. /for/ removed, /industries/ added
    # ------------------------------------------------------------------ #
    def test_for_urls_removed(self):
        sitemap = self._write_sitemap([
            f"{BASE_URL}/",
            f"{BASE_URL}/for/",
            f"{BASE_URL}/for/healthcare.html",
        ])
        mapping = self._write_mapping()
        mod.update_sitemap(sitemap, mapping)
        locs = self._get_locs(sitemap)
        for loc in locs:
            self.assertNotIn("/for/", loc, f"Found /for/ in {loc}")

    def test_industries_urls_added_from_for(self):
        sitemap = self._write_sitemap([
            f"{BASE_URL}/",
            f"{BASE_URL}/for/",
            f"{BASE_URL}/for/healthcare.html",
        ])
        mapping = self._write_mapping()
        mod.update_sitemap(sitemap, mapping)
        locs = self._get_locs(sitemap)
        self.assertIn(f"{BASE_URL}/industries/", locs)
        self.assertIn(f"{BASE_URL}/industries/healthcare.html", locs)

    def test_industries_added_even_if_for_missing(self):
        """If /for/ never existed in sitemap, /industries/ should still appear."""
        sitemap = self._write_sitemap([f"{BASE_URL}/"])
        mapping = self._write_mapping()
        mod.update_sitemap(sitemap, mapping)
        locs = self._get_locs(sitemap)
        # At minimum the root industries/ should be present
        self.assertIn(f"{BASE_URL}/industries/", locs)

    # ------------------------------------------------------------------ #
    # 5. No duplicate <url> entries
    # ------------------------------------------------------------------ #
    def test_no_duplicate_locs(self):
        sitemap = self._write_sitemap([
            f"{BASE_URL}/",
            f"{BASE_URL}/for/",
            f"{BASE_URL}/for/healthcare.html",
            f"{BASE_URL}/negotiations/akira-20230529.html",
        ])
        mapping = self._write_mapping()
        mod.update_sitemap(sitemap, mapping)
        locs = self._get_locs(sitemap)
        self.assertEqual(len(locs), len(set(locs)), "Duplicate URLs found")

    # ------------------------------------------------------------------ #
    # 6. Priority and changefreq for new URLs
    # ------------------------------------------------------------------ #
    def test_group_index_priority(self):
        sitemap = self._write_sitemap([f"{BASE_URL}/"])
        mapping = self._write_mapping()
        mod.update_sitemap(sitemap, mapping)
        tree = ET.parse(sitemap)
        root = tree.getroot()
        for url_elem in root.findall(f"{{{NS}}}url"):
            loc = url_elem.find(f"{{{NS}}}loc").text
            if loc == f"{BASE_URL}/negotiations/akira/":
                self.assertEqual(url_elem.find(f"{{{NS}}}priority").text, "0.7")
                self.assertEqual(url_elem.find(f"{{{NS}}}changefreq").text, "monthly")
                break
        else:
            self.fail("Group index URL not found")

    def test_transcript_priority(self):
        sitemap = self._write_sitemap([f"{BASE_URL}/"])
        mapping = self._write_mapping()
        mod.update_sitemap(sitemap, mapping)
        tree = ET.parse(sitemap)
        root = tree.getroot()
        for url_elem in root.findall(f"{{{NS}}}url"):
            loc = url_elem.find(f"{{{NS}}}loc").text
            if loc == f"{BASE_URL}/negotiations/akira/akira-20230529.html":
                self.assertEqual(url_elem.find(f"{{{NS}}}priority").text, "0.5")
                self.assertEqual(url_elem.find(f"{{{NS}}}changefreq").text, "yearly")
                break
        else:
            self.fail("Transcript URL not found")

    # ------------------------------------------------------------------ #
    # 7. dry_run does not write
    # ------------------------------------------------------------------ #
    def test_dry_run_does_not_modify_file(self):
        sitemap = self._write_sitemap([f"{BASE_URL}/"])
        mapping = self._write_mapping()
        mtime_before = os.path.getmtime(sitemap)
        import time
        time.sleep(0.01)
        mod.update_sitemap(sitemap, mapping, dry_run=True)
        mtime_after = os.path.getmtime(sitemap)
        self.assertEqual(mtime_before, mtime_after)

    # ------------------------------------------------------------------ #
    # 8. lastmod updated to TODAY
    # ------------------------------------------------------------------ #
    def test_lastmod_updated(self):
        sitemap = self._write_sitemap([f"{BASE_URL}/negotiations/"])
        mapping = self._write_mapping()
        mod.update_sitemap(sitemap, mapping)
        tree = ET.parse(sitemap)
        root = tree.getroot()
        for url_elem in root.findall(f"{{{NS}}}url"):
            loc = url_elem.find(f"{{{NS}}}loc").text
            if loc == f"{BASE_URL}/negotiations/":
                self.assertEqual(url_elem.find(f"{{{NS}}}lastmod").text, mod.TODAY)
                break

    # ------------------------------------------------------------------ #
    # 9. Missing mapping file raises FileNotFoundError
    # ------------------------------------------------------------------ #
    def test_missing_mapping_raises(self):
        sitemap = self._write_sitemap([f"{BASE_URL}/"])
        with self.assertRaises(FileNotFoundError):
            mod.update_sitemap(sitemap, "/nonexistent/path/mapping.json")

    # ------------------------------------------------------------------ #
    # 10. Integration test with real repo files
    # ------------------------------------------------------------------ #
    def test_integration_with_real_files(self):
        """Run against the real sitemap.xml and mapping to check acceptance criteria."""
        repo = Path(__file__).parent.parent
        sitemap_path = repo / "sitemap.xml"
        mapping_path = repo / "negotiations-mapping.json"

        if not sitemap_path.exists() or not mapping_path.exists():
            self.skipTest("Real sitemap.xml or mapping not found")

        # Parse the already-updated sitemap (or make a copy and re-run)
        tree = ET.parse(sitemap_path)
        root = tree.getroot()
        locs = [e.find(f"{{{NS}}}loc").text for e in root.findall(f"{{{NS}}}url")]

        # Acceptance criteria checks
        negotiations_locs = [l for l in locs if "/negotiations/" in l]
        self.assertGreaterEqual(len(negotiations_locs), 235,
                                f"Expected >= 235 negotiations URLs, got {len(negotiations_locs)}")

        flat_akira = [l for l in locs if "/negotiations/akira-" in l]
        self.assertEqual(len(flat_akira), 0,
                         f"Found flat akira URLs: {flat_akira[:3]}")

        grouped_akira = [l for l in locs if "/negotiations/akira/" in l]
        self.assertGreater(len(grouped_akira), 0, "No grouped akira URLs found")

        for_locs = [l for l in locs if "/for/" in l]
        self.assertEqual(len(for_locs), 0, f"Found /for/ URLs: {for_locs}")

        industries_locs = [l for l in locs if "/industries/" in l]
        self.assertGreaterEqual(len(industries_locs), 6,
                                f"Expected >= 6 industries URLs, got {len(industries_locs)}")


if __name__ == "__main__":
    unittest.main()
