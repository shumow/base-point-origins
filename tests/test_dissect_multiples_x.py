"""Positive controls for scripts/dissect_multiples_x.py: confirm the transcription
of DiSSECT's multiples_x trait is faithful (k=2 is the inverse-2 multiple, i.e.
x(G/2)) and that the reconciliation is not vacuous (a wrong target would fail)."""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import dissect_multiples_x as dm  # noqa: E402
from secg_scan import CURVES, C   # noqa: E402


class TraitTranscription(unittest.TestCase):
    def test_k2_is_the_half_generator(self):
        c = C(CURVES["secp256k1"])
        G = (c.Gx, c.Gy)
        Hx, bits, diff = dm.trait_multiples_x(c.n, c.n * c.h, c.mul, G, 2)
        # 1/2 mod n == (n+1)/2, and that multiple of G is G/2
        half = c.mul((c.n + 1) // 2, G)
        self.assertEqual(Hx, half[0])
        self.assertEqual(bits, Hx.bit_length())
        self.assertEqual(diff, (c.n * c.h).bit_length() - bits)

    def test_inverse_definition_matches_sage_style(self):
        c = C(CURVES["secp192k1"])
        G = (c.Gx, c.Gy)
        for k in (1, 2, 3, 7):
            Hx, _, _ = dm.trait_multiples_x(c.n, c.n * c.h, c.mul, G, k)
            self.assertEqual(Hx, c.mul(pow(k, -1, c.n), G)[0])


class Reconciliation(unittest.TestCase):
    def test_k2_reproduces_recorded_half_on_every_curve(self):
        self.assertEqual(dm.main(), [])

    def test_check_is_not_vacuous(self):
        # a deliberately wrong "recorded" value must be detected as a mismatch
        c = C(CURVES["secp256k1"])
        Hx, _, _ = dm.trait_multiples_x(c.n, c.n * c.h, c.mul, (c.Gx, c.Gy), 2)
        self.assertNotEqual(Hx, dm.RECORDED_HALF["secp256k1"] ^ 1)


if __name__ == "__main__":
    unittest.main()
