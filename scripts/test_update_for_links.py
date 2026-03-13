#!/usr/bin/env python3
"""
Tests for scripts/update-for-links.py (US-008)
"""
import importlib.util
import os
import sys
import tempfile
import shutil
import unittest

# Load the module via importlib (hyphenated filename)
_SCRIPT = os.path.join(os.path.dirname(__file__), 'update-for-links.py')
_spec = importlib.util.spec_from_file_location('update_for_links', _SCRIPT)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

find_files_with_for_refs = _mod.find_files_with_for_refs
update_file = _mod.update_file
main = _mod.main

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TestFindFiles(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def _write(self, relpath, content):
        fpath = os.path.join(self.tmp, relpath)
        os.makedirs(os.path.dirname(fpath), exist_ok=True)
        with open(fpath, 'w') as f:
            f.write(content)
        return fpath

    def test_finds_html_with_for_ref(self):
        self._write('index.html', '<a href="/for/healthcare.html">Healthcare</a>')
        result = find_files_with_for_refs(self.tmp)
        self.assertEqual(len(result), 1)
        self.assertTrue(result[0].endswith('index.html'))

    def test_finds_js_with_for_ref(self):
        self._write('js/nav.js', 'href="/for/"')
        result = find_files_with_for_refs(self.tmp)
        self.assertEqual(len(result), 1)

    def test_skips_for_directory(self):
        self._write('for/index.html', '<a href="/for/healthcare.html">')
        result = find_files_with_for_refs(self.tmp)
        self.assertEqual(result, [])

    def test_skips_nested_for_directory(self):
        self._write('for/sub/page.html', 'href="/for/test.html"')
        result = find_files_with_for_refs(self.tmp)
        self.assertEqual(result, [])

    def test_skips_files_without_for_ref(self):
        self._write('index.html', '<a href="/services/">Services</a>')
        result = find_files_with_for_refs(self.tmp)
        self.assertEqual(result, [])

    def test_does_not_false_positive_on_before(self):
        self._write('index.html', '<a href="/before/page.html">Before</a>')
        result = find_files_with_for_refs(self.tmp)
        self.assertEqual(result, [])

    def test_skips_git_directory(self):
        self._write('.git/config', 'href="/for/test.html"')
        result = find_files_with_for_refs(self.tmp)
        self.assertEqual(result, [])

    def test_only_html_and_js_extensions(self):
        self._write('data.json', '{"url": "/for/test.html"}')
        self._write('style.css', '.for { color: red; }')
        result = find_files_with_for_refs(self.tmp)
        self.assertEqual(result, [])


class TestUpdateFile(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def _write(self, name, content):
        fpath = os.path.join(self.tmp, name)
        with open(fpath, 'w') as f:
            f.write(content)
        return fpath

    def test_replaces_for_with_industries(self):
        fpath = self._write('nav.js', 'href="/for/healthcare.html"')
        changed, count = update_file(fpath)
        self.assertTrue(changed)
        self.assertEqual(count, 1)
        with open(fpath) as f:
            self.assertEqual(f.read(), 'href="/industries/healthcare.html"')

    def test_dry_run_does_not_modify(self):
        original = 'href="/for/healthcare.html"'
        fpath = self._write('nav.js', original)
        changed, count = update_file(fpath, dry_run=True)
        self.assertTrue(changed)
        with open(fpath) as f:
            self.assertEqual(f.read(), original)

    def test_unchanged_file_returns_false(self):
        fpath = self._write('nav.js', 'href="/industries/healthcare.html"')
        changed, count = update_file(fpath)
        self.assertFalse(changed)
        self.assertEqual(count, 0)

    def test_multiple_replacements(self):
        content = 'href="/for/a.html" href="/for/b.html" href="/for/"'
        fpath = self._write('nav.js', content)
        changed, count = update_file(fpath)
        self.assertTrue(changed)
        self.assertEqual(count, 3)
        with open(fpath) as f:
            result = f.read()
        self.assertNotIn('/for/', result)
        self.assertEqual(result.count('/industries/'), 3)

    def test_relative_path_replacement(self):
        # ../for/ style relative paths (as in negotiations/index.html)
        fpath = self._write('index.html', '<a href="../for/healthcare.html">Healthcare</a>')
        changed, count = update_file(fpath)
        self.assertTrue(changed)
        with open(fpath) as f:
            result = f.read()
        self.assertIn('../industries/healthcare.html', result)
        self.assertNotIn('/for/', result)


class TestMain(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        # Create a structure that mimics the repo
        os.makedirs(os.path.join(self.tmp, 'js'))
        os.makedirs(os.path.join(self.tmp, 'for'))
        os.makedirs(os.path.join(self.tmp, 'scripts'))

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def _write(self, relpath, content):
        fpath = os.path.join(self.tmp, relpath)
        os.makedirs(os.path.dirname(fpath), exist_ok=True)
        with open(fpath, 'w') as f:
            f.write(content)
        return fpath

    def test_main_updates_files_and_exits_zero(self):
        self._write('js/nav.js', 'href="/for/healthcare.html"')
        ret = main(['--repo-root', self.tmp])
        self.assertEqual(ret, 0)
        with open(os.path.join(self.tmp, 'js/nav.js')) as f:
            self.assertIn('/industries/', f.read())

    def test_main_dry_run_exits_zero_no_changes(self):
        self._write('js/nav.js', 'href="/for/healthcare.html"')
        ret = main(['--dry-run', '--repo-root', self.tmp])
        self.assertEqual(ret, 0)
        # File should still have /for/
        with open(os.path.join(self.tmp, 'js/nav.js')) as f:
            self.assertIn('/for/', f.read())

    def test_main_no_files_exits_zero(self):
        self._write('js/nav.js', 'href="/industries/healthcare.html"')
        ret = main(['--repo-root', self.tmp])
        self.assertEqual(ret, 0)

    def test_main_skips_for_directory(self):
        self._write('for/index.html', 'href="/for/healthcare.html"')
        ret = main(['--repo-root', self.tmp])
        self.assertEqual(ret, 0)
        # for/index.html should be untouched
        with open(os.path.join(self.tmp, 'for/index.html')) as f:
            self.assertIn('/for/', f.read())


class TestActualRepo(unittest.TestCase):
    """Integration tests against the actual repo."""

    def test_nav_js_has_industries_links(self):
        nav_path = os.path.join(REPO_ROOT, 'js', 'nav.js')
        self.assertTrue(os.path.exists(nav_path), 'js/nav.js not found')
        with open(nav_path) as f:
            content = f.read()
        self.assertIn('/industries/healthcare.html', content)
        self.assertIn('/industries/legal.html', content)
        self.assertIn('/industries/manufacturing.html', content)
        self.assertIn('/industries/financial-services.html', content)
        self.assertIn('/industries/education.html', content)

    def test_nav_js_has_no_for_refs(self):
        nav_path = os.path.join(REPO_ROOT, 'js', 'nav.js')
        with open(nav_path) as f:
            content = f.read()
        self.assertNotIn('/for/', content)

    def test_nav_js_industries_label(self):
        nav_path = os.path.join(REPO_ROOT, 'js', 'nav.js')
        with open(nav_path) as f:
            content = f.read()
        self.assertIn('Industries', content)

    def test_no_for_refs_outside_for_dir(self):
        """No HTML/JS files outside /for/ should reference /for/."""
        files = find_files_with_for_refs(REPO_ROOT)
        self.assertEqual(files, [],
            f'Files outside /for/ still reference /for/: {files}')

    def test_script_exits_zero_when_run_on_clean_repo(self):
        """Running the script again on already-updated repo should exit 0."""
        ret = main(['--repo-root', REPO_ROOT])
        self.assertEqual(ret, 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
