"""Local Windows GPU searches, with Python/PARI work isolated in WSL Docker."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import socket
import subprocess
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parent.parent
IMAGE = "base-point-origins:local"
CONTROLS = ("Certicom", "Certicom1")
ALGORITHMS = (("sha1", 100, "secp_core_sha1.txt", 12290),
              ("md5", 0, "k163_md5.txt", 6))
DEFAULT_HASHCAT = ROOT / ".tools" / "hashcat-7.1.2" / "hashcat.exe"

SANDBOX_PROBE = """
import errno, os, pathlib, socket
if os.geteuid() == 0:
    raise RuntimeError("Container must not run as root")
status = dict(line.split(":", 1) for line in pathlib.Path("/proc/self/status").read_text().splitlines() if ":" in line)
if status["NoNewPrivs"].strip() != "1" or int(status["CapEff"].strip(), 16):
    raise RuntimeError("Container privileges are not restricted")
mounts = [line.split() for line in pathlib.Path("/proc/mounts").read_text().splitlines()]
for directory in ("/", "/work"):
    if not any(row[1] == directory and "ro" in row[3].split(",") for row in mounts):
        raise RuntimeError(directory + " is not mounted read-only")
    probe = pathlib.Path(directory) / ".base-point-sandbox-probe"
    try:
        with probe.open("x"):
            pass
    except OSError as error:
        if error.errno not in (errno.EROFS, errno.EACCES):
            raise
    else:
        probe.unlink()
        raise RuntimeError(directory + " unexpectedly accepts writes")
if any(name != "lo" for _, name in socket.if_nameindex()):
    raise RuntimeError("Container has an external network interface")
