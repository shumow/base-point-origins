import contextlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import secg_core_search as core
import secg_scan as scan


ROOT = Path(__file__).resolve().parents[1]
GP = os.environ.get("GP") or shutil.which("gp")
MINIMA = {
    "secp112r1": (92, "55891*G", 97, "9482*G"),
    "secp112r2": (96, "52721*G", 92, "8376*G"),
    "secp128r1": (112, "28826*G", 110, "46572*G"),
    "secp128r2": (113, "37289*G", 110, "G/515"),
    "secp160k1": (140, "19380*G", 143, "14977*G"),
    "secp160r1": (145, "4849*G", 142, "41811*G"),
    "secp160r2": (145, "12334*G", 143, "13257*G"),
    "secp192k1": (173, "G/3838", 176, "64169*G"),
    "secp224k1": (166, "G/2", 208, "34761*G"),
    "secp256k1": (166, "G/2", 238, "22838*G"),
}


class CoordinateTests(unittest.TestCase):
    def test_all_generator_and_half_relations(self):
        rows = json.loads((ROOT / "results" / "secg-halfpoints.json").read_text())
        for name, d in scan.CURVES.items():
            with self.subTest(curve=name):
                c = scan.C(d)
                G = c.Gx, c.Gy
                half = c.mul((c.n + 1)//2, G)
                self.assertTrue(c.on(G))
                self.assertIsNone(c.mul(c.n, G))
                self.assertTrue(c.on(half))
                self.assertEqual(c.mul(2, half), G)
                self.assertEqual(f"{half[0]:x}", rows[name]["half_x"])

    def test_shared_core_and_prefix(self):
        halves = {}
        for name in ("secp160k1", "secp192k1", "secp224k1", "secp256k1", "secp160r2"):
            c = scan.C(scan.CURVES[name])
            halves[name] = c.mul((c.n + 1)//2, (c.Gx, c.Gy))[0]
        for name in ("secp160k1", "secp192k1", "secp224k1", "secp256k1"):
            self.assertEqual((halves[name] >> 4) & core.MASK, core.CORE)
        self.assertEqual(halves["secp224k1"], halves["secp256k1"])
        self.assertEqual(halves["secp224k1"].bit_length(), 166)
        self.assertEqual(f"{halves['secp160r2']:040x}"[:23],
                         f"{scan.CURVES['secp160r1']['Gx']:040x}"[:23])

    def test_complete_preimages_and_witnesses(self):
        for name, expected in (("secp112r2", [107, 108, 111, 111]),
                               ("secp128r2", [125, 127, 128, 128])):
            c = scan.C(scan.CURVES[name])
            G = c.Gx, c.Gy
            pre = scan.cofactor_preimages(c, G)
            self.assertEqual(len(set(pre)), 4)
            self.assertEqual(sorted(P[0].bit_length() for P in pre), expected)
            for P in pre:
                self.assertTrue(c.on(P))
                self.assertEqual(c.mul(c.h, P), G)
            row = scan.scan(name, scan.CURVES[name], K=2, KD=2)
            self.assertTrue(row["cofactor_preimages_complete"])
            self.assertEqual([(int(P["x"], 16), int(P["y"], 16))
                              for P in row["cofactor_preimages"]], pre)

    def test_incomplete_kernel_fails_instead_of_returning_partial_result(self):
        c = scan.C(scan.CURVES["secp112r2"])
        with self.assertRaisesRegex(ValueError, "Incomplete cofactor kernel"):
            scan.cofactor_preimages(c, (c.Gx, c.Gy), max_x=0)

    def test_unsupported_square_root_fails(self):
        c = scan.C(dict(scan.CURVES["secp112r2"], p=13))
        with self.assertRaisesRegex(ValueError, "p = 3 mod 4"):
            scan.cofactor_preimages(c, (c.Gx, c.Gy))

    def test_invalid_generator_and_bounds_fail(self):
        with self.assertRaisesRegex(ValueError, "invalid declared generator"):
            scan.scan("bad", dict(scan.CURVES["secp112r1"], Gx=0), K=2, KD=2)
        with self.assertRaisesRegex(ValueError, "bounds"):
            scan.scan("bad", scan.CURVES["secp112r1"], K=1)

    def test_trivial_cofactor_preimage(self):
        c = scan.C(scan.CURVES["secp160k1"])
        G = c.Gx, c.Gy
        self.assertEqual(scan.cofactor_preimages(c, G), [G])

    def test_cached_minima_have_exact_arithmetic_witnesses(self):
        rows = json.loads((ROOT / "results" / "secg-halfpoints.json").read_text())
        for name, (bx, lx, by, ly) in MINIMA.items():
            with self.subTest(curve=name):
                row = rows[name]
                self.assertEqual(row["shortest_x"], [bx, lx])
                self.assertEqual(row["shortest_y"], [by, ly])
                c = scan.C(scan.CURVES[name])
                G = c.Gx, c.Gy
                for axis, bits, label in ((0, bx, lx), (1, by, ly)):
                    k = pow(int(label[2:]), -1, c.n) if label.startswith("G/") else int(label[:-2])
                    P = c.mul(k, G)
                    value = P[0] if axis == 0 else min(P[1], c.p - P[1])
                    self.assertEqual(value.bit_length(), bits)

    def test_cached_witnesses_and_text_regeneration(self):
        rows = json.loads((ROOT / "results" / "secg-halfpoints.json").read_text())
        for name, row in rows.items():
            c = scan.C(scan.CURVES[name])
            G = c.Gx, c.Gy
            self.assertEqual(row["multiple_bound"], 2**16)
            self.assertEqual(row["inverse_bound"], 2**12)
            self.assertTrue(row["cofactor_preimages_complete"])
            pre = [(int(P["x"], 16), int(P["y"], 16)) for P in row["cofactor_preimages"]]
            self.assertEqual(pre, scan.cofactor_preimages(c, G))
        self.assertEqual(scan.report(rows), (ROOT / "results" / "secg-halfpoints.txt").read_text())

    @unittest.skipUnless(GP, "Set GP or put PARI/GP on PATH for independent SEC checks")
    def test_pari_halves_prime_orders_and_full_cofactor_orders(self):
        script = ""
        rows = json.loads((ROOT / "results" / "secg-halfpoints.json").read_text())
        for name, d in scan.CURVES.items():
            script += (f"E=ellinit([Mod({d['a']},{d['p']}),Mod({d['b']},{d['p']})]);"
                       f"G=[Mod({d['Gx']},{d['p']}),Mod({d['Gy']},{d['p']})];n={d['n']};"
                       'if(!isprime(n)||!ellisoncurve(E,G)||ellmul(E,G,n)!=[0],error("bad subgroup"));'
                       f"Q=ellmul(E,G,(n+1)/2);if(lift(Q[1])!=0x{rows[name]['half_x']},"
                       'error("bad half"));')
            if d["h"] > 1:
                script += f'if(ellcard(E)!={d["h"]}*n,error("bad full group order"));'
            script += "\n"
        result = subprocess.run([GP, "-fq", "-s", "512000000"],
                                input=script + 'print("SEC_CHECKS_OK");quit\n',
                                capture_output=True, text=True, timeout=120)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr.strip(), "")
        self.assertEqual(result.stdout.strip(), "SEC_CHECKS_OK")


class CoreSearchTests(unittest.TestCase):
    def test_full_target_controls_and_byte_readings(self):
        for value in core.FULL:
            digest = value.to_bytes(20, "big")
            self.assertEqual(core.check(digest), "d full")
            self.assertEqual(core.check(digest[::-1]), "rev full")
            self.assertEqual(core.check(dict(core.readings(digest))["wswap"]), "wswap full")

    def test_core_mask_boundaries(self):
        base = core.CORE << 4
        self.assertEqual(core.check(base.to_bytes(20, "big")), "d core")
        for bit in (0, 3, 152, 159):
            self.assertEqual(core.check((base ^ (1 << bit)).to_bytes(20, "big")), "d core")
        for bit in (4, 151):
            self.assertIsNone(core.check((base ^ (1 << bit)).to_bytes(20, "big")))
        self.assertIsNone(core.check(bytes(20)))
        with self.assertRaisesRegex(ValueError, "160-bit"):
            core.check(bytes(16))

    def test_missing_ripemd_is_explicit_and_no_inputs_are_consumed(self):
        def forbidden_inputs():
            self.fail("Search consumed candidates despite missing required hash")
            yield
        with patch.object(core.hashlib, "new", side_effect=ValueError("unsupported hash")):
            with self.assertRaisesRegex(RuntimeError, "ripemd160.*unavailable"):
                core.search(forbidden_inputs())
        self.assertIn("ripemd160", core.HASHES)

    def test_bounded_search_counts_actual_coverage(self):
        result = core.search([("abc", b"abc"), ("empty", b"")])
        self.assertEqual(result["algorithms"], list(core.HASHES))
        self.assertEqual(result["candidate_count"], 2)
        self.assertEqual(result["evaluations"], 2*5*13)
        self.assertEqual(result["hits"], [])
        self.assertEqual(len(result["suffixes_hex"]), 13)
        self.assertEqual(result["core_bit_range"], [4, 151])
        self.assertEqual(result["readings"], ["d", "rev", "wswap"])
        self.assertEqual(len(result["input_sequence_sha256"]), 64)

    def test_hit_manifest_preserves_witness(self):
        digest = next(iter(core.FULL)).to_bytes(20, "big")
        with patch.dict(core.HASHES, {"control": lambda b: digest}, clear=True):
            with contextlib.redirect_stdout(io.StringIO()):
                result = core.search([("positive", b"input")])
        self.assertEqual(len(result["hits"]), 13)
        self.assertEqual(result["hits"][0],
                         dict(label="positive", input_hex=b"input".hex(), algorithm="control",
                              suffix_hex="", match="d full"))


class CommandTests(unittest.TestCase):
    def run_script(self, script, cwd, *args):
        return subprocess.run([sys.executable, "-B", "-X", "utf8",
                               str(ROOT / "scripts" / script), *args],
                              cwd=cwd, capture_output=True, text=True, timeout=60)

    def test_import_has_no_execution_or_output_files(self):
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run([sys.executable, "-B", "-c",
                                     f"import sys;sys.path.insert(0,{str(ROOT / 'scripts')!r});"
                                     "import secg_scan;import secg_core_search"],
                                    cwd=directory, capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, "")
            self.assertEqual(result.stderr, "")
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_default_output_paths_are_repository_relative(self):
        rows = json.loads((ROOT / "results" / "secg-halfpoints.json").read_text())
        for module, args, stem in (
            (scan, [], "secg-halfpoints"),
            (core, ["--limit", "2"], "secg-core-search-smoke"),
        ):
            with self.subTest(module=module.__name__):
                with patch.object(sys, "argv", ["script", *args]), \
                     patch.object(Path, "write_text", autospec=True) as write, \
                     contextlib.redirect_stdout(io.StringIO()):
                    if module is scan:
                        with patch.object(scan, "scan", side_effect=lambda name, *a: rows[name]):
                            scan.main()
                    else:
                        core.main()
                self.assertEqual([call.args[0] for call in write.call_args_list],
                                 [ROOT / "results" / (stem + suffix) for suffix in (".json", ".txt")])

    def test_smoke_outputs_are_explicit_and_reproducible_from_other_cwd(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "reports"
            for script, args, stem in (
                ("secg_scan.py", ("--multiple-bound", "2", "--inverse-bound", "2"),
                 "secg-halfpoints-smoke"),
                ("secg_core_search.py", ("--limit", "2"), "secg-core-search-smoke"),
            ):
                first = self.run_script(script, directory, "--output-dir", str(output), *args)
                self.assertEqual(first.returncode, 0, first.stderr)
                before = {p.name: p.read_bytes() for p in output.glob(stem + ".*")}
                self.assertEqual(len(before), 2)
                second = self.run_script(script, directory, "--output-dir", str(output), *args)
                self.assertEqual(second.returncode, 0, second.stderr)
                self.assertEqual(before, {p.name: p.read_bytes() for p in output.glob(stem + ".*")})
            manifest = json.loads((output / "secg-core-search-smoke.json").read_text())
            self.assertEqual(manifest["scope"], "bounded")
            self.assertEqual(manifest["limit"], 2)
            self.assertEqual(manifest["evaluations"], 130)
            self.assertEqual(len(manifest["source_sha256"]), 3)
            self.assertFalse((output / "secg-halfpoints.json").exists())
            self.assertFalse((output / "secg-core-search.json").exists())
            self.assertFalse((Path(directory) / "secg_scan.json").exists())


if __name__ == "__main__":
    unittest.main()
