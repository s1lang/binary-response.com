#!/usr/bin/env python3
"""
Tests for scripts/add-negotiations-htaccess.py (US-006).
"""

import importlib.util
import os
import sys
import tempfile
import unittest

# Load module with hyphenated filename
SCRIPT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "add-negotiations-htaccess.py")
spec = importlib.util.spec_from_file_location("add_negotiations_htaccess", SCRIPT_PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


SAMPLE_MAPPING = {
    "akira": ["akira-20230529.html", "akira-20230606.html"],
    "conti": ["conti-20210107.html"],
    "lockbit3-0": ["royal-mail-lockbit-3-0-20230213.html"],
}


class TestBuildRedirectBlock(unittest.TestCase):

    def test_begins_and_ends_with_markers(self):
        block = mod.build_redirect_block(SAMPLE_MAPPING)
        self.assertIn("# BEGIN negotiations-redirects", block)
        self.assertIn("# END negotiations-redirects", block)

    def test_correct_redirect_count(self):
        block = mod.build_redirect_block(SAMPLE_MAPPING)
        count = block.count("Redirect 301 /negotiations/")
        self.assertEqual(count, 4)

    def test_redirect_format(self):
        block = mod.build_redirect_block(SAMPLE_MAPPING)
        self.assertIn(
            "Redirect 301 /negotiations/akira-20230529.html /negotiations/akira/akira-20230529.html",
            block
        )

    def test_lockbit3_0_mapping(self):
        block = mod.build_redirect_block(SAMPLE_MAPPING)
        self.assertIn(
            "Redirect 301 /negotiations/royal-mail-lockbit-3-0-20230213.html "
            "/negotiations/lockbit3-0/royal-mail-lockbit-3-0-20230213.html",
            block
        )

    def test_groups_sorted_alphabetically(self):
        block = mod.build_redirect_block(SAMPLE_MAPPING)
        akira_pos = block.index("# akira")
        conti_pos = block.index("# conti")
        lockbit_pos = block.index("# lockbit3-0")
        self.assertLess(akira_pos, conti_pos)
        self.assertLess(conti_pos, lockbit_pos)

    def test_no_duplicate_redirect_entries(self):
        block = mod.build_redirect_block(SAMPLE_MAPPING)
        lines = [l.strip() for l in block.splitlines() if l.startswith("Redirect")]
        self.assertEqual(len(lines), len(set(lines)), "Duplicate redirect entries found")

    def test_group_comment_headers(self):
        block = mod.build_redirect_block(SAMPLE_MAPPING)
        self.assertIn("# akira", block)
        self.assertIn("# conti", block)
        self.assertIn("# lockbit3-0", block)


class TestStripExistingBlock(unittest.TestCase):

    def test_no_existing_block(self):
        content = "# some rules\nOptions -Indexes\n"
        result = mod.strip_existing_block(content)
        self.assertEqual(result, content)

    def test_strips_existing_block(self):
        original = "# original rules\nOptions -Indexes\n"
        block = "# BEGIN negotiations-redirects\nRedirect 301 /a /b\n# END negotiations-redirects\n"
        combined = original + "\n" + block
        result = mod.strip_existing_block(combined)
        self.assertNotIn("# BEGIN negotiations-redirects", result)
        self.assertNotIn("Redirect 301 /a /b", result)
        self.assertIn("# original rules", result)

    def test_strips_and_preserves_content_after_block(self):
        content = "before\n\n# BEGIN negotiations-redirects\nRedirect 301 /x /y\n# END negotiations-redirects\nafter\n"
        result = mod.strip_existing_block(content)
        self.assertIn("before", result)
        self.assertIn("after", result)
        self.assertNotIn("BEGIN", result)


class TestIntegration(unittest.TestCase):

    def _make_temp_mapping(self, mapping):
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        import json
        json.dump(mapping, f)
        f.close()
        return f.name

    def _make_temp_htaccess(self, content):
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".htaccess", delete=False)
        f.write(content)
        f.close()
        return f.name

    def test_dry_run_does_not_modify_file(self):
        htaccess_path = self._make_temp_htaccess("# original\n")
        mapping_path = self._make_temp_mapping(SAMPLE_MAPPING)
        original_content = open(htaccess_path).read()

        mod.main(["--dry-run", "--mapping", mapping_path, "--htaccess", htaccess_path])

        self.assertEqual(open(htaccess_path).read(), original_content)
        os.unlink(htaccess_path)
        os.unlink(mapping_path)

    def test_writes_block_to_htaccess(self):
        original_htaccess = "# Force HTTPS\nOptions -Indexes\n"
        htaccess_path = self._make_temp_htaccess(original_htaccess)
        mapping_path = self._make_temp_mapping(SAMPLE_MAPPING)

        ret = mod.main(["--mapping", mapping_path, "--htaccess", htaccess_path])

        self.assertEqual(ret, 0)
        result = open(htaccess_path).read()
        self.assertIn("# BEGIN negotiations-redirects", result)
        self.assertIn("# END negotiations-redirects", result)
        self.assertIn("# Force HTTPS", result)
        self.assertEqual(result.count("Redirect 301 /negotiations/"), 4)
        os.unlink(htaccess_path)
        os.unlink(mapping_path)

    def test_existing_block_replaced_not_duplicated(self):
        original_htaccess = "# rules\n\n# BEGIN negotiations-redirects\nRedirect 301 /old /new\n# END negotiations-redirects\n"
        htaccess_path = self._make_temp_htaccess(original_htaccess)
        mapping_path = self._make_temp_mapping(SAMPLE_MAPPING)

        mod.main(["--mapping", mapping_path, "--htaccess", htaccess_path])

        result = open(htaccess_path).read()
        # Only one BEGIN marker
        self.assertEqual(result.count("# BEGIN negotiations-redirects"), 1)
        # Old redirect gone, new ones present
        self.assertNotIn("Redirect 301 /old /new", result)
        self.assertEqual(result.count("Redirect 301 /negotiations/"), 4)
        os.unlink(htaccess_path)
        os.unlink(mapping_path)

    def test_missing_mapping_file_raises(self):
        with self.assertRaises(FileNotFoundError):
            mod.load_mapping("/nonexistent/path.json")

    def test_original_htaccess_content_preserved(self):
        original_lines = ["# Force HTTPS and non-www canonical URL\n",
                          "<IfModule mod_rewrite.c>\n",
                          "    RewriteEngine On\n"]
        original_htaccess = "".join(original_lines)
        htaccess_path = self._make_temp_htaccess(original_htaccess)
        mapping_path = self._make_temp_mapping(SAMPLE_MAPPING)

        mod.main(["--mapping", mapping_path, "--htaccess", htaccess_path])

        result = open(htaccess_path).read()
        for line in original_lines:
            self.assertIn(line.strip(), result)

        # Redirects come AFTER original content
        orig_end = result.index("RewriteEngine On")
        block_start = result.index("# BEGIN negotiations-redirects")
        self.assertLess(orig_end, block_start)
        os.unlink(htaccess_path)
        os.unlink(mapping_path)


if __name__ == "__main__":
    unittest.main()
