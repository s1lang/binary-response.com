#!/usr/bin/env python3
"""
Tests for generate-negotiations-mapping.py grouping logic.

Run with: python3 -m pytest scripts/test_generate_negotiations_mapping.py -v
      or: python3 scripts/test_generate_negotiations_mapping.py (unittest)
"""

import importlib.util
import json
import sys
import unittest
from pathlib import Path


def _import_script():
    """Import the hyphen-named script using importlib."""
    script_path = Path(__file__).parent / "generate-negotiations-mapping.py"
    spec = importlib.util.spec_from_file_location("generate_negotiations_mapping", script_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_mod = _import_script()
get_group = _mod.get_group
generate_mapping = _mod.generate_mapping


class TestGetGroup(unittest.TestCase):

    # --- Rule 1: lockbit3-0 prefix ---
    def test_lockbit3_0_prefix(self):
        self.assertEqual(get_group("lockbit3-0-entrust-com.html"), "lockbit3-0")

    def test_lockbit3_0_with_domain(self):
        self.assertEqual(get_group("lockbit3-0-royalmailgroup-com.html"), "lockbit3-0")

    def test_lockbit3_0_with_number(self):
        self.assertEqual(get_group("lockbit3-0-149576.html"), "lockbit3-0")

    # --- Rule 2: royal-mail special case ---
    def test_royal_mail_lockbit_3(self):
        self.assertEqual(get_group("royal-mail-lockbit-3.html"), "lockbit3-0")

    # --- Rule 3: dragonforce prefix ---
    def test_dragonforce_uuid(self):
        self.assertEqual(
            get_group("dragonforce-058f4b92-ae99-45c7-bf35-5d2d6754b3de.html"),
            "dragonforce",
        )

    def test_dragonforce_hex(self):
        self.assertEqual(get_group("dragonforce-29bbe03074fdbb8d.html"), "dragonforce")

    # --- Rule 4: trinity prefix ---
    def test_trinity_numbered(self):
        self.assertEqual(get_group("trinity-0001.html"), "trinity")

    def test_trinity_large_number(self):
        self.assertEqual(get_group("trinity-0014.html"), "trinity")

    # --- Rule 5: hunters-international prefix ---
    def test_hunters_international(self):
        self.assertEqual(
            get_group("hunters-international-20240510.html"), "hunters-international"
        )

    # --- Rule 6: General YYYYMMDD extraction ---
    def test_standard_date_format(self):
        self.assertEqual(get_group("akira-20230529.html"), "akira")

    def test_b_suffix_date(self):
        """akira-20250425b.html → 'akira'"""
        self.assertEqual(get_group("akira-20250425b.html"), "akira")

    def test_numeric_suffix_variant(self):
        """-2 variant: avaddon-20210518-2.html → 'avaddon'"""
        self.assertEqual(get_group("avaddon-20210518-2.html"), "avaddon")

    def test_numeric_suffix_variant_3(self):
        """-3 variant: avaddon-20210518-3.html → 'avaddon'"""
        self.assertEqual(get_group("avaddon-20210518-3.html"), "avaddon")

    def test_letter_suffix_variant(self):
        """conti-20210517-b.html → 'conti'"""
        self.assertEqual(get_group("conti-20210517-b.html"), "conti")

    def test_long_id_after_date(self):
        """qilin-20250203-from-rakeshkrish12.html → 'qilin'"""
        self.assertEqual(get_group("qilin-20250203-from-rakeshkrish12.html"), "qilin")

    def test_cloak_variant(self):
        """cloak-20230802-2.html → 'cloak'"""
        self.assertEqual(get_group("cloak-20230802-2.html"), "cloak")

    def test_mount_locker(self):
        """multi-word group: mount-locker-20201016.html → 'mount-locker'"""
        self.assertEqual(get_group("mount-locker-20201016.html"), "mount-locker")

    def test_blackbasta(self):
        self.assertEqual(get_group("blackbasta-20221011.html"), "blackbasta")

    def test_blackmatter(self):
        self.assertEqual(get_group("blackmatter-20210829.html"), "blackmatter")

    def test_ransomhub(self):
        self.assertEqual(get_group("ransomhub-20240810.html"), "ransomhub")

    def test_revil(self):
        self.assertEqual(get_group("revil-20201014.html"), "revil")

    def test_runsomewares(self):
        self.assertEqual(get_group("runsomewares-20250411.html"), "runsomewares")

    def test_noescape(self):
        self.assertEqual(get_group("noescape-20230911.html"), "noescape")

    def test_fog(self):
        self.assertEqual(get_group("fog-20240517.html"), "fog")

    def test_mallox(self):
        self.assertEqual(get_group("mallox-20230427.html"), "mallox")

    def test_pear(self):
        self.assertEqual(get_group("pear-20250720.html"), "pear")

    def test_hive(self):
        self.assertEqual(get_group("hive-20211004.html"), "hive")

    def test_darkside(self):
        self.assertEqual(get_group("darkside-20200811.html"), "darkside")


class TestGenerateMapping(unittest.TestCase):
    """Integration tests against the actual site."""

    @classmethod
    def setUpClass(cls):
        script_dir = Path(__file__).resolve().parent
        cls.site_root = script_dir.parent
        cls.negotiations_dir = cls.site_root / "negotiations"

    def test_negotiations_dir_exists(self):
        self.assertTrue(self.negotiations_dir.is_dir())

    def test_mapping_total_count(self):
        mapping = generate_mapping(self.site_root)
        total = sum(len(v) for v in mapping.values())
        self.assertEqual(total, 235, f"Expected 235 files, got {total}")

    def test_mapping_group_count(self):
        mapping = generate_mapping(self.site_root)
        self.assertEqual(len(mapping), 24, f"Expected 24 groups, got {len(mapping)}")

    def test_mapping_expected_groups(self):
        mapping = generate_mapping(self.site_root)
        expected = {
            "akira", "avaddon", "avos", "babuk", "blackbasta", "blackmatter",
            "cloak", "conti", "darkside", "dragonforce", "fog", "hive",
            "hunters-international", "lockbit3-0", "mallox", "mount-locker",
            "noescape", "pear", "qilin", "ransomhub", "ranzy", "revil",
            "runsomewares", "trinity",
        }
        self.assertEqual(set(mapping.keys()), expected)

    def test_royal_mail_in_lockbit3_0(self):
        mapping = generate_mapping(self.site_root)
        self.assertIn("royal-mail-lockbit-3.html", mapping.get("lockbit3-0", []))

    def test_index_html_excluded(self):
        mapping = generate_mapping(self.site_root)
        all_files = [f for files in mapping.values() for f in files]
        self.assertNotIn("index.html", all_files)

    def test_no_file_duplicated(self):
        mapping = generate_mapping(self.site_root)
        all_files = [f for files in mapping.values() for f in files]
        self.assertEqual(len(all_files), len(set(all_files)), "Duplicate files in mapping")


if __name__ == "__main__":
    unittest.main(verbosity=2)
