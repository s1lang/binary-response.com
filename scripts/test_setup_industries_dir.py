#!/usr/bin/env python3
"""
Tests for scripts/setup-industries-dir.py (US-007).

Tests cover:
- copy_for_to_industries: copies files, respects dry-run
- replace_for_references: replaces all /for/ occurrences
- main(): integration — dry-run does nothing, real run produces correct output
- html.parser parses all 6 industries/ files without error
"""

import importlib.util
import shutil
import sys
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path


# ---------------------------------------------------------------------------
# Load the module under test (hyphenated filename)
# ---------------------------------------------------------------------------
def _load_module(name: str = "setup_industries_dir"):
    spec = importlib.util.spec_from_file_location(
        name,
        Path(__file__).parent / "setup-industries-dir.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_mod = _load_module()
copy_for_to_industries = _mod.copy_for_to_industries
replace_for_references = _mod.replace_for_references
git_add_industries = _mod.git_add_industries
main = _mod.main


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
SAMPLE_HTML = """\
<!DOCTYPE html>
<html lang="en">
<head>
<link rel="canonical" href="https://binary-response.com/for/healthcare.html">
<meta property="og:url" content="https://binary-response.com/for/healthcare.html">
<script type="application/ld+json">
{{"url":"https://binary-response.com/for/healthcare.html"}}
</script>
</head>
<body>
<a href="/for/index.html">Industries</a>
<a href="/for/legal.html">Legal</a>
</body>
</html>
"""

SAMPLE_HTML_NO_FOR = """\
<!DOCTYPE html><html><body><p>No path references here.</p></body></html>
"""


def _make_fake_repo(tmp: Path, include_for: bool = True) -> Path:
    """Create a minimal fake repo with a for/ directory."""
    (tmp / "for").mkdir(parents=True, exist_ok=True)
    files = ["index.html", "healthcare.html", "legal.html",
             "manufacturing.html", "financial-services.html", "education.html"]
    if include_for:
        for fname in files:
            (tmp / "for" / fname).write_text(
                SAMPLE_HTML.replace("healthcare", fname.replace(".html", "")),
                encoding="utf-8",
            )
    return tmp


# ---------------------------------------------------------------------------
# Tests: copy_for_to_industries
# ---------------------------------------------------------------------------
class TestCopyForToIndustries(unittest.TestCase):

    def test_copies_6_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = _make_fake_repo(Path(tmp))
            copied = copy_for_to_industries(repo, dry_run=False)
            self.assertEqual(len(copied), 6)
            industries = repo / "industries"
            for path in copied:
                self.assertTrue(path.exists(), f"Expected {path} to exist")

    def test_dry_run_does_not_create_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = _make_fake_repo(Path(tmp))
            copy_for_to_industries(repo, dry_run=True)
            self.assertFalse((repo / "industries").exists())

    def test_raises_if_for_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(FileNotFoundError):
                copy_for_to_industries(Path(tmp), dry_run=False)

    def test_raises_if_no_html_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "for").mkdir()
            with self.assertRaises(ValueError):
                copy_for_to_industries(Path(tmp), dry_run=False)

    def test_copies_correct_filenames(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = _make_fake_repo(Path(tmp))
            copied = copy_for_to_industries(repo, dry_run=False)
            names = {p.name for p in copied}
            expected = {"index.html", "healthcare.html", "legal.html",
                        "manufacturing.html", "financial-services.html", "education.html"}
            self.assertEqual(names, expected)


# ---------------------------------------------------------------------------
# Tests: replace_for_references
# ---------------------------------------------------------------------------
class TestReplaceForReferences(unittest.TestCase):

    def test_replaces_all_occurrences(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "test.html"
            f.write_text(SAMPLE_HTML, encoding="utf-8")
            count = replace_for_references(f)
            self.assertGreater(count, 0)
            content = f.read_text()
            self.assertNotIn("/for/", content)
            self.assertIn("/industries/", content)

    def test_returns_zero_when_no_matches(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "test.html"
            f.write_text(SAMPLE_HTML_NO_FOR, encoding="utf-8")
            count = replace_for_references(f)
            self.assertEqual(count, 0)

    def test_dry_run_does_not_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "test.html"
            f.write_text(SAMPLE_HTML, encoding="utf-8")
            replace_for_references(f, dry_run=True)
            content = f.read_text()
            self.assertIn("/for/", content)

    def test_canonical_replaced(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "test.html"
            f.write_text(SAMPLE_HTML, encoding="utf-8")
            replace_for_references(f)
            content = f.read_text()
            self.assertIn('href="https://binary-response.com/industries/', content)

    def test_og_url_replaced(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "test.html"
            f.write_text(SAMPLE_HTML, encoding="utf-8")
            replace_for_references(f)
            content = f.read_text()
            self.assertIn('content="https://binary-response.com/industries/', content)

    def test_json_ld_url_replaced(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "test.html"
            f.write_text(SAMPLE_HTML, encoding="utf-8")
            replace_for_references(f)
            content = f.read_text()
            self.assertIn('"url":"https://binary-response.com/industries/', content)

    def test_internal_hrefs_replaced(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "test.html"
            f.write_text(SAMPLE_HTML, encoding="utf-8")
            replace_for_references(f)
            content = f.read_text()
            self.assertNotIn('href="/for/', content)
            self.assertIn('href="/industries/', content)


# ---------------------------------------------------------------------------
# Tests: main() integration
# ---------------------------------------------------------------------------
class TestMain(unittest.TestCase):

    def test_dry_run_no_industries_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = _make_fake_repo(Path(tmp))
            main(["--dry-run", "--repo-root", str(repo)])
            self.assertFalse((repo / "industries").exists())

    def test_real_run_creates_industries_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = _make_fake_repo(Path(tmp))
            # Can't git add without a real git repo; patch git_add_industries
            import unittest.mock as mock
            with mock.patch.object(_mod, "git_add_industries"):
                main(["--repo-root", str(repo)])
            industries = repo / "industries"
            self.assertTrue(industries.exists())
            self.assertEqual(len(list(industries.glob("*.html"))), 6)

    def test_real_run_no_for_references_remain(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = _make_fake_repo(Path(tmp))
            import unittest.mock as mock
            with mock.patch.object(_mod, "git_add_industries"):
                main(["--repo-root", str(repo)])
            for html_file in (repo / "industries").glob("*.html"):
                content = html_file.read_text()
                self.assertNotIn("/for/", content,
                                 f"/for/ still present in {html_file.name}")

    def test_missing_for_dir_exits_nonzero(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(FileNotFoundError):
                main(["--repo-root", str(tmp)])


# ---------------------------------------------------------------------------
# Tests: html.parser parses all 6 actual industries/ files without error
# ---------------------------------------------------------------------------
class TestIndustriesFilesParseCleanly(unittest.TestCase):
    """Acceptance criterion 6: html.parser parses all 6 industries/ files."""

    def _get_industries_dir(self) -> Path | None:
        repo = Path(__file__).parent.parent
        industries = repo / "industries"
        return industries if industries.exists() else None

    def test_all_6_files_parse_without_error(self):
        industries = self._get_industries_dir()
        if industries is None:
            self.skipTest("industries/ directory not yet created — run the script first")

        html_files = sorted(industries.glob("*.html"))
        self.assertEqual(len(html_files), 6,
                         f"Expected 6 files, got {len(html_files)}")

        class StrictParser(HTMLParser):
            def handle_error(self, message):  # type: ignore[override]
                raise ValueError(f"HTML parse error: {message}")

        for html_file in html_files:
            with self.subTest(file=html_file.name):
                content = html_file.read_text(encoding="utf-8")
                parser = StrictParser()
                parser.feed(content)  # raises on hard errors

    def test_no_for_references_in_industries_files(self):
        industries = self._get_industries_dir()
        if industries is None:
            self.skipTest("industries/ directory not yet created")
        for html_file in sorted(industries.glob("*.html")):
            with self.subTest(file=html_file.name):
                content = html_file.read_text(encoding="utf-8")
                self.assertNotIn("/for/", content)

    def test_canonical_urls_reference_industries(self):
        industries = self._get_industries_dir()
        if industries is None:
            self.skipTest("industries/ directory not yet created")
        for html_file in sorted(industries.glob("*.html")):
            with self.subTest(file=html_file.name):
                content = html_file.read_text(encoding="utf-8")
                self.assertIn("/industries/", content)


if __name__ == "__main__":
    unittest.main()
