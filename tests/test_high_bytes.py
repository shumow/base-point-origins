"""Positive controls for scripts/high_bytes_analysis.py (HANDOFF §4.2, the
characterization of the secp*k1 top byte and the 192k1 prefix). The analysis
makes structural claims and runs exclusion tests; these controls check that its
helpers compute what they say and that its decomposition is invertible, so the
exclusions it reports can be trusted."""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import high_bytes_analysis as hb  # noqa: E402
from secg_scan import CURVES, C   # noqa: E402

PUBLISHED = {
    "secp160k1": 0x48ce563f89a0ed9414f5aa28ad0d96d6795f9c62,
    "secp192k1": 0x554123b78ce563f89a0ed9414f5aa28ad0d96d6795f9c66,
    "secp224k1": 0x3b78ce563f89a0ed9414f5aa28ad0d96d6795f9c63,
    "secp256k1": 0x3b78ce563f89a0ed9414f5aa28ad0d96d6795f9c63,
}


class HalfGenerator(unittest.TestCase):
    def test_half_x_recovers_the_published_constants(self):
        for name, want in PUBLISHED.items():
            self.assertEqual(hb.half_x(C(CURVES[name])), want)


class IsXHelper(unittest.TestCase):
    def test_true_on_a_known_point_false_on_a_planted_nonresidue(self):
        for name in PUBLISHED:
            c = C(CURVES[name])
            # the published generator's x lifts by construction
            self.assertTrue(hb.is_x(c, c.Gx))
            # find an x that is provably not a coordinate and confirm is_x says so
            misses = [x for x in range(c.Gx + 1, c.Gx + 400) if not hb.is_x(c, x)]
            self.assertTrue(misses, "expected some non-lifting x in a short window")
            for x in misses[:5]:
                rhs = (x ** 3 + c.a * x + c.b) % c.p
                self.assertNotEqual(pow(rhs, (c.p - 1) // 2, c.p), 1)
                self.assertNotEqual(rhs, 0)

    def test_out_of_range_is_rejected(self):
        c = C(CURVES["secp256k1"])
        self.assertFalse(hb.is_x(c, -1))
        self.assertFalse(hb.is_x(c, c.p))


class Decomposition(unittest.TestCase):
    """The core / top-byte / high / last-nibble split must be invertible, or the
    'what varies' claims are meaningless."""

    def test_split_and_reassemble_is_identity(self):
        for name, x in PUBLISHED.items():
            low160 = x & ((1 << 160) - 1)
            high = x >> 160
            topbyte = (low160 >> 152) & 0xFF
            mid = low160 & ~(0xFF << 152)           # bits 0..151
            rebuilt = (high << 160) | (topbyte << 152) | mid
            self.assertEqual(rebuilt, x)

    def test_shared_core_and_shared_V(self):
        core, V = set(), set()
        for x in PUBLISHED.values():
            low160 = x & ((1 << 160) - 1)
            core.add((low160 >> 4) & ((1 << 152) - 1))
            V.add((low160 & ~(0xFF << 152) & ~0xF) | (0x78 << 152))
        self.assertEqual(len(core), 1, "the 152-bit core must be shared")
        self.assertEqual(len(V), 1, "the normalised 160-bit block V must be shared")
        self.assertEqual(core.pop(), 0x8ce563f89a0ed9414f5aa28ad0d96d6795f9c6)

    def test_224_and_256_are_byte_identical(self):
        self.assertEqual(PUBLISHED["secp224k1"], PUBLISHED["secp256k1"])


class ExclusionLogic(unittest.TestCase):
    def test_fips_single_seed_contradiction_is_real(self):
        """Low 64 bits always determine low 32 bits; the two high fields disagree."""
        high192 = PUBLISHED["secp192k1"] >> 160
        high224 = PUBLISHED["secp224k1"] >> 160
        self.assertEqual(high192 & 0xFFFFFFFF, high192)       # 192 high is < 2^32
        self.assertNotEqual(high224 & 0xFFFFFFFF, high192 & 0xFFFFFFFF)

    def test_192_prefix_exceeds_224_256_over_a_smaller_field(self):
        hi = {n: (x >> 160).bit_length() for n, x in PUBLISHED.items()}
        self.assertGreater(hi["secp192k1"], hi["secp224k1"])
        self.assertGreater(hi["secp192k1"], hi["secp256k1"])


class ObservedReductions(unittest.TestCase):
    def test_planted_nonzero_quotient_is_found(self):
        value = PUBLISHED["secp256k1"]
        p = CURVES["secp160k1"]["p"]
        xs = {"secp256k1": value, "secp160k1": value % p}
        self.assertIn(dict(source="secp256k1", reading="full", target="secp160k1",
                           quotient=value // p), hb.observed_reductions(xs))
        self.assertGreater(value // p, 0)

    def test_low160_reading_is_actually_tested(self):
        value = PUBLISHED["secp192k1"]
        low160 = value & ((1 << 160) - 1)
        xs = {"secp192k1": value, "secp160k1": low160}
        self.assertIn(dict(source="secp192k1", reading="low160", target="secp160k1",
                           quotient=0), hb.observed_reductions(xs))
        self.assertNotIn(dict(source="secp192k1", reading="full", target="secp160k1",
                              quotient=value // CURVES["secp160k1"]["p"]),
                         hb.observed_reductions(xs))

    def test_unrelated_values_do_not_match(self):
        self.assertEqual(hb.observed_reductions({"secp160k1": 0x1234, "secp256k1": 0x9999}), [])

    def test_real_matches_are_only_the_known_identity(self):
        self.assertEqual(hb.observed_reductions(PUBLISHED), [
            dict(source="secp224k1", reading="full", target="secp256k1", quotient=0),
            dict(source="secp256k1", reading="full", target="secp224k1", quotient=0),
        ])


if __name__ == "__main__":
    unittest.main()
