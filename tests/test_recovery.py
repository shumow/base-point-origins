"""Positive controls: every search in this repository must recover a planted or known answer.

A negative result ("0 hits") means nothing unless the same code finds the answer when the answer is present. These tests
plant one, through the real search entry points (not reimplementations), and check the hit is reported.

Run:  python3 -m unittest discover -s tests -v        (stdlib only; ~1 minute)
"""
import hashlib, io, os, struct, sys, tempfile, unittest
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts")); sys.path.insert(0, str(ROOT / "scripts" / "k163"))

import secg_core_search as core
import search as k163
import wordlist_search
import freelip_sweep
import nibble_rules
import sha1_steps
from secg_scan import CURVES as SEC_CURVES, C as SecCurve


def plant_core(digest: bytes):
    """Point secg_core_search at the 148-bit core of `digest` (bits 4..151, as the real matcher reads them)."""
    v = int.from_bytes(digest, "big")
    core.CORE = (v >> 4) & core.MASK
    core.FULL = {}


def plant_k163(digest16: bytes):
    k163.TARGET = digest16; k163.T_INT = int.from_bytes(digest16, "big")


def run_main(module, strings):
    """Run a harness's main() over a fixed string list, return printed output."""
    saved = module.all_strings
    module.all_strings = lambda: iter(strings)
    buf = io.StringIO()
    try:
        with redirect_stdout(buf): module.main()
    finally:
        module.all_strings = saved
    return buf.getvalue()


class TestCoreMatcher(unittest.TestCase):
    """secg_core_search: the 148-bit-core matcher and its main loop."""

    def setUp(self):
        self._saved = (core.CORE, core.FULL)

    def tearDown(self):
        core.CORE, core.FULL = self._saved

    def test_published_constants_match_real_core(self):
        # the three published 160-bit forms must satisfy the matcher as shipped
        for v in (0x48ce563f89a0ed9414f5aa28ad0d96d6795f9c62, 0x78ce563f89a0ed9414f5aa28ad0d96d6795f9c63):
            self.assertIsNotNone(core.check(v.to_bytes(20, "big")))
        self.assertIsNone(core.check(hashlib.sha1(b"not it").digest()))

    def test_planted_sha1_found_through_main(self):
        plant_core(hashlib.sha1(b"Certicom").digest())
        out = run_main(core, [("decoy", b"decoy"), ("ascii:'Certicom'", b"Certicom"), ("decoy2", b"other")])
        self.assertIn("HIT ascii:'Certicom' sha1 b''", out)
        self.assertIn("1 hits", out)

    def test_planted_with_counter_suffix_and_sha0(self):
        # a hit that only exists with the X9.62-style counter 2 appended as a byte, under SHA-0
        from hashes import sha0
        plant_core(sha0(b"Waterloo" + bytes([2])))
        out = run_main(core, [("w", b"Waterloo")])
        self.assertIn("HIT w sha0 b'\\x02'", out)

    def test_planted_reversed_reading(self):
        # digest stored byte-reversed: the 'rev' reading must catch it
        d = hashlib.sha1(b"Minghua Qu").digest()
        plant_core(d[::-1])
        self.assertEqual(core.check(d), "rev core")

    def test_top_byte_and_last_nibble_are_ignored(self):
        # the matcher must not care about the per-curve top byte and last nibble
        d = hashlib.sha1(b"SECG").digest()
        plant_core(d)
        v = int.from_bytes(d, "big")
        v2 = (v & ~(0xFF << 152) & ~0xF) | (0x9A << 152) | 0x7
        self.assertIsNotNone(core.check(v2.to_bytes(20, "big")))


