"""Positive controls for the nothing-up-my-sleeve experiment: plant a famous-value hit in each of the three paths
(direct substring, secp-core hash, K-163 hash) and confirm the runner recovers it, and check the math-constant
expansion against known hex digits. A null result from the experiment is only trustworthy if these pass.

Run:  python3 -m unittest discover -s tests
"""
import hashlib
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from decimal import Decimal, getcontext, localcontext
from pathlib import Path
from unittest.mock import Mock, patch

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

    def test_precision_is_local_and_expansion_is_stable(self):
        precision = getcontext().prec
        direct, candidates = nums.build_corpus()
        self.assertEqual(getcontext().prec, precision)
        with localcontext() as context:
            context.prec = 12
            self.assertEqual(nums.build_corpus(), (direct, candidates))
            self.assertEqual(context.prec, 12)
        self.assertTrue(dict(direct)["frac_hex(pi)"].startswith(
            "243f6a8885a308d313198a2e03707344a4093822299f31d0"))


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

    def test_identity_is_excluded_but_other_source_is_not(self):
        target = f"{core.CORE:037x}"
        hits = nums.run_direct([("secp_core", target), ("independent", target)])
        self.assertEqual([h["source"] for h in hits], ["independent"])

    def test_planted_k163_substring_is_found(self):
        hits = nums.run_direct([("planted", "abcd" + k163.TARGET.hex() + "abcd")])
        self.assertTrue(any(h["target"] == "k163(128)" and h["offset_hexdigits"] == 4 for h in hits))

    def test_reversed_hex_is_not_byte_reversal(self):
        target = k163.TARGET.hex()
        hits = nums.run_direct([("byte-reversed", bytes.fromhex(target)[::-1].hex()),
                                ("character-reversed", target[::-1])])
        self.assertEqual([(h["source"], h["reading"], h["target"]) for h in hits],
                         [("character-reversed", "reversed-hex", "k163(128)")])


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
        core_result, _ = nums.run_hash([("decoy", b"x"), ("control", control)])
        self.assertTrue(any(h["label"] == "control" and h["algorithm"] == "sha1"
                            for h in core_result["hits"]))

    def test_planted_k163_hash_is_found(self):
        control = b"another famous value"
        digest = hashlib.md5(control).digest()
        k163.TARGET = digest
        k163.T_INT = int.from_bytes(digest, "big")
        _, k163_result = nums.run_hash([("decoy", b"y"), ("control", control)])
        self.assertTrue(any(h["label"] == "control" and h["hash"] == "md5"
                            for h in k163_result["hits"]))

    def test_secp_suffix_is_used_but_k163_input_is_unsuffixed(self):
        control = b"suffix control"
        digest = hashlib.sha1(control + b"\x02").digest()
        core.CORE = (int.from_bytes(digest, "big") >> 4) & core.MASK
        spy = Mock(side_effect=lambda b: hashlib.md5(b).digest())
        with patch.dict(k163.HASHES, {"spy": spy}, clear=True):
            core_result, k163_result = nums.run_hash([("control", control)])
        spy.assert_called_once_with(control)
        self.assertTrue(any(h["suffix_hex"] == "02" and h["algorithm"] == "sha1"
                            for h in core_result["hits"]))
        self.assertEqual(k163_result["evaluations"], 1)
        self.assertEqual(k163_result["suffixes_hex"], [""])


class TestCorpusBuilds(unittest.TestCase):
    def test_corpus_is_nonempty_and_well_formed(self):
        direct, hash_cands = nums.build_corpus()
        self.assertGreater(len(direct), 10)
        self.assertGreater(len(hash_cands), 20)
        for label, h in direct:
            self.assertRegex(h.lower(), r"^[0-9a-f]+$")
        for label, b in hash_cands:
            self.assertIsInstance(b, bytes)

    def test_md5_iv_word_and_little_endian_encodings_are_distinct(self):
        words = bytes.fromhex(nums.STANDARDS_HEX["md5_iv"])
        self.assertEqual(words.hex(), "67452301efcdab8998badcfe10325476")
        little_endian = b"".join(words[i:i+4][::-1] for i in range(0, 16, 4))
        self.assertEqual(little_endian.hex(), nums.STANDARDS_HEX["md5_iv_le"])
        self.assertNotEqual(words, little_endian)

    def test_manifest_reports_actual_evaluations_and_scope(self):
        with tempfile.TemporaryDirectory() as directory, \
             patch.object(sys, "argv", ["nothing_up_my_sleeve.py", "--output-dir", directory]), \
             redirect_stdout(io.StringIO()):
            self.assertEqual(nums.main(), 0)
            result = json.loads(Path(directory, "nothing-up-my-sleeve.json").read_text(encoding="utf-8"))
            text = Path(directory, "nothing-up-my-sleeve.txt").read_text(encoding="utf-8")
        self.assertEqual(result["direct_sources"], 20)
        self.assertEqual(result["hash_candidates"], 66)
        self.assertEqual(result["core_hash_evaluations"], 4290)
        self.assertEqual(result["k163_hash_evaluations"], 594)
        secp = result["core_search"]
        binary = result["k163_search"]
        self.assertEqual(secp["evaluations"], 66 * len(secp["algorithms"]) * len(secp["suffixes_hex"]))
        self.assertEqual(binary["evaluations"], 66 * len(binary["algorithms"]))
        self.assertEqual(secp["candidate_count"], 66)
        self.assertEqual(binary["candidate_count"], 66)
        self.assertEqual(secp["core_bit_range"], [4, 151])
        self.assertEqual(secp["readings"], ["d", "rev", "wswap"])
        self.assertEqual(binary["suffixes_hex"], [""])
        self.assertEqual(secp["input_sequence_sha256"], binary["input_sequence_sha256"])
        self.assertEqual(len(result["source_sha256"]), 4)
        self.assertIn("4290 evaluations", text)
        self.assertIn("594 evaluations", text)
        self.assertIn("unsuffixed only", text)


if __name__ == "__main__":
    unittest.main()
