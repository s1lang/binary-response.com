#!/usr/bin/env python3
"""
Tests for scripts/create-negotiations-redirects.py (US-003).
"""

import importlib.util
import json
import os
import sys
import tempfile
import unittest

# Import hyphen-named module via importlib
_script_dir = os.path.dirname(__file__)
_spec = importlib.util.spec_from_file_location(
    "create_negotiations_redirects",
    os.path.join(_script_dir, "create-negotiations-redirects.py"),
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
create_redirects = _mod.create_redirects
REDIRECT_TEMPLATE = _mod.REDIRECT_TEMPLATE


def _build_fake_repo(tmpdir: str, mapping: dict) -> str:
    """Set up a fake repo with negotiations-mapping.json and the
    negotiations/{group}/{filename} target files already in place."""
    # Write mapping
    mapping_path = os.path.join(tmpdir, "negotiations-mapping.json")
    with open(mapping_path, "w") as f:
        json.dump(mapping, f)

    # Create negotiations dir and subdirectory target files
    for group, files in mapping.items():
        group_dir = os.path.join(tmpdir, "negotiations", group)
        os.makedirs(group_dir, exist_ok=True)
        for filename in files:
            target = os.path.join(group_dir, filename)
            with open(target, "w") as f:
                f.write("<html>transcript</html>")

    return tmpdir


class TestDryRun(unittest.TestCase):
    def test_dry_run_does_not_create_files(self):
        mapping = {"akira": ["akira-20230529.html", "akira-20230606.html"]}
        with tempfile.TemporaryDirectory() as tmp:
            _build_fake_repo(tmp, mapping)
            create_redirects(tmp, dry_run=True)
            # Nothing should have been created in negotiations/ at the flat level
            flat_files = [
                f for f in os.listdir(os.path.join(tmp, "negotiations"))
                if os.path.isfile(os.path.join(tmp, "negotiations", f))
            ]
            self.assertEqual(flat_files, [], "Dry run should not create files")

    def test_dry_run_returns_correct_count(self):
        mapping = {"lockbit3-0": ["royal-mail-lockbit-3.html", "lockbit3-20220101.html"]}
        with tempfile.TemporaryDirectory() as tmp:
            _build_fake_repo(tmp, mapping)
            count = create_redirects(tmp, dry_run=True)
            self.assertEqual(count, 2)


class TestRedirectContent(unittest.TestCase):
    def _run_and_read(self, mapping, filename, group):
        with tempfile.TemporaryDirectory() as tmp:
            _build_fake_repo(tmp, mapping)
            create_redirects(tmp, dry_run=False)
            redirect_path = os.path.join(tmp, "negotiations", filename)
            self.assertTrue(os.path.exists(redirect_path), f"Redirect file not created: {redirect_path}")
            with open(redirect_path) as f:
                return f.read()

    def test_akira_redirect_contains_meta_refresh(self):
        mapping = {"akira": ["akira-20230529.html"]}
        content = self._run_and_read(mapping, "akira-20230529.html", "akira")
        self.assertIn('meta http-equiv="refresh"', content)
        self.assertIn('url=/negotiations/akira/akira-20230529.html', content)

    def test_akira_redirect_contains_canonical(self):
        mapping = {"akira": ["akira-20230529.html"]}
        content = self._run_and_read(mapping, "akira-20230529.html", "akira")
        self.assertIn(
            'href="https://binary-response.com/negotiations/akira/akira-20230529.html"',
            content,
        )

    def test_lockbit3_royal_mail_redirect(self):
        """royal-mail-lockbit-3.html should redirect to lockbit3-0 group."""
        mapping = {"lockbit3-0": ["royal-mail-lockbit-3.html"]}
        content = self._run_and_read(mapping, "royal-mail-lockbit-3.html", "lockbit3-0")
        self.assertIn('url=/negotiations/lockbit3-0/royal-mail-lockbit-3.html', content)
        self.assertIn(
            'href="https://binary-response.com/negotiations/lockbit3-0/royal-mail-lockbit-3.html"',
            content,
        )

    def test_conti_redirect(self):
        mapping = {"conti": ["conti-20210107.html"]}
        content = self._run_and_read(mapping, "conti-20210107.html", "conti")
        self.assertIn('url=/negotiations/conti/conti-20210107.html', content)

    def test_redirect_does_not_point_to_itself(self):
        """Redirect URL must include /negotiations/{group}/ — not the flat URL."""
        mapping = {"akira": ["akira-20230529.html"]}
        content = self._run_and_read(mapping, "akira-20230529.html", "akira")
        # The refresh target must go into a subdirectory, not flat negotiations/
        import re
        match = re.search(r"content=\"0;url=([^\"]+)\"", content)
        self.assertIsNotNone(match)
        url = match.group(1)
        self.assertNotEqual(url, "/negotiations/akira-20230529.html")
        self.assertIn("/negotiations/akira/", url)


class TestMultipleGroups(unittest.TestCase):
    def test_creates_correct_total_count(self):
        mapping = {
            "akira": ["akira-20230529.html", "akira-20230606.html"],
            "conti": ["conti-20210107.html"],
            "lockbit3-0": ["royal-mail-lockbit-3.html"],
        }
        with tempfile.TemporaryDirectory() as tmp:
            _build_fake_repo(tmp, mapping)
            count = create_redirects(tmp, dry_run=False)
            self.assertEqual(count, 4)

    def test_all_redirect_files_exist(self):
        mapping = {
            "akira": ["akira-20230529.html", "akira-20230606.html"],
            "conti": ["conti-20210107.html"],
        }
        with tempfile.TemporaryDirectory() as tmp:
            _build_fake_repo(tmp, mapping)
            create_redirects(tmp, dry_run=False)
            for group, files in mapping.items():
                for filename in files:
                    path = os.path.join(tmp, "negotiations", filename)
                    self.assertTrue(os.path.exists(path), f"Missing redirect: {path}")


class TestMissingMapping(unittest.TestCase):
    def test_exits_on_missing_mapping(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.makedirs(os.path.join(tmp, "negotiations"))
            with self.assertRaises(SystemExit):
                create_redirects(tmp)


if __name__ == "__main__":
    unittest.main()