class TestK163Matcher(unittest.TestCase):
    def setUp(self):
        self._saved = (k163.TARGET, k163.T_INT)

    def tearDown(self):
        k163.TARGET, k163.T_INT = self._saved

    def test_real_target_is_the_published_half_point(self):
        self.assertEqual(k163.TARGET.hex(), "23e21d6019e1211f6bd47ec180256e97")

    def test_planted_md5_found_through_main(self):
        plant_k163(hashlib.md5(b"sect163k1").digest())
        out = run_main(k163, [("x", b"nope"), ("ascii:'sect163k1'", b"sect163k1")])
        self.assertIn("HIT ascii:'sect163k1' md5 d", out)

    def test_planted_low128_of_sha1(self):
        d = hashlib.sha1(b"K-163").digest()
        plant_k163(d[-16:])
        self.assertEqual(k163.match(d), "d[-16:]")

    def test_planted_masked_top_bits(self):
        d = hashlib.md5(b"Koblitz").digest()
        v = int.from_bytes(d, "big") & ((1 << 126) - 1)          # top two bits cleared, as on the real value
        plant_k163(v.to_bytes(16, "big"))
        self.assertIn("top 2 bits masked", k163.match(d))


class TestWordlistSearch(unittest.TestCase):
    def test_planted_word_with_variant_found(self):
        saved = (core.CORE, core.FULL)
        try:
            plant_core(hashlib.sha1(b"Hayward.").digest())      # only the '.' variant of the word hashes to the core
            with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
                f.write("Mississauga\nHayward\n"); path = f.name
            buf = io.StringIO()
            with redirect_stdout(buf): wordlist_search.main(path)
            os.unlink(path)
            self.assertIn("HIT core 'Hayward.' ascii b'' sha1", buf.getvalue())
        finally:
            core.CORE, core.FULL = saved


class TestMakeTargets(unittest.TestCase):
    def test_every_completion_of_the_core_is_a_target(self):
        import random, subprocess
        with tempfile.TemporaryDirectory() as d:
            subprocess.run([sys.executable, str(ROOT / "scripts" / "make_targets.py"), d], check=True, capture_output=True)
            targets = set(Path(d, "secp_core_sha1.txt").read_text().split())
            self.assertEqual(len(targets), 12288)
            rng = random.Random(1)
            for _ in range(50):
                v = (rng.randrange(256) << 152) | (core.MASK & 0xce563f89a0ed9414f5aa28ad0d96d6795f9c6) << 4 | rng.randrange(16)
                b = v.to_bytes(20, "big")
                self.assertIn(b.hex(), targets)
                self.assertIn(b[::-1].hex(), targets)
                self.assertIn(b"".join(b[i:i+4][::-1] for i in range(0, 20, 4)).hex(), targets)
            self.assertNotIn(hashlib.sha1(b"x").hexdigest(), targets)
            k = Path(d, "k163_md5.txt").read_text().split()
            self.assertIn("23e21d6019e1211f6bd47ec180256e97", k); self.assertEqual(len(k), 4)


