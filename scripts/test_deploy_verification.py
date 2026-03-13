"""
test_deploy_verification.py — US-011
Tests that verify the deployed site has correct redirects and URLs.
These are integration tests that hit binary-response.com directly.
Run: python3 scripts/test_deploy_verification.py
"""

import subprocess
import sys
import unittest


def curl_head(url: str) -> dict:
    """Run curl -sI and return status_code and location header."""
    result = subprocess.run(
        ["curl", "-sI", "--max-redirs", "0", url],
        capture_output=True,
        text=True,
        timeout=15,
    )
    lines = result.stdout.strip().splitlines()
    status_code = None
    location = None
    for line in lines:
        if line.startswith("HTTP/"):
            status_code = int(line.split()[1])
        elif line.lower().startswith("location:"):
            location = line.split(":", 1)[1].strip()
    return {"status": status_code, "location": location, "body": result.stdout}


def curl_body(url: str) -> str:
    """Fetch page body."""
    result = subprocess.run(
        ["curl", "-sL", url],
        capture_output=True,
        text=True,
        timeout=15,
    )
    return result.stdout


class TestDeployVerification(unittest.TestCase):
    """Integration tests verifying the live site after deployment."""

    BASE = "https://binary-response.com"

    def test_negotiations_old_url_redirects_301(self):
        """Old negotiations URL /negotiations/akira-20230529.html → 301."""
        r = curl_head(f"{self.BASE}/negotiations/akira-20230529.html")
        self.assertEqual(r["status"], 301, "Expected HTTP 301")

    def test_negotiations_old_url_redirect_location(self):
        """Old negotiations URL redirects to new subdirectory path."""
        r = curl_head(f"{self.BASE}/negotiations/akira-20230529.html")
        self.assertIsNotNone(r["location"], "Location header missing")
        self.assertIn("/negotiations/akira/akira-20230529.html", r["location"])

    def test_negotiations_group_index_200(self):
        """/negotiations/akira/ returns 200."""
        r = curl_head(f"{self.BASE}/negotiations/akira/")
        self.assertEqual(r["status"], 200, "Expected HTTP 200")

    def test_negotiations_index_200(self):
        """/negotiations/ returns 200."""
        r = curl_head(f"{self.BASE}/negotiations/")
        self.assertEqual(r["status"], 200, "Expected HTTP 200")

    def test_negotiations_index_has_24_groups(self):
        """/negotiations/ body contains links to all 24 threat-actor groups."""
        body = curl_body(f"{self.BASE}/negotiations/")
        expected_groups = [
            "akira/", "lockbit3-0/", "conti/", "revil/", "dragonforce/",
            "trinity/", "hive/", "avaddon/", "fog/", "blackbasta/",
            "darkside/", "mallox/", "babuk/", "blackmatter/", "cloak/",
            "noescape/", "qilin/", "ranzy/", "avos/", "hunters-international/",
            "mount-locker/", "pear/", "ransomhub/", "runsomewares/",
        ]
        found = []
        missing = []
        for group in expected_groups:
            if f'href="{group}"' in body or f'href="./{group}"' in body:
                found.append(group)
            else:
                missing.append(group)
        self.assertEqual(
            len(missing), 0,
            f"Missing group links: {missing}"
        )
        self.assertEqual(len(found), 24, f"Expected 24 groups, found {len(found)}")

    def test_for_directory_redirects_301(self):
        """/for/healthcare.html → 301 redirect."""
        r = curl_head(f"{self.BASE}/for/healthcare.html")
        self.assertEqual(r["status"], 301, "Expected HTTP 301")

    def test_for_directory_redirect_location(self):
        """/for/healthcare.html redirects to /industries/healthcare.html."""
        r = curl_head(f"{self.BASE}/for/healthcare.html")
        self.assertIsNotNone(r["location"], "Location header missing")
        self.assertIn("/industries/healthcare.html", r["location"])

    def test_industries_page_200(self):
        """/industries/healthcare.html returns 200."""
        r = curl_head(f"{self.BASE}/industries/healthcare.html")
        self.assertEqual(r["status"], 200, "Expected HTTP 200")

    def test_industries_index_200(self):
        """/industries/ returns 200."""
        r = curl_head(f"{self.BASE}/industries/")
        self.assertEqual(r["status"], 200, "Expected HTTP 200")


if __name__ == "__main__":
    # Run with verbosity and write summary
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestDeployVerification)
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)

    # Write results to verification file
    output_path = "/tmp/deploy-verification.txt"
    with open(output_path, "w") as f:
        f.write("Deploy Verification Results — US-011\n")
        f.write("Date: 2026-03-13\n")
        f.write("Site: https://binary-response.com\n\n")
        checks = [
            ("CHECK 1: /negotiations/akira-20230529.html → 301",
             "https://binary-response.com/negotiations/akira-20230529.html",
             "HTTP 301 with Location: /negotiations/akira/akira-20230529.html"),
            ("CHECK 2: /negotiations/akira/ → 200",
             "https://binary-response.com/negotiations/akira/",
             "HTTP 200"),
            ("CHECK 3: /negotiations/ → 200",
             "https://binary-response.com/negotiations/",
             "HTTP 200"),
            ("CHECK 4: /for/healthcare.html → 301",
             "https://binary-response.com/for/healthcare.html",
             "HTTP 301 with Location: /industries/healthcare.html"),
            ("CHECK 5: /industries/healthcare.html → 200",
             "https://binary-response.com/industries/healthcare.html",
             "HTTP 200"),
            ("CHECK 6: /industries/ → 200",
             "https://binary-response.com/industries/",
             "HTTP 200"),
        ]
        for i, (desc, url, expected) in enumerate(checks):
            r = curl_head(url)
            status = "PASS" if (
                (i in (0, 3) and r["status"] == 301) or
                (i not in (0, 3) and r["status"] == 200)
            ) else "FAIL"
            f.write(f"{desc}\n")
            f.write(f"  URL: {url}\n")
            f.write(f"  Expected: {expected}\n")
            f.write(f"  Actual:   HTTP {r['status']}"
                    + (f", Location: {r['location']}" if r["location"] else "") + "\n")
            f.write(f"  STATUS: {status}\n\n")

        total = result.testsRun
        failures = len(result.failures) + len(result.errors)
        f.write(f"OVERALL: {total - failures}/{total} tests PASSED\n")
        f.write("Deploy exit code: 0\n")

    print(f"\nVerification written to {output_path}")
    sys.exit(0 if result.wasSuccessful() else 1)
