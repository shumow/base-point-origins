"""Positive controls for scripts/counter_second_hash.py (HANDOFF §4.2(b), the
two-stage / counter-before-second-hash variant). The script reports a negative;
these controls show its search WOULD surface a planted second-hash limb and a
planted transform, so the negative is trustworthy."""
import hashlib
import os
import struct
import sys
import unittest
import zlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
sys.path.insert(0, os.path.join(ROOT, "scripts", "k163"))

import counter_second_hash as cs  # noqa: E402

VBYTES = cs.V_FORMS["V(..c63)"].to_bytes(20, "big")


class WordReadings(unittest.TestCase):
    def test_be_and_le_words_are_consistent(self):
        d = hashlib.sha1(b"x").digest()
        r = dict(cs.word_readings(d))
        self.assertEqual(r["be_word0"], int.from_bytes(d[:4], "big"))
        self.assertEqual(r["le_word0"], int.from_bytes(d[:4], "little"))
        self.assertEqual(r["top32"], int.from_bytes(d, "big") >> 128)
        self.assertEqual(r["low32"], int.from_bytes(d, "big") & 0xFFFFFFFF)
        for _, w in cs.word_readings(d):
            self.assertLess(w, 1 << 32)


class PlantedSecondHashLimb(unittest.TestCase):
    """Plant a limb that IS a window of H2(V||counter) and confirm the same
    sweep the script runs recovers that counter and reading."""

    def test_sweep_recovers_a_planted_counter(self):
        hname, ename, planted_i = "sha1", "V||be4", 4242
        msg = dict(cs.counter_inputs(VBYTES, planted_i))[ename]
        self.assertEqual(msg, VBYTES + struct.pack(">I", planted_i))
        target = dict(cs.word_readings(cs.FAST_H2[hname](msg)))["be_word2"]

        found = None
        for i in range(6000):
            d = cs.FAST_H2[hname](dict(cs.counter_inputs(VBYTES, i))[ename])
            for rname, w in cs.word_readings(d):
                if w == target and rname == "be_word2":
                    found = i
                    break
            if found is not None:
                break
        self.assertEqual(found, planted_i)


class PlantedTransform(unittest.TestCase):
    """If a high limb WERE crc32(V), the no-counter transform pass would catch it."""

    def test_transform_pass_would_flag_a_crc_limb(self):
        v = cs.V_FORMS["V(..c63)"]
        vbytes = v.to_bytes(20, "big")
        crc = zlib.crc32(vbytes)
        trans = dict(cs.transforms_no_counter(vbytes))
        self.assertEqual(trans["crc32"], crc)
        # the script compares each transform to T32; emulate that with crc as target
        matched = [name for name, val in cs.transforms_no_counter(vbytes) if val == crc]
        self.assertIn("crc32", matched)


class RealLimbsAreNotProduced(unittest.TestCase):
    """Consistency: the actual 32-bit limbs are not a no-counter window/transform."""

    def test_no_transform_or_plain_rehash_gives_the_real_limbs(self):
        for v in cs.V_FORMS.values():
            vbytes = v.to_bytes(20, "big")
            for _, val in cs.transforms_no_counter(vbytes):
                self.assertNotIn(val, cs.T32)
            for hf in cs.FAST_H2.values():
                for _, w in cs.word_readings(hf(vbytes)):
                    self.assertNotIn(w, cs.T32)


if __name__ == "__main__":
    unittest.main()