class TestFreelipSweep(unittest.TestCase):
    P192 = dict(p=2**192 - 2**64 - 1, a=-3, b=0x64210519e59c80e70fa7e9ab72243049feb8deecc146b9b1,
                Gx=0x188da80eb03090f67cbf20eb43a18800f4ff0afd82ff1012, Gy=0x07192b95ffc8da78631011ed6b24cdd573f977a11e794811,
                n=0xffffffffffffffffffffffff99def836146bc9b1b4d22831)

    def test_recovers_published_p192_from_seed_20000(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            hits = freelip_sweep.sweep("P-192", self.P192, 20005, discards=(7,))
        self.assertEqual(hits, 1)
        self.assertIn("seed=20000 discard=7 limbs=9 try=2", buf.getvalue())

    def test_recovers_planted_point_on_p256_with_nonstandard_discard(self):
        # build a generator on P-256 by the recipe with seed 777, discard 5, then check the sweep finds it
        c = dict(freelip_sweep.CURVES["P-256"]); p, a, b = c["p"], c["a"], c["b"]
        state = 777
        def limb():
            nonlocal state
            state = state * freelip_sweep.A % freelip_sweep.M; return state % 2**26
        for _ in range(5): limb()
        L = -(-p.bit_length() // 26) + 1
        while True:
            x = 0
            for _ in range(L): x = x << 26 | limb()
            x %= p; rhs = (x**3 + a * x + b) % p
            if pow(rhs, (p - 1) // 2, p) == 1: break
        y = pow(rhs, (p + 1) // 4, p); assert y * y % p == rhs
        c["Gx"], c["Gy"] = x, y
        buf = io.StringIO()
        with redirect_stdout(buf):
            hits = freelip_sweep.sweep("planted", c, 800, discards=range(0, 13))
        self.assertGreaterEqual(hits, 1)
        self.assertIn("seed=777 discard=5", buf.getvalue())

    def test_no_false_positive_on_real_p256_small_range(self):
        hits = freelip_sweep.sweep("P-256", freelip_sweep.CURVES["P-256"], 50, discards=(7,))
        self.assertEqual(hits, 0)


class TestNibbleRules(unittest.TestCase):
    def test_recovers_planted_first_on_curve_rule(self):
        # plant: "first on-curve x at or after ...9c60" -> i = 0, 0, 2, 1 (from the record), and check it is found
        planted = {"secp160k1": 0, "secp192k1": 0, "secp224k1": 2, "secp256k1": 1}
        found = nibble_rules.main(used=planted, span=16, pairs=False, verbose=False)
        self.assertIn((0, 1, 1, "on"), found)

    def test_published_nibbles_are_not_first_on_curve(self):
        found = nibble_rules.main(span=16, pairs=False, verbose=False)
        self.assertNotIn((0, 1, 1, "on"), found)


class TestEcArithmetic(unittest.TestCase):
    def test_half_generator_constants_are_recomputed(self):
        # the whole investigation rests on these values; recompute them from the published G
        want = {"secp160k1": "48ce563f89a0ed9414f5aa28ad0d96d6795f9c62", "secp192k1": "554123b78ce563f89a0ed9414f5aa28ad0d96d6795f9c66",
                "secp224k1": "3b78ce563f89a0ed9414f5aa28ad0d96d6795f9c63", "secp256k1": "3b78ce563f89a0ed9414f5aa28ad0d96d6795f9c63"}
        for name, hx in want.items():
            c = SecCurve(SEC_CURVES[name]); G = (c.Gx, c.Gy)
            self.assertIsNone(c.mul(c.n, G))
            self.assertEqual(f"{c.mul((c.n + 1) // 2, G)[0]:x}", hx)


class TestHashes(unittest.TestCase):
    def test_pure_python_hashes_against_published_vectors(self):
        from hashes import md4, sha0, ripemd128, ripemd160, ripemd160_best
        self.assertEqual(md4(b"abc").hex(), "a448017aaf21d8525fc10ae87aa6729d")
        self.assertEqual(sha0(b"abc").hex(), "0164b8a914cd2a5e74c4f7ff082c4d97f1edf880")
        self.assertEqual(ripemd128(b"abc").hex(), "c14a12199c66e4ba84636b0f69144c77")
        self.assertEqual(ripemd160(b"abc").hex(), "8eb208f7e05d987a9b044a8e98c6b087f15a0bfc")
        self.assertEqual(ripemd160(b"message digest").hex(), "5d0689ef49d2fae572b881b123a85ffa21595f36")
        self.assertEqual(ripemd160_best(b"abc"), ripemd160(b"abc"))   # whichever backend, same answer


class TestSha1Steps(unittest.TestCase):
    def test_backward_from_digest_recovers_iv_and_rejects_wrong_block(self):
        msg = b"Standards for Efficient Cryptography"
        d = sha1_steps.sha1(msg); self.assertEqual(d, hashlib.sha1(msg).digest())
        final = sha1_steps.final_state_from_digest(struct.unpack(">5I", d))
        self.assertEqual(sha1_steps.run_backwards(final, sha1_steps.pad(msg)), sha1_steps.IV)
        self.assertNotEqual(sha1_steps.run_backwards(final, sha1_steps.pad(msg + b"?")), sha1_steps.IV)


if __name__ == "__main__":
    unittest.main()
