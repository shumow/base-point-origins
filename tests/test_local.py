import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import local


class TestSandbox(unittest.TestCase):
    def test_only_the_output_mount_is_writable(self):
        options = local.sandbox_options("/mnt/c/research", "/mnt/c/research/runs/example")
        for flag in ("--rm", "--pull=never", "--read-only", "--network=none",
                     "--user=1000:1000", "--cap-drop=ALL", "--security-opt=no-new-privileges",
                     "--pids-limit=128", "--cpus=2", "--memory=2g", "--memory-swap=2g"):
            self.assertIn(flag, options)
        mounts = [options[i + 1] for i, value in enumerate(options) if value == "--mount"]
        self.assertEqual(mounts, [
            "type=bind,source=/mnt/c/research,target=/work,readonly",
            "type=bind,source=/mnt/c/research/runs/example,target=/output",
        ])
        self.assertFalse(any("docker.sock" in option for option in options))

    def test_test_container_has_no_writable_host_mount(self):
        self.assertEqual(local.sandbox_options("/source").count("--mount"), 1)
        self.assertIn("type=bind,source=/source,target=/work,readonly",
                      local.sandbox_options("/source"))

    def test_path_conversion_is_checked_and_preserves_spaces(self):
        with patch.object(local.subprocess, "run") as run:
            run.return_value = subprocess.CompletedProcess([], 0, "/mnt/c/with spaces\n")
            self.assertEqual(local.linux_path(Path("with spaces"), "Ubuntu"), "/mnt/c/with spaces")
            self.assertTrue(run.call_args.kwargs["check"])
            run.return_value.stdout = "/mnt/c/with,comma\n"
            with self.assertRaisesRegex(ValueError, "commas"):
                local.linux_path(Path("with,comma"), "Ubuntu")


class TestGpuCommand(unittest.TestCase):
    def test_gpu_only_low_workload_and_per_run_state(self):
        output = Path("run with spaces")
        command = local.hashcat_command(Path("hashcat.exe"), output, "sha1", 100,
                                       "secp_core_sha1.txt", 2, 30)
        for key, value in (("-m", "100"), ("-D", "2"), ("-d", "2"), ("-w", "1"),
                           ("--runtime", "30"), ("--outfile-format", "1,3")):
            self.assertEqual(command[command.index(key) + 1], value)
        for key in ("--potfile-path", "--restore-file-path", "--outfile"):
            self.assertEqual(Path(command[command.index(key) + 1]).parent, output)
        self.assertNotIn("--force", command)
        self.assertIn("--keep-guessing", command)
        self.assertEqual(command[-1], str(output / "dictionary.txt"))

    def test_bounded_defaults_and_invalid_budgets(self):
        args = local.parser().parse_args(["search"])
        self.assertEqual(args.seconds, 60)
        self.assertEqual(args.device, 1)
        for value in ("0", "-1"):
            with self.assertRaises(argparse.ArgumentTypeError):
                local.positive_int(value)


