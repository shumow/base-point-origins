"""Positive controls for the nothing-up-my-sleeve experiment: plant a famous-value hit in each of the three paths
(direct substring, secp-core hash, K-163 hash) and confirm the runner recovers it, and check the math-constant
expansion against known hex digits. A null result from the experiment is only trustworthy if these pass.

Run:  python3 -m unittest discover -s tests
"""
import hashlib
import sys
import unittest
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "k163"))
import nothing_up_my_sleeve as nums
import secg_core_search as core
import search as k163


class TestConstantExpansion(unittest.TestCase):
    """Known hex digits of famous constants -- these are the published nothing-up-my-sleeve numbers."""

    def test_known_fractional_hex(self):
        consts = nums.math_constants()
        self.assertTrue(nums.frac_hex(consts["pi"], 16).startswith("243f6a8885a308d3"))
        self.assertTrue(nums.frac_hex(consts["e"], 16).startswith("b7e151628aed2a6a"))
        self.assertTrue(nums.frac_hex(consts["sqrt2"], 16).startswith("6a09e667f3bcc908"))

    def test_frac_hex_simple(self):
        self.assertEqual(nums.frac_hex(Decimal("0.5"), 4), "8000")
        self.assertEqual(nums.frac_hex(Decimal("0.25"), 4), "4000")


class TestDirectControl(unittest.TestCase):
    def setUp(self):
        self._core = core.CORE

    def tearDown(self):
        core.CORE = self._core

    def test_planted_substring_is_found(self):
        core.CORE = 0x1234567890abcdef1122334455667788990  # a 148-bit stand-in
        core_hex = f"{core.CORE:037x}"
        planted = [("decoy", "deadbeef" * 8),
                   ("fake_constant", "cafe" + core_hex + "babe"),
                   ("other", "00" * 20)]
        hits = nums.run_direct(planted)
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["source"], "fake_constant")
        self.assertEqual(hits[0]["target"], "secp_core(148)")
        self.assertEqual(hits[0]["offset_hexdigits"], 4)

    def test_reversed_reading_is_found(self):
        core.CORE = 0x1234567890abcdef1122334455667788990
        core_hex = f"{core.CORE:037x}"
        planted = [("mirror", ("ff" + core_hex)[::-1])]
        hits = nums.run_direct(planted)
        self.assertTrue(any(h["reading"] == "reversed-hex" and h["target"] == "secp_core(148)" for h in hits))


class TestHashControls(unittest.TestCase):
    def setUp(self):
        self._core_core, self._core_full = core.CORE, dict(core.FULL)
        self._k_target, self._k_tint = k163.TARGET, k163.T_INT

    def tearDown(self):
        core.CORE, core.FULL = self._core_core, self._core_full
        k163.TARGET, k163.T_INT = self._k_target, self._k_tint

    def test_planted_secp_core_hash_is_found(self):
        control = b"a famous value"
        digest = hashlib.sha1(control).digest()
        core.CORE = (int.from_bytes(digest, "big") >> 4) & core.MASK
        core_hits, _, _, _ = nums.run_hash([("decoy", b"x"), ("control", control)])
        self.assertTrue(any(h["label"] == "control" and h["algorithm"] == "sha1" for h in core_hits))

    def test_planted_k163_hash_is_found(self):
        control = b"another famous value"
        digest = hashlib.md5(control).digest()
        k163.TARGET = digest
        k163.T_INT = int.from_bytes(digest, "big")
        _, k163_hits, _, _ = nums.run_hash([("decoy", b"y"), ("control", control)])
        self.assertTrue(any(h["label"] == "control" and h["hash"] == "md5" for h in k163_hits))


class TestCorpusBuilds(unittest.TestCase):
    def test_corpus_is_nonempty_and_well_formed(self):
        direct, hash_cands = nums.build_corpus()
        self.assertGreater(len(direct), 10)
        self.assertGreater(len(hash_cands), 20)
        for label, h in direct:
            self.assertRegex(h.lower(), r"^[0-9a-f]+$")
        for label, b in hash_cands:
            self.assertIsInstance(b, bytes)


if __name__ == "__main__":
    unittest.main()
