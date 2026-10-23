"""Positive controls for scripts/sectk_2020_checks.py (the replication of Dan's
June 2020 sect*k1 searches). Every search entry point must recover a planted or
known answer before its negatives are trusted."""
import os
import random
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import binpts  # noqa: E402
import sectk_2020_checks as s2020  # noqa: E402


class FieldInverse(unittest.TestCase):
    def test_eea_inverse_matches_fermat_on_two_fields(self):
        rng = random.Random(163233)
        for name in ("sect163k1", "sect233k1"):
            d = s2020.SECTK[name]
            poly = binpts.poly_from(d["m"], d["taps"])
            for _ in range(20):
                a = rng.randrange(1, 1 << d["m"])
                inv = s2020.gf_inv_eea(a, poly, d["m"])
                self.assertEqual(inv, binpts.gf_inv(a, poly, d["m"]))
                self.assertEqual(binpts.gf_mul(a, inv, poly, d["m"]), 1)
        with self.assertRaises(ZeroDivisionError):
            s2020.gf_inv_eea(0, poly, d["m"])


class GridSearch(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        s2020.install_fast_inverse()
        cls.k163 = s2020.Sect("sect163k1", s2020.SECTK["sect163k1"])
        cls.k233 = s2020.Sect("sect233k1", s2020.SECTK["sect233k1"])

    def test_frobenius_eigenvalue_and_cofactor_group(self):
        for c in (self.k163, self.k233):
            self.assertEqual(c.C.mul(c.lam, c.G), c.frob(c.G, 1))
            self.assertEqual(len(c.cofactor_group), c.h)

    def test_recorded_2020_minima_are_reproduced(self):
        for c in (self.k163, self.k233):
            bits, k, j, xhex = s2020.RECORDED_2020[c.name]
            got_bits, got_x = c.coset_x_bits(c.grid_point(k, j))
            self.assertEqual((got_bits, got_x), (bits, int(xhex, 16)))

    def test_planted_short_x_is_found_on_the_grid(self):
        # Plant: pick (k, j), take the point the 2020 search would examine there, and
        # check that the grid evaluation at (k, j) returns that point's coset minimum,
        # which the real search would then report if it were the shortest.
        c = self.k163
        rng = random.Random(2020)
        k, j = rng.randrange(c.m), rng.randrange(1, c.m)
        P = c.grid_point(k, j)
        expect = min((c.C.add(P, T)[0].bit_length(), c.C.add(P, T)[0]) for T in c.cofactor_group)
        self.assertEqual(c.coset_x_bits(P), expect)
        # and the half-generator (k = 0, j = 1) is the published 126-bit value
        self.assertEqual(c.coset_x_bits(c.grid_point(0, 1)),
                         (126, 0x23e21d6019e1211f6bd47ec180256e97))

    def test_full_grid_finds_the_known_minimum_in_a_slice(self):
        # The --full job's search function, on the j-slice 0..3 of sect163k1, must
        # return the 126-bit half-generator at (k=0, j=1) as its minimum.
        c = self.k163
        calls = []
        best = s2020.full_grid(c, js=range(4), progress=lambda d, t, e: calls.append((d, t)))
        self.assertEqual(best, (126, 0x23e21d6019e1211f6bd47ec180256e97, 0, 1))
        self.assertEqual(calls, [(1, 4), (2, 4), (3, 4), (4, 4)])


class EndomorphismHypothesis(unittest.TestCase):
    def test_planted_generator_of_the_form_P_plus_frobenius_P_is_inverted(self):
        s2020.install_fast_inverse()
        d = s2020.SECTK["sect163k1"]
        base = s2020.Sect("sect163k1", d)
        rng = random.Random(7)
        r = rng.randrange(2, base.n)
        P0 = base.C.mul(r, base.G)
        Gp = base.C.add(P0, base.frob(P0, 1))          # a generator built as P + sigma(P)
        c = s2020.Sect("sect163k1", d, G=Gp)
        P = c.C.mul(pow(1 + c.lam, -1, c.n), c.G)      # what the check computes
        self.assertEqual(P, P0)
        self.assertEqual(c.C.add(P, c.frob(P, 1)), Gp)


if __name__ == "__main__":
    unittest.main()