class TestRecoveryVerification(unittest.TestCase):
    def write_recoveries(self, directory, algorithm, words):
        path = Path(directory) / "recovered"
        targets = set()
        lines = []
        for word in words:
            data = word.encode("ascii")
            digest = hashlib.new(algorithm, data).hexdigest()
            targets.add(digest)
            lines.append(f"{digest}:{data.hex()}")
        path.write_text("\n".join(lines) + "\n", encoding="ascii")
        return path, targets

    def test_controls_are_not_reported_as_discoveries(self):
        for algorithm in ("sha1", "md5"):
            with self.subTest(algorithm=algorithm), tempfile.TemporaryDirectory() as directory:
                path, targets = self.write_recoveries(directory, algorithm, [*local.CONTROLS, "found"])
                hits, partial_matches = local.verify_recoveries(path, algorithm, targets)
                self.assertEqual(partial_matches, [])
                self.assertEqual(hits, [{
                    "hash": hashlib.new(algorithm, b"found").hexdigest(),
                    "plaintext_hex": b"found".hex(),
                }])

    def test_missing_control_invalidates_the_run(self):
        with tempfile.TemporaryDirectory() as directory:
            path, targets = self.write_recoveries(directory, "sha1", ["Certicom"])
            with self.assertRaisesRegex(RuntimeError, "Missing sha1 positive control"):
                local.verify_recoveries(path, "sha1", targets)

    def test_sha1_representative_is_rehashed_against_the_full_target_set(self):
        with tempfile.TemporaryDirectory() as directory:
            path, targets = self.write_recoveries(directory, "sha1", [*local.CONTROLS, "found"])
            actual = hashlib.sha1(b"found").hexdigest()
            representative = "00" + actual[2:]
            targets.add(representative)
            path.write_text(path.read_text().replace(actual, representative), encoding="ascii")
            hits, partial_matches = local.verify_recoveries(path, "sha1", targets)
            self.assertEqual(hits, [{"hash": actual, "plaintext_hex": b"found".hex()}])
            self.assertEqual(partial_matches, [])

    def test_sha1_partial_collision_is_recorded_not_reported_as_a_hit(self):
        with tempfile.TemporaryDirectory() as directory:
            path, targets = self.write_recoveries(directory, "sha1", list(local.CONTROLS))
            actual = hashlib.sha1(b"partial match").hexdigest()
            representative = "00000000" + actual[8:]
            targets.add(representative)
            with path.open("a", encoding="ascii") as output:
                output.write(f"{representative}:{b'partial match'.hex()}\n")
            hits, partial_matches = local.verify_recoveries(path, "sha1", targets)
            self.assertEqual(hits, [])
            self.assertEqual(partial_matches, [{
                "reported_hash": representative, "computed_hash": actual,
                "plaintext_hex": b"partial match".hex(),
            }])

    def test_absent_recovery_file_is_not_a_negative_result(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(RuntimeError, "positive controls were not recovered"):
                local.verify_recoveries(Path(directory) / "missing", "sha1", set())

    def test_corrupt_recovery_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path, targets = self.write_recoveries(directory, "md5", list(local.CONTROLS))
            path.write_text(path.read_text().replace(b"Certicom".hex(), b"other".hex()),
                            encoding="ascii")
            with self.assertRaisesRegex(RuntimeError, "independent verification"):
                local.verify_recoveries(path, "md5", targets)

    def test_unrequested_hash_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path, _ = self.write_recoveries(directory, "sha1", list(local.CONTROLS))
            with self.assertRaisesRegex(RuntimeError, "independent verification"):
                local.verify_recoveries(path, "sha1", set())


class TestGpuRunStatus(unittest.TestCase):
    def run_mocked_gpu(self, directory, exit_codes):
        output = Path(directory)
        executable = output / "hashcat.exe"
        executable.touch()
        for algorithm, _, filename, _ in local.ALGORITHMS:
            lines = []
            digests = []
            for word in local.CONTROLS:
                data = word.encode("ascii")
                digest = hashlib.new(algorithm, data).hexdigest()
                lines.append(f"{digest}:{data.hex()}")
                digests.append(digest)
            (output / filename).write_text("\n".join(digests) + "\n", encoding="ascii")
            (output / f"{algorithm}.recovered").write_text("\n".join(lines) + "\n", encoding="ascii")
        args = argparse.Namespace(hashcat=executable, distro="Ubuntu", device=1, seconds=1)
        results = [subprocess.CompletedProcess([], 0, "v7.1.2\n")]
        results += [subprocess.CompletedProcess([], code) for code in exit_codes]
        with patch.object(local, "prepare_run", return_value=(output, {"stages": []})):
            with patch.object(local.subprocess, "run", side_effect=results):
                return local.gpu_run(args, smoke=True)

    def test_exhausted_passes_are_completed_after_controls_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(self.run_mocked_gpu(directory, [1, 1]), 0)
            manifest = json.loads((Path(directory) / "run.json").read_text())
            self.assertEqual(manifest["status"], "completed")
            self.assertTrue(all(stage["controls_verified"] for stage in manifest["stages"]))
            self.assertTrue(all(stage["state"] == "exhausted" for stage in manifest["stages"]))

    def test_runtime_limit_is_incomplete_and_preserves_exit_code(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(self.run_mocked_gpu(directory, [4, 1]), 4)
            manifest = json.loads((Path(directory) / "run.json").read_text())
            self.assertEqual(manifest["status"], "time_limited")
            self.assertEqual(manifest["stages"][0]["state"], "time_limited")

    def test_backend_error_is_recorded_and_raised(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(RuntimeError, "failed with exit code -1"):
                self.run_mocked_gpu(directory, [-1])
            manifest = json.loads((Path(directory) / "run.json").read_text())
            self.assertEqual(manifest["status"], "failed")
            self.assertIn("exit code -1", manifest["error"])
            self.assertNotIn("controls_verified", manifest["stages"][0])


if __name__ == "__main__":
    unittest.main()
