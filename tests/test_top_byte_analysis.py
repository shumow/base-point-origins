"""Controls for experiment 2 (top-byte / high-bit analysis). Known-answer checks on the derived half-x values and the
on-curve test, and a planted reduction relation the item-3d scan must recover. A null conclusion is only trustworthy if
these pass.

Run:  python3 -m unittest discover -s tests
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "k163"))
import top_byte_analysis as tba
from secg_scan import CURVES


# The published half-point x-coordinates (SEC 2); the script must derive exactly these from the curve definitions.
KNOWN_HALF_X = {
    "secp160k1": 0x48ce563f89a0ed9414f5aa28ad0d96d6795f9c62,
    "secp192k1": 0x554123b78ce563f89a0ed9414f5aa28ad0d96d6795f9c66,
    "secp224k1": 0x3b78ce563f89a0ed9414f5aa28ad0d96d6795f9c63,
    "secp256k1": 0x3b78ce563f89a0ed9414f5aa28ad0d96d6795f9c63,
}


class TestDerivedHalves(unittest.TestCase):
    def test_half_x_matches_published(self):
        for name, expected in KNOWN_HALF_X.items():
            self.assertEqual(tba.half_x(name), expected, name)

    def test_core_is_shared(self):
        for name in tba.K1:
            self.assertTrue(tba.decompose(KNOWN_HALF_X[name])["core_matches"], name)

    def test_decomposition_fields(self):
        d = tba.decompose(KNOWN_HALF_X["secp160k1"])
        self.assertEqual(d["byte_above_core_hex"], "48")
        self.assertEqual(d["low_nibble"], 2)
        d2 = tba.decompose(KNOWN_HALF_X["secp224k1"])
        self.assertEqual(d2["prefix_above_core_hex"], "3b78")
        self.assertEqual(d2["byte_above_core_hex"], "78")


class TestOnCurve(unittest.TestCase):
    def test_generators_are_on_curve(self):
        for name in tba.K1:
            self.assertTrue(tba.on_curve_x(CURVES[name]["Gx"], name), name)
            self.assertTrue(tba.on_curve_x(KNOWN_HALF_X[name], name), name)

    def test_known_non_residue_x_is_rejected(self):
        # x = 0 gives y^2 = b; for secp160k1 b = 7 and 7 is a non-residue mod that prime.
        p = CURVES["secp160k1"]["p"]
        self.assertFalse(tba.is_qr(7, p))
        self.assertFalse(tba.on_curve_x(0, "secp160k1"))


class TestReductionControl(unittest.TestCase):
    def test_planted_reduction_is_found(self):
        # Plant: make secp160k1's "half-x" equal secp256k1's value reduced mod the secp160k1 prime.
        p160 = CURVES["secp160k1"]["p"]
        v256 = KNOWN_HALF_X["secp256k1"]
        planted = {"secp256k1": v256, "secp160k1": v256 % p160}
        hits = tba.find_reductions(planted)
        self.assertTrue(any(h["source_reading"] == "secp256k1:full" and h["reduced_mod"] == "secp160k1"
                            for h in hits), hits)

    def test_no_spurious_reduction_on_distinct_values(self):
        # Two unrelated values must not report a reduction match.
        planted = {"secp160k1": 0x1234, "secp256k1": 0x9999}
        self.assertEqual(tba.find_reductions(planted), [])


if __name__ == "__main__":
    unittest.main()
