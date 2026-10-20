"""Core-matched preimage search for the secp*k1 half-generator constant.
Tests whether bits 4..151 of any 160-bit digest (SHA-1, SHA-0, RIPEMD-160, doubled variants) of the k163 string set,
with the usual readings (as-is, byte-reversed, word-swapped) and X9.62-style counters, equal the shared 148-bit core
ce563f89a0ed9414f5aa28ad0d96d6795f9c6. Also tests the full secp224k1/256k1 value as the low 160 bits with top byte 78,
and the secp160k1 value 48ce...9c62 exactly."""
import argparse
import hashlib
import itertools
import json
import ssl
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent / "k163"))
from hashes import sha0
from strings import all_strings

CORE = 0xce563f89a0ed9414f5aa28ad0d96d6795f9c6          # bits 4..151 of every secp*k1 half x
MASK = (1 << 148) - 1
FULL = {0x48ce563f89a0ed9414f5aa28ad0d96d6795f9c62: "secp160k1 x(G/2)",
        0x78ce563f89a0ed9414f5aa28ad0d96d6795f9c63: "low 160 bits of secp224k1/256k1 x(G/2)"}

HASHES = {
    "sha1": lambda b: hashlib.sha1(b).digest(),
    "sha0": sha0,
    "ripemd160": lambda b: hashlib.new("ripemd160", b).digest(),
    "sha1(sha1)": lambda b: hashlib.sha1(hashlib.sha1(b).digest()).digest(),
    "sha1(md5)": lambda b: hashlib.sha1(hashlib.md5(b).digest()).digest(),
}
SUFFIXES = (b"",) + tuple(cb for c in range(4) for cb in
                         (bytes([c]), str(c).encode(), c.to_bytes(4, "big")))

def readings(d):
    yield "d", d
    yield "rev", d[::-1]
    yield "wswap", b"".join(d[i:i+4][::-1] for i in range(0, len(d), 4))

def check(d):
    if len(d) != 20:
        raise ValueError("Core search requires a 160-bit digest")
    for name, r in readings(d):
        v = int.from_bytes(r, "big")
        if v in FULL: return name + " full"
        if (v >> 4) & MASK == CORE: return name + " core"
    return None

def search(candidates):
    for name, function in HASHES.items():
        try:
            digest = function(b"")
        except ValueError as error:
            raise RuntimeError(f"Required hash {name} is unavailable; search not started") from error
        if len(digest) != 20:
            raise ValueError(f"{name} did not produce a 160-bit digest")
    n = count = 0
    input_digest = hashlib.sha256()
    hits = []
    for label, b in candidates:
        count += 1
        input_digest.update(json.dumps([label, b.hex()], ensure_ascii=True).encode("ascii") + b"\n")
        for hname, hf in HASHES.items():
            for suffix in SUFFIXES:
                match = check(hf(b + suffix))
                n += 1
                if match:
                    hit = dict(label=label, input_hex=b.hex(), algorithm=hname,
                               suffix_hex=suffix.hex(), match=match)
                    hits.append(hit)
                    print("HIT", hit, flush=True)
    return dict(status="completed", algorithms=list(HASHES), candidate_count=count,
                suffixes_hex=[s.hex() for s in SUFFIXES], readings=["d", "rev", "wswap"],
                core_hex=f"{CORE:x}", core_bit_range=[4, 151], evaluations=n, hits=hits,
                input_sequence_sha256=input_digest.hexdigest(),
                python_version=sys.version, openssl_version=ssl.OPENSSL_VERSION,
                reading_definitions=dict(d="digest bytes as-is", rev="reverse all bytes",
                                         wswap="reverse bytes within each 4-byte word"),
                full_targets_hex=[f"{v:040x}" for v in FULL])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path,
                        default=Path(__file__).resolve().parents[1] / "results")
    parser.add_argument("--limit", type=int, help="Bounded smoke search; not the full input set")
    args = parser.parse_args()
    if args.limit is not None and args.limit < 1:
        raise ValueError("--limit must be positive")
    candidates = all_strings()
    if args.limit is not None:
        candidates = itertools.islice(candidates, args.limit)
    result = search(candidates)
    result["limit"] = args.limit
    result["scope"] = "full" if args.limit is None else "bounded"
    result["input_set"] = "scripts/k163/strings.py:all_strings"
    result["source_sha256"] = {
        str(path.name): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in (Path(__file__).resolve(), Path(__file__).resolve().parent / "k163" / "strings.py",
                     Path(__file__).resolve().parent / "k163" / "hashes.py")}
    args.output_dir.mkdir(parents=True, exist_ok=True)
    stem = "secg-core-search" if args.limit is None else "secg-core-search-smoke"
    (args.output_dir / (stem + ".json")).write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8")
    text = (f"algorithms: {', '.join(result['algorithms'])}\n"
            f"candidates: {result['candidate_count']}; suffix variants: {len(SUFFIXES)}; "
            f"readings: d, rev, wswap; limit: {args.limit}\n"
            f"done: {result['evaluations']} evaluations, {len(result['hits'])} hits\n")
    (args.output_dir / (stem + ".txt")).write_text(text, encoding="utf-8")
    print(text, end="")

if __name__ == "__main__":
    main()
