"""Positive controls for scripts/seed_two_stage.py (HANDOFF §4.2(b), stage 2
hashing the seed). The script reports an all-negative joint search; these
controls show each arm WOULD surface a planted answer, so the negative holds."""
import hashlib
import os
import struct
import sys
import unittest

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
    def test_counter_inputs_distinct_and_contain_the_counter(self):
        msgs = [list(sts.stage2_inputs(b"seed", i)) for i in range(32)]
        flat = {m for group in msgs for m in group}
        self.assertEqual(len(flat), 32 * 4)                  # 4 placements, all distinct
        self.assertIn(b"seed" + struct.pack(">I", 7), list(sts.stage2_inputs(b"seed", 7)))


class PlantedStage2Limb(unittest.TestCase):
    def test_sweep_recovers_a_planted_seed_counter(self):
        seed, planted_i, hname = b"Certicom Research", 777, "sha1"
        msg = seed + struct.pack(">I", planted_i)           # the "seed||be4" placement
        target = dict(cs.word_readings(sts.H2[hname](msg)))["be_word1"]
        found = None
        for i in range(3000):
            for m in sts.stage2_inputs(seed, i):
                for rname, w in cs.word_readings(sts.H2[hname](m)):
                    if w == target and rname == "be_word1" and m == seed + struct.pack(">I", i):
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


if __name__ == "__main__":
    unittest.main()
