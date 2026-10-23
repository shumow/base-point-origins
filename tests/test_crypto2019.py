import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SAGE = shutil.which("sage")
OFFSETS = "[977, 949, 739, 487, 361, 359, 263]"


class PythonVerificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with tempfile.TemporaryDirectory() as directory:
            cls.result = subprocess.run(
                [sys.executable, "-B", str(ROOT / "scripts" / "verify_crypto2019.py")],
                cwd=directory, capture_output=True, text=True, timeout=60,
            )
            cls.created_files = list(Path(directory).iterdir())

    def test_arithmetic_checks_pass_without_writing_to_the_working_directory(self):
        self.assertEqual(self.result.returncode, 0, self.result.stderr + self.result.stdout)
        self.assertEqual(self.result.stderr, "")
        self.assertEqual(self.created_files, [])
        self.assertNotIn("  FAIL ", self.result.stdout)

    def test_cm_report_distinguishes_probable_primes_from_certificates(self):
        self.assertIn("probable primes, not certificates", self.result.stdout)
        self.assertIn(f"probable-prime offsets below 2^256-2^32: {OFFSETS}", self.result.stdout)
        self.assertIn("7 probable-prime moduli in the full window", self.result.stdout)
        self.assertIn("3 split moduli (p = 1 mod 3)", self.result.stdout)
        self.assertIn("18 CM candidate orders checked", self.result.stdout)
        self.assertIn("ALL OK (CM primality is probable-prime only)", self.result.stdout)

    def test_counter_report_only_excludes_direct_counter_models(self):
        for curve in ("secp160k1", "secp192k1", "secp224k1", "secp256k1"):
            for bits in (4, 6, 8):
                for direction in ("up", "down"):
                    self.assertIn(
                        f"{curve}: count-{direction} over the low {bits} bits does not pick the actual value",
                        self.result.stdout,
                    )
            for direction in ("up", "down"):
                self.assertIn(
                    f"{curve}: first lifting top nibble counting {direction} does not pick the actual value",
                    self.result.stdout,
                )
        self.assertIn("Counter-before-hash/transform constructions are not tested.", self.result.stdout)

    def test_recorded_python_output_is_reproducible(self):
        expected = (ROOT / "results" / "verify-crypto2019.txt").read_text(encoding="utf-8")
        self.assertEqual(self.result.stdout, expected)


@unittest.skipUnless(SAGE, "SageMath is required for the independent proof-enabled check")
class SageVerificationTests(unittest.TestCase):
    def test_proof_enabled_reconstruction_and_recorded_output(self):
        script = ROOT / "references" / "crypto2019-rump" / "halve_generators.sage"
        command = """
from pathlib import Path
import sys
from sage.repl.preparse import preparse
source = Path(sys.argv[1])
namespace = {"__file__": str(source), "__name__": "__main__"}
exec("from sage.all import *", namespace)
exec(compile(preparse(source.read_text(encoding="utf-8")), str(source), "exec"), namespace)
"""
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [SAGE, "-python", "-B", "-c", command, str(script)],
                cwd=directory, capture_output=True, text=True, timeout=120,
                env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"),
            )
            self.assertEqual(list(Path(directory).iterdir()), [])
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertEqual(result.stderr, "")
        self.assertIn("primality mode: Sage is_prime(proof=True)", result.stdout)
        self.assertIn(f"proven prime offsets below 2^256-2^32: {OFFSETS}", result.stdout)
        self.assertIn("prime moduli: 7; split primes (p = 1 mod 3): 3", result.stdout)
        self.assertIn("CM candidate orders checked: 18; proven prime orders: 1", result.stdout)
        self.assertIn("not the historical generation procedure", result.stdout)
        expected = (ROOT / "results" / "verify-crypto2019-sage.txt").read_text(encoding="utf-8")
        self.assertEqual(result.stdout, expected)


if __name__ == "__main__":
    unittest.main()