print("Sandbox verified: non-root, no capabilities, no new privileges, read-only source/root, no external network")
"""


def positive_int(value: str) -> int:
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return number


def wsl_command(distro: str, *command: str) -> list[str]:
    return ["wsl.exe", "--distribution", distro, "--cd", str(ROOT),
            "--exec", *command]


def linux_path(path: Path, distro: str) -> str:
    result = subprocess.run(wsl_command(distro, "wslpath", "-a", "-u", str(path)),
                            check=True, capture_output=True, text=True)
    converted = result.stdout.strip()
    if not converted or "," in converted:
        raise ValueError("Docker bind paths must be nonempty and contain no commas")
    return converted


def sandbox_options(source: str, output: str | None = None) -> list[str]:
    options = [
        "--rm", "--pull=never", "--read-only", "--network=none",
        "--user=1000:1000", "--cap-drop=ALL",
        "--security-opt=no-new-privileges", "--pids-limit=128",
        "--cpus=2", "--memory=2g", "--memory-swap=2g",
        "--tmpfs=/tmp:rw,nosuid,nodev,noexec,size=512m",
        "--mount", f"type=bind,source={source},target=/work,readonly",
        "--workdir=/work",
    ]
    if output is not None:
        options += ["--mount", f"type=bind,source={output},target=/output"]
    return options


def container_run(distro: str, command: list[str], output: Path | None = None) -> None:
    source = linux_path(ROOT, distro)
    destination = linux_path(output, distro) if output is not None else None
    subprocess.run(wsl_command(distro, "docker", "run",
                              *sandbox_options(source, destination), IMAGE, *command),
                   check=True)


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def normalize_newlines(data: bytes) -> bytes:
    r"""Collapse CRLF and lone CR line endings to LF.

    A Windows checkout (git autocrlf) or a user-supplied wordlist/rule file can
    carry CRLF. hashcat does not strip a trailing '\r' from a wordlist candidate
    or a rule line, so without this the real candidates would hash as b'word\r'
    while the LF-appended controls still crack -- masking every miss as a clean
    negative. rstrip alone does not help: it only touches the final line."""
    return data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def prepare_run(distro: str, purpose: str, wordlist: Path | None = None,
                rules: Path | None = None) -> tuple[Path, dict]:
    dictionary = normalize_newlines(wordlist.read_bytes()) if wordlist is not None else b"Certicom\n"
    rule_data = normalize_newlines(rules.read_bytes()) if rules is not None else b""
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output = ROOT / "runs" / f"{stamp}-{purpose}-{uuid.uuid4().hex[:8]}"
    output.mkdir(parents=True)
    container_run(distro, ["python", "-X", "utf8", "scripts/make_targets.py",
                          "/output", "--plant", *CONTROLS], output)
    # Keep the bare and rule-only controls in exactly the same GPU pass as the real targets.
    (output / "dictionary.txt").write_bytes(dictionary.rstrip(b"\r\n") + b"\nCerticom\n")
    (output / "search.rule").write_bytes(rule_data.rstrip(b"\r\n") + b"\n:\n$1\n")
    counts = {}
    for algorithm, _, filename, expected_count in ALGORITHMS:
        targets = (output / filename).read_text(encoding="ascii").splitlines()
        expected_length = hashlib.new(algorithm).digest_size * 2
        if (len(targets) != expected_count or len(set(targets)) != expected_count
                or any(len(target) != expected_length
                       or any(c not in "0123456789abcdef" for c in target)
                       for target in targets)):
            raise RuntimeError(f"Invalid {algorithm} target list: {output / filename}")
        for control in CONTROLS:
            if hashlib.new(algorithm, control.encode("ascii")).hexdigest() not in targets:
                raise RuntimeError(f"Missing {algorithm} positive control: {control}")
        counts[algorithm] = len(targets)
    image = subprocess.run(wsl_command(distro, "docker", "image", "inspect",
                                      "--format", "{{.Id}}", IMAGE),
                           check=True, capture_output=True, text=True).stdout.strip()
    manifest = {
        "status": "prepared", "purpose": purpose, "host": socket.gethostname(),
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "container_image": image, "distro": distro, "target_counts": counts,
        "controls": list(CONTROLS), "stages": [],
        "wordlist_source": str(wordlist.resolve()) if wordlist is not None else None,
        "rules_source": str(rules.resolve()) if rules is not None else None,
        "input_sha256": {
            name: hashlib.sha256((output / name).read_bytes()).hexdigest()
            for name in ("dictionary.txt", "search.rule", "secp_core_sha1.txt", "k163_md5.txt")
        },
    }
    write_json(output / "run.json", manifest)
    print(f"Prepared {counts['sha1']} SHA-1 and {counts['md5']} MD5 targets in {output}",
          flush=True)
    return output, manifest


def hashcat_command(executable: Path, output: Path, algorithm: str, mode: int,
                    targets: str, device: int, seconds: int) -> list[str]:
    command = [
        str(executable), "-m", str(mode), "-a", "0", "-D", "2", "-d", str(device),
        "-w", "1", "--runtime", str(seconds), "--status", "--status-timer", "5",
        "--session", f"bp-{algorithm}-{output.name}",
        "--potfile-path", str(output / f"{algorithm}.potfile"),
        "--restore-file-path", str(output / f"{algorithm}.restore"),
        "--logfile-disable", "--outfile", str(output / f"{algorithm}.recovered"),
        "--outfile-format", "1,3", "-r", str(output / "search.rule"),
        str(output / targets), str(output / "dictionary.txt"),
    ]
    if algorithm == "sha1":
        command.insert(1, "--keep-guessing")
    return command


def verify_recoveries(path: Path, algorithm: str,
                      targets: set[str]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    if not path.is_file():
        raise RuntimeError(f"No recovery file; positive controls were not recovered: {path}")
    recovered = {}
    partial_matches = []
    for line in path.read_text(encoding="ascii").splitlines():
        digest, separator, plain_hex = line.partition(":")
        if not separator:
            raise ValueError(f"Malformed hashcat recovery line in {path}")
        plain = bytes.fromhex(plain_hex)
        actual = hashlib.new(algorithm, plain).hexdigest()
        if digest not in targets:
            raise RuntimeError(f"Hashcat recovery failed independent verification: {digest}")
        # Mode 100 compares SHA-1 words 1..4; word 0 may be a deduplicated target's representative.
        if actual != digest and (algorithm != "sha1" or actual[8:] != digest[8:]):
            raise RuntimeError(f"Hashcat recovery failed independent verification: {digest}")
        if actual not in targets:
            partial_matches.append({"reported_hash": digest, "computed_hash": actual,
                                    "plaintext_hex": plain_hex})
            continue
        recovered[actual] = plain_hex
    controls = {hashlib.new(algorithm, word.encode("ascii")).hexdigest():
                word.encode("ascii").hex() for word in CONTROLS}
    for digest, plain_hex in controls.items():
        if recovered.get(digest) != plain_hex:
            raise RuntimeError(f"Missing {algorithm} positive control {bytes.fromhex(plain_hex)!r}")
    hits = [{"hash": digest, "plaintext_hex": value}
            for digest, value in recovered.items() if digest not in controls]
    return hits, partial_matches


def gpu_run(args: argparse.Namespace, smoke: bool) -> int:
    executable = args.hashcat.resolve()
    if not executable.is_file():
        raise FileNotFoundError(f"Hashcat not found: {executable}; use --hashcat or install the portable release")
    output, manifest = prepare_run(
        args.distro, "smoke" if smoke else "search",
        None if smoke else args.wordlist, None if smoke else args.rules)
    manifest.update(status="running", hashcat=str(executable), device=args.device,
                    seconds_per_algorithm=args.seconds)
    write_json(output / "run.json", manifest)
    try:
        version = subprocess.run([str(executable), "-V"], cwd=executable.parent,
                                 check=True, capture_output=True, text=True)
        manifest["hashcat_version"] = version.stdout.strip()
        for algorithm, mode, targets, _ in ALGORITHMS:
            command = hashcat_command(executable, output, algorithm, mode, targets,
                                      args.device, args.seconds)
            log_path = output / f"{algorithm}.log"
            stage = {"algorithm": algorithm, "command": command, "log": str(log_path)}
            manifest["stages"].append(stage)
            write_json(output / "run.json", manifest)
            print(f"Running {algorithm} on GPU device {args.device}; log: {log_path}", flush=True)
            started = time.monotonic()
            with log_path.open("wb") as log:
                result = subprocess.run(command, cwd=executable.parent, stdin=subprocess.DEVNULL,
                                        stdout=log, stderr=subprocess.STDOUT)
            stage.update(exit_code=result.returncode,
                         elapsed_seconds=round(time.monotonic() - started, 3))
            states = {0: "all_targets_recovered", 1: "exhausted", 4: "time_limited"}
            if result.returncode not in states:
                raise RuntimeError(f"Hashcat {algorithm} failed with exit code {result.returncode}; see {log_path}")
            stage["state"] = states[result.returncode]
            target_set = set((output / targets).read_text(encoding="ascii").splitlines())
            hits, partial_matches = verify_recoveries(
                output / f"{algorithm}.recovered", algorithm, target_set)
            stage["real_hits"] = hits
            stage["partial_matches_rejected"] = partial_matches
            stage["controls_verified"] = True
            write_json(output / "run.json", manifest)
            print(f"{algorithm}: {stage['state']}; both controls independently verified; "
                  f"{len(hits)} real hit(s); {len(partial_matches)} partial GPU match(es) rejected",
                  flush=True)
        limited = any(stage["exit_code"] == 4 for stage in manifest["stages"])
        manifest["status"] = "time_limited" if limited else "completed"
        write_json(output / "run.json", manifest)
        print(f"Report: {output / 'run.json'}", flush=True)
        if limited:
            print("Time budget reached: this is NOT an exhausted or negative search.", flush=True)
            return 4
        return 0
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as error:
        manifest.update(status="failed", error=str(error))
        write_json(output / "run.json", manifest)
        raise


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--distro", default="Ubuntu", help="local WSL distribution (default: Ubuntu)")
    result.add_argument("--hashcat", type=Path, default=DEFAULT_HASHCAT,
                        help="native Windows hashcat.exe path")
    result.add_argument("--device", type=positive_int, default=1,
                        help="GPU backend device ID from gpu-info (default: 1)")
    commands = result.add_subparsers(dest="action", required=True)
    commands.add_parser("build", help="build the CPU sandbox image; requires network access")
    commands.add_parser("test", help="verify sandbox isolation and run all positive-control tests")
    commands.add_parser("gpu-info", help="enumerate native Windows hashcat backends")
    for name in ("prepare", "smoke", "search"):
        command = commands.add_parser(name)
        if name != "smoke":
            command.add_argument("--wordlist", type=Path, default=ROOT / "wordlists" / "certicom.txt")
            command.add_argument("--rules", type=Path, help="optional hashcat rules; controls are added")
        if name != "prepare":
            command.add_argument("--seconds", type=positive_int, default=60,
                                 help="hashcat runtime budget per algorithm, excluding setup (default: 60)")
    return result


def main() -> int:
    args = parser().parse_args()
    if sys.platform != "win32":
        raise RuntimeError("Run this launcher with native Windows Python, not WSL Python")
    if args.action == "build":
        subprocess.run(wsl_command(args.distro, "docker", "build", "--network=host", "--tag", IMAGE, "-"),
                       input=(ROOT / "scripts" / "Dockerfile.local").read_bytes(), check=True)
    elif args.action == "test":
        container_run(args.distro, ["python", "-c", SANDBOX_PROBE])
        container_run(args.distro, ["python", "-X", "utf8", "-c",
            "import sys, unittest; "
            "suite = unittest.TestLoader().discover('tests'); "
            "suite.addTests(unittest.TestLoader().discover('scripts', pattern='test_secg.py')); "
            "result = unittest.TextTestRunner(verbosity=2).run(suite); "
            "sys.exit(not result.wasSuccessful())"])
    elif args.action == "prepare":
        prepare_run(args.distro, "targets", args.wordlist, args.rules)
    elif args.action == "gpu-info":
        executable = args.hashcat.resolve(strict=True)
        subprocess.run([str(executable), "-I"], cwd=executable.parent, check=True)
    else:
        return gpu_run(args, args.action == "smoke")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as error:
        print(f"error: {error}", file=sys.stderr)
        sys.exit(1)
