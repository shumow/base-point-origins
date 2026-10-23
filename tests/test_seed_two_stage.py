"""Positive controls for scripts/seed_two_stage.py (HANDOFF §4.2(b), stage 2
hashing the seed). The script reports an all-negative joint search; these
controls show each arm WOULD surface a planted answer, and that a planted joint
hit driven through the production entry point `main` comes back as a byte-exact
witness (seed bytes, both stages' construction), so the negative holds and a
positive would be reproducible."""
import hashlib
import os
import struct
import sys
import unittest
from unittest.mock import patch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
sys.path.insert(0, os.path.join(ROOT, "scripts", "k163"))

import seed_two_stage as sts  # noqa: E402
import counter_second_hash as cs  # noqa: E402
import secg_core_search as core  # noqa: E402


class Windows(unittest.TestCase):
    def test_windows_cover_every_offset_and_recover_a_planted_slice(self):
        d = hashlib.sha256(b"abc").digest()
        dint = int.from_bytes(d, "big")
        width, off = 166, 40
        planted = (dint >> off) & ((1 << width) - 1)
        got = {o: w for o, w in sts.windows(dint, 256, width)}
        self.assertEqual(got[off], planted)
        self.assertEqual(len(got), 256 - width + 1)          # every bit offset present
        for _, w in sts.windows(dint, 256, width):
            self.assertLess(w, 1 << width)


class Stage2Encoders(unittest.TestCase):
    def test_counter_inputs_distinct_named_and_contain_the_counter(self):
        msgs = [[m for _, m in sts.stage2_inputs(b"seed", i)] for i in range(32)]
        flat = {m for group in msgs for m in group}
        self.assertEqual(len(flat), 32 * 4)                  # 4 placements, all distinct
        named = dict(sts.stage2_inputs(b"seed", 7))
        self.assertEqual(named["seed||be4"], b"seed" + struct.pack(">I", 7))
        self.assertEqual(named["be4||seed"], struct.pack(">I", 7) + b"seed")


class PlantedStage2Limb(unittest.TestCase):
    def test_sweep_recovers_a_planted_seed_counter(self):
        seed, planted_i, hname = b"Certicom Research", 777, "sha1"
        msg = seed + struct.pack(">I", planted_i)           # the "seed||be4" placement
        target = dict(cs.word_readings(sts.H2[hname](msg)))["be_word1"]
        found = None
        for i in range(3000):
            for pname, m in sts.stage2_inputs(seed, i):
                for rname, w in cs.word_readings(sts.H2[hname](m)):
                    if w == target and rname == "be_word1" and pname == "seed||be4":
                        found = i
            if found is not None:
                break
        self.assertEqual(found, planted_i)


class Stage1MatcherFires(unittest.TestCase):
    def test_core_matcher_fires_on_the_real_V(self):
        # stage 1 reuses core.check; confirm it recognises V's low-160 forms
        self.assertTrue(core.check((0x78ce563f89a0ed9414f5aa28ad0d96d6795f9c63).to_bytes(20, "big")))
        self.assertIsNone(core.check(hashlib.sha1(b"not a seed").digest()))


class CandidateSeeds(unittest.TestCase):
    def test_corpus_includes_wordlist_and_curve_params(self):
        labels = {lab for lab, _ in sts.candidate_seeds()}
        self.assertIn("wl", labels)
        self.assertIn("secp256k1.p", labels)
        self.assertIn("secp192k1.n_dec", labels)


class PlantedJointThroughMain(unittest.TestCase):
    """Drive the production entry point with a seed planted to clear both stages:
    stage 1 by making the core matcher fire on SHA-1(seed) (the real matcher's
    target is the published core, which no short string hits), stage 2 by adding
    a 32-bit window of SHA-1(seed||be4(7)) to the high-limb targets. The report
    and the returned witness must name the seed bytes and both constructions."""

    def test_main_returns_a_byte_exact_witness_for_a_planted_joint_hit(self):
        planted_text = "Planted Seed 2026"
        seed = planted_text.encode("ascii")
        d1 = hashlib.sha1(seed).digest()

        def fake_check(d):
            return "sha1 core (planted)" if d == d1 else None

        counter, placement = 7, "seed||be4"
        msg = seed + struct.pack(">I", counter)
        limb = dict(cs.word_readings(hashlib.sha1(msg).digest()))["be_word1"]
        t32 = dict(cs.T32)
        t32[limb] = "planted limb"

        before = len(sts.out_lines)
        with patch.object(sts.core, "check", fake_check), patch.object(sts.cs, "T32", t32):
            res = sts.main(seeds=[("wl", "another word"), ("wl", planted_text)],
                           counter_max=16, encs=("ascii",))
        report = "\n".join(sts.out_lines[before:])

        self.assertEqual(len(res["joint_hits"]), 1)
        j = res["joint_hits"][0]
        self.assertEqual(j["input_hex"], seed.hex())
        self.assertEqual(j["text"], planted_text)
        self.assertEqual(j["enc"], "ascii")
        s1 = [h for h in j["stage1"] if h["hash"] == "sha1" and h["suffix_hex"] == ""]
        self.assertEqual(len(s1), 1)
        self.assertEqual(s1[0]["msg_hex"], seed.hex())
        self.assertEqual(s1[0]["reading"], "sha1 core (planted)")
        s2 = [h for h in j["stage2"] if h["hash"] == "sha1" and h["placement"] == placement
              and h["reading"] == "be_word1" and h["counter"] == counter]
        self.assertEqual(len(s2), 1)
        self.assertEqual(s2[0]["msg_hex"], msg.hex())
        self.assertEqual(s2[0]["limb"], f"{limb:#010x}")
        # the printed report carries the same witness, so stdout alone reproduces it
        self.assertIn(f"JOINT HIT input_hex={seed.hex()}", report)
        self.assertIn(f"counter={counter} msg_hex={msg.hex()}", report)
        # the other candidate is not reported as anything
        self.assertNotIn("another word".encode().hex(), report)
        self.assertEqual(res["stage1_hits"][0]["input_hex"], seed.hex())


if __name__ == "__main__":
    unittest.main()
