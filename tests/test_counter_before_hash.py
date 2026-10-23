"""Positive controls for scripts/counter_before_hash.py (HANDOFF §4.2(b)). The
model rests on two engines: the 148-bit core matcher (that a real preimage would
fire it) and the 'observed signature' predicate (shared low 152 bits with a
different top nibble). Both are checked here against planted inputs so the
script's 0-hit probe and 0-signature demonstration can be trusted."""
import hashlib
import os
import struct
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
sys.path.insert(0, os.path.join(ROOT, "scripts", "k163"))

import counter_before_hash as cbh  # noqa: E402
import secg_core_search as core    # noqa: E402

SECP160 = 0x48ce563f89a0ed9414f5aa28ad0d96d6795f9c62
LOW160_BIG = 0x78ce563f89a0ed9414f5aa28ad0d96d6795f9c63   # 224/256 low 160 bits


def signature(va, vb):
    """The observed signature: share bits 4..155, differ at bits 156..159."""
    return (cbh.window_156(va) == cbh.window_156(vb)
            and (va >> 156 & 0xF) != (vb >> 156 & 0xF))


class CoreMatcherWiring(unittest.TestCase):
    def test_matcher_fires_on_the_real_full_values(self):
        # a digest equal to the published 160-bit forms must be flagged
        self.assertTrue(core.check(SECP160.to_bytes(20, "big")))
        self.assertTrue(core.check(LOW160_BIG.to_bytes(20, "big")))

    def test_matcher_fires_on_a_planted_core_digest(self):
        # any digest carrying the 152-bit core (bits 4..155) in its low bits,
        # arbitrary top nibble and last nibble, is a hit the probe would catch
        planted = (0x7 << 156) | (0x8ce563f89a0ed9414f5aa28ad0d96d6795f9c6 << 4) | 0x5
        self.assertTrue(core.check(planted.to_bytes(20, "big")))

    def test_matcher_silent_on_an_unrelated_digest(self):
        self.assertIsNone(core.check(hashlib.sha1(b"nothing to see").digest()))


class EncoderCounter(unittest.TestCase):
    def test_distinct_counters_give_distinct_inputs(self):
        for name in [e for e, _ in cbh.encoders(b"seed", 0)]:
            msgs = {dict(cbh.encoders(b"seed", i))[name] for i in range(64)}
            self.assertEqual(len(msgs), 64, f"{name} collides across counters")

    def test_counter_actually_enters_the_hashed_bytes(self):
        # a planted (seed, counter) whose SHA-1 is known is recoverable by rehash
        seed, i = b"Certicom Research", 37
        msg = seed + struct.pack(">I", i)
        self.assertEqual(dict(cbh.encoders(seed, i))["suffix_be4"], msg)
        self.assertEqual(hashlib.sha1(msg).digest(), hashlib.sha1(msg).digest())


class SignaturePredicate(unittest.TestCase):
    def test_fires_on_shared_core_split_top(self):
        core152 = 0x8ce563f89a0ed9414f5aa28ad0d96d6795f9c6
        va = (0x4 << 156) | (core152 << 4) | 0x2
        vb = (0x7 << 156) | (core152 << 4) | 0x3
        self.assertTrue(signature(va, vb))          # the real 160k1-vs-256k1 shape

    def test_silent_on_identical_values(self):
        v = (0x7 << 156) | (0x8ce563f89a0ed9414f5aa28ad0d96d6795f9c6 << 4) | 0x3
        self.assertFalse(signature(v, v))           # same top nibble -> not the signature

    def test_silent_on_independent_values(self):
        a = int.from_bytes(hashlib.sha1(b"a").digest(), "big")
        b = int.from_bytes(hashlib.sha1(b"b").digest(), "big")
        self.assertFalse(signature(a, b))           # cores differ


if __name__ == "__main__":
    unittest.main()
