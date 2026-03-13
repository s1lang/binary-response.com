#!/usr/bin/env python3
"""
Tests for scripts/create-for-redirects.py (US-009)
"""

import importlib.util
import os
import sys
import tempfile
import shutil
import unittest
from html.parser import HTMLParser

# Load the module under test (hyphenated filename)
SCRIPT_PATH = os.path.join(os.path.dirname(__file__), "create-for-redirects.py")
spec = importlib.util.spec_from_file_location("create_for_redirects", SCRIPT_PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


FOR_FILES = mod.FOR_FILES


def make_temp_repo():
    """Create a temporary directory with a /for/ structure."""
    tmp = tempfile.mkdtemp()
    for_dir = os.path.join(tmp, "for")
    os.makedirs(for_dir)
    for fname in FOR_FILES:
        with open(os.path.join(for_dir, fname), "w") as f:
            f.write("<html><body>original content</body></html>")
    return tmp


class TestCreateRedirectFiles(unittest.TestCase):

    def setUp(self):
        self.tmp = make_temp_repo()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_all_six_files_created(self):
        """All 6 for/*.html files get redirect stubs."""
        result = mod.create_redirect_files(self.tmp)
        self.assertTrue(result)
        for fname in FOR_FILES:
            path = os.path.join(self.tmp, "for", fname)
            self.assertTrue(os.path.exists(path), f"Missing: for/{fname}")

    def test_files_contain_meta_refresh(self):
        """Each redirect stub contains meta http-equiv='refresh'."""
        mod.create_redirect_files(self.tmp)
        for fname in FOR_FILES:
            path = os.path.join(self.tmp, "for", fname)
            with open(path) as f:
                content = f.read()
            self.assertIn('meta http-equiv="refresh"', content,
                          f"Missing meta refresh in for/{fname}")

    def test_files_point_to_industries(self):
        """Each redirect stub points to /industries/ equivalent."""
        mod.create_redirect_files(self.tmp)
        for fname in FOR_FILES:
            path = os.path.join(self.tmp, "for", fname)
            with open(path) as f:
                content = f.read()
            self.assertIn(f"/industries/{fname}", content,
                          f"Missing /industries/{fname} reference in for/{fname}")

    def test_canonical_link_present(self):
        """Each file has a canonical link pointing to industries URL."""
        mod.create_redirect_files(self.tmp)
        for fname in FOR_FILES:
            path = os.path.join(self.tmp, "for", fname)
            with open(path) as f:
                content = f.read()
            self.assertIn("canonical", content, f"Missing canonical in for/{fname}")
            self.assertIn("industries", content, f"Missing industries in canonical for/{fname}")

    def test_canonical_count_six(self):
        """All 6 files have canonical.*industries (acceptance criterion 4)."""
        mod.create_redirect_files(self.tmp)
        count = 0
        for fname in FOR_FILES:
            path = os.path.join(self.tmp, "for", fname)
            with open(path) as f:
                content = f.read()
            if "canonical" in content and "industries" in content:
                count += 1
        self.assertEqual(count, 6)

    def test_index_redirect_points_to_industries_index(self):
        """for/index.html redirects to /industries/index.html."""
        mod.create_redirect_files(self.tmp)
        path = os.path.join(self.tmp, "for", "index.html")
        with open(path) as f:
            content = f.read()
        self.assertIn("/industries/index.html", content)

    def test_html_parses_without_error(self):
        """All 6 for/ redirect files parse cleanly with html.parser."""
        mod.create_redirect_files(self.tmp)
        parser = HTMLParser()
        for fname in FOR_FILES:
            path = os.path.join(self.tmp, "for", fname)
            with open(path) as f:
                content = f.read()
            # If this raises, the test fails
            try:
                parser.feed(content)
            except Exception as e:
                self.fail(f"html.parser raised on for/{fname}: {e}")

    def test_dry_run_does_not_modify_files(self):
        """Dry-run mode doesn't overwrite existing files."""
        # Mark original content
        original = {}
        for fname in FOR_FILES:
            path = os.path.join(self.tmp, "for", fname)
            with open(path) as f:
                original[fname] = f.read()

        mod.create_redirect_files(self.tmp, dry_run=True)

        for fname in FOR_FILES:
            path = os.path.join(self.tmp, "for", fname)
            with open(path) as f:
                current = f.read()
            self.assertEqual(original[fname], current,
                             f"Dry-run modified for/{fname}")

    def test_missing_for_directory_returns_false(self):
        """Returns False if /for/ directory doesn't exist."""
        shutil.rmtree(os.path.join(self.tmp, "for"))
        result = mod.create_redirect_files(self.tmp)
        self.assertFalse(result)


class TestUpdateHtaccess(unittest.TestCase):

    def setUp(self):
        self.tmp = make_temp_repo()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def _write_htaccess(self, content):
        with open(os.path.join(self.tmp, ".htaccess"), "w") as f:
            f.write(content)

    def _read_htaccess(self):
        with open(os.path.join(self.tmp, ".htaccess")) as f:
            return f.read()

    def test_adds_redirect_match_rule(self):
        """Adds RedirectMatch 301 rule to .htaccess."""
        self._write_htaccess("Options -Indexes\n")
        mod.update_htaccess(self.tmp)
        content = self._read_htaccess()
        self.assertIn("RedirectMatch 301 ^/for/(.*)$ /industries/$1", content)

    def test_block_delimiters_present(self):
        """BEGIN/END block markers are added."""
        self._write_htaccess("")
        mod.update_htaccess(self.tmp)
        content = self._read_htaccess()
        self.assertIn("# BEGIN for-redirects", content)
        self.assertIn("# END for-redirects", content)

    def test_idempotent_does_not_duplicate(self):
        """Running twice doesn't duplicate the block."""
        self._write_htaccess("")
        mod.update_htaccess(self.tmp)
        mod.update_htaccess(self.tmp)
        content = self._read_htaccess()
        self.assertEqual(content.count("# BEGIN for-redirects"), 1)

    def test_creates_htaccess_if_missing(self):
        """Creates .htaccess if it doesn't exist."""
        htaccess = os.path.join(self.tmp, ".htaccess")
        if os.path.exists(htaccess):
            os.remove(htaccess)
        mod.update_htaccess(self.tmp)
        self.assertTrue(os.path.exists(htaccess))
        content = self._read_htaccess()
        self.assertIn("RedirectMatch 301", content)

    def test_dry_run_does_not_modify_htaccess(self):
        """Dry-run doesn't write to .htaccess."""
        self._write_htaccess("# existing\n")
        mod.update_htaccess(self.tmp, dry_run=True)
        content = self._read_htaccess()
        self.assertEqual(content, "# existing\n")

    def test_preserves_existing_htaccess_content(self):
        """Existing .htaccess content is preserved."""
        self._write_htaccess("# existing rules\nOptions -Indexes\n")
        mod.update_htaccess(self.tmp)
        content = self._read_htaccess()
        self.assertIn("# existing rules", content)
        self.assertIn("Options -Indexes", content)


class TestMainScript(unittest.TestCase):

    def setUp(self):
        self.tmp = make_temp_repo()
        self.orig_argv = sys.argv

    def tearDown(self):
        shutil.rmtree(self.tmp)
        sys.argv = self.orig_argv

    def test_main_exits_zero_on_success(self):
        """main() exits 0 when everything works."""
        # Patch REPO_ROOT in module
        orig_root = mod.REPO_ROOT
        mod.REPO_ROOT = self.tmp
        sys.argv = ["create-for-redirects.py"]
        try:
            with self.assertRaises(SystemExit) as ctx:
                mod.main()
            self.assertEqual(ctx.exception.code, 0)
        finally:
            mod.REPO_ROOT = orig_root


if __name__ == "__main__":
    unittest.main()
