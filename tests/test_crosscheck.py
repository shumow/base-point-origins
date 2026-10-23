"""Positive controls for scripts/crosscheck_stdcurves.py. A clean cross-check is
only meaningful if the comparator actually flags disagreements, so these controls
plant a mismatch and confirm it is caught, check coverage, and confirm the real
cross-check passes."""
import json
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import crosscheck_stdcurves as cc  # noqa: E402
from secg_scan import CURVES       # noqa: E402
import sectk_2020_checks as s2020  # noqa: E402


class ComparatorDetectsMismatch(unittest.TestCase):
    def test_compare_flags_a_planted_disagreement(self):
        bad = cc.compare("planted", [("Gx", 0x1234, 0x1234), ("Gy", 0xAAAA, 0xBBBB)])
        self.assertEqual([m[0] for m in bad], ["Gy"])

    def test_compare_passes_when_equal(self):
        self.assertEqual(cc.compare("ok", [("p", 7, 7), ("n", 11, 11)]), [])


class Coverage(unittest.TestCase):
    def test_std_source_covers_every_repo_curve(self):
        by_name, by_alias = cc.load_std()
        for name in CURVES:
            self.assertIn(name, by_name, f"{name} missing from std-curves")
        for name in s2020.SECTK:
            self.assertIn(name, by_name, f"{name} missing from std-curves")
        for nist in ("K-163", "B-571"):
            self.assertIn(f"nist/{nist}".lower(), by_alias)

    def test_binary_poly_bitmask_roundtrips(self):
        by_name, _ = cc.load_std()
        from binpts import poly_from
        v = s2020.SECTK["sect163k1"]
        self.assertEqual(poly_from(v["m"], v["taps"]), cc.std_poly_int(by_name["sect163k1"]))


class RealCrossCheckPasses(unittest.TestCase):
    def test_every_field_agrees(self):
        self.assertEqual(cc.main(), [])


if __name__ == "__main__":
    unittest.main()
