"""Experiment 1 of notes/experiment-shortlist.md: the nothing-up-my-sleeve / structured non-semantic corpus.

Tests the hypothesis that the secp*k1 core (bits 4..151 = ce563f89a0ed9414f5aa28ad0d96d6795f9c6) or the K-163 value
(23e21d6019e1211f6bd47ec180256e97, top two bits zero) is NOT a hash of a human sentence but either
  (a) a famous value itself -- the leading hex digits of a math constant, a hash IV/round constant, another curve's
      parameter -- possibly truncated or reduced (the DIRECT test), or
  (b) the hash of such a famous value (the HASH test, reusing the existing secp-core and K-163 matchers).

This is candidate selection, not cryptanalysis. The corpus is frozen in build_corpus(); a negative result means exactly
"none of these frozen famous values, in these encodings, under these matchers." Positive controls are planted and must
be recovered (see tests/test_nothing_up_my_sleeve.py) before any null result here is trusted.

Run:  python3 scripts/nothing_up_my_sleeve.py [--output-dir results]
"""
import argparse
import hashlib
import json
import sys
from decimal import Decimal, getcontext
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent / "k163"))
import secg_core_search as core
import search as k163               # K-163 128-bit matcher: match(), HASHES, TARGET

HEX_DIGITS = 160                    # fractional hex digits to expand each constant to


def frac_hex(x: Decimal, n: int) -> str:
    """The first n hex digits of the fractional part of a positive Decimal."""
    frac = x - int(x)
    out = []
    for _ in range(n):
        frac *= 16
        digit = int(frac)
        out.append("0123456789abcdef"[digit])
        frac -= digit
    return "".join(out)


def math_constants() -> dict:
    """pi, e, ln2, sqrt2/3/5, phi -- computed, not hardcoded, so they are auditable."""
    getcontext().prec = HEX_DIGITS * 2 + 50
    # pi via Chudnovsky
    C = 426880 * Decimal(10005).sqrt()
    M, L, X, S, K = 1, 13591409, 1, Decimal(13591409), 6
    for i in range(1, HEX_DIGITS // 3 + 3):
        M = M * (K**3 - 16 * K) // (i**3)
        L += 545140134
        X *= -262537412640768000
        S += Decimal(M * L) / X
        K += 12
    pi = C / S
    return {
        "pi": pi, "e": Decimal(1).exp(), "ln2": Decimal(2).ln(),
        "sqrt2": Decimal(2).sqrt(), "sqrt3": Decimal(3).sqrt(), "sqrt5": Decimal(5).sqrt(),
        "phi": (1 + Decimal(5).sqrt()) / 2,
    }


# Famous standards-world values, as hex strings (lowercase, no 0x).
STANDARDS_HEX = {
    # Hash initialization vectors and SHA-1 round constants (the canonical nothing-up-my-sleeve numbers).
    "sha1_iv": "67452301efcdab8998badcfe10325476c3d2e1f0",
    "md5_iv": "0123456789abcdeffedcba9876543210",
    "md5_iv_le": "0123456789abcdeffedcba9876543210",
    "sha1_k": "5a8279996ed9eba18f1bbcdcca62c1d6",
    # Other SEC curve public coordinates and the r-curve SEEDs (which embed ASCII "Minghua Qu").
    "secp160r1_xG": "4a96b5688ef573284664698968c38bb913cbfc82",
    "secp160r2_xGhalf": "4a96b5688ef573284664698e81e1510fae4e8422",
    "secp160r1_seed": "1053cde42c14d696e67687561517533bf3f83345",
    "secp160r2_seed": "b99b99b099b323e02709a4d696e6768756151751",
    # Field primes of the k1 curves.
    "p160k1": "fffffffffffffffffffffffffffffffeffffac73",
    "p192k1": "fffffffffffffffffffffffffffffffffffffffeffffee37",
    "p256k1": "fffffffffffffffffffffffffffffffffffffffffffffffffffffffefffffc2f",
    # The targets themselves, for the reversed/complement self-reference checks.
    "secp_core": f"{core.CORE:037x}",
    "k163_target": k163.TARGET.hex(),
}


def build_corpus():
    """Return (direct_values, hash_candidates). Frozen: edit here and record the change, do not vary at run time.

    direct_values: list of (label, hexstring) searched for the targets as substrings / exact / reduced.
    hash_candidates: list of (label, bytes) fed to the secp-core and K-163 hash matchers.
    """
    constants = math_constants()
    direct, hash_cands = [], []

    for name, value in constants.items():
        h = frac_hex(value, HEX_DIGITS)
        direct.append((f"frac_hex({name})", h))
    for name, h in STANDARDS_HEX.items():
        direct.append((name, h))

    # Hash inputs: each famous value as raw bytes, as lowercase/upper hex ASCII, and as decimal ASCII; plus a few
    # era names/labels that are non-semantic markers rather than sentences.
    def add(label, data: bytes):
        hash_cands.append((label, data))

    for name, h in STANDARDS_HEX.items():
        raw = bytes.fromhex(h if len(h) % 2 == 0 else "0" + h)
        add(f"{name}:raw", raw)
        add(f"{name}:hexlo", h.encode("ascii"))
        add(f"{name}:hexup", h.upper().encode("ascii"))
    for name, value in constants.items():
        hx = frac_hex(value, 64)
        add(f"{name}:frachex64", hx.encode("ascii"))
        add(f"{name}:frachex40", hx[:40].encode("ascii"))
        add(f"{name}:raw20", bytes.fromhex(hx[:40]))
    for marker in ("", "nothing up my sleeve", "0", "1", "secp256k1", "Koblitz"):
        add(f"marker:{marker!r}", marker.encode("ascii"))

    return direct, hash_cands


def run_direct(direct_values):
    """Substring / exact / reversed matches of the two targets inside the famous hex strings."""
    core_hex = f"{core.CORE:037x}"
    full_hex = {f"{v:040x}": name for v, name in core.FULL.items()}
    k163_hex = k163.TARGET.hex()
    needles = {core_hex: "secp_core(148)", k163_hex: "k163(128)", **{h: f"full:{n}" for h, n in full_hex.items()}}
    self_identity = {"secp_core": "secp_core(148)", "k163_target": "k163(128)"}  # the targets probe themselves
    hits = []
    for label, h in direct_values:
        hl = h.lower()
        variants = {"as-is": hl, "reversed-hex": hl[::-1]}
        for vname, hv in variants.items():
            for needle, what in needles.items():
                if needle in hv:
                    if vname == "as-is" and self_identity.get(label) == what:
                        continue  # a target matching itself is a tautology, not a finding
                    hits.append({"source": label, "reading": vname, "target": what,
                                 "offset_hexdigits": hv.index(needle)})
    return hits


def run_hash(hash_candidates):
    """Feed candidates to the existing secp-core matcher and the K-163 matcher."""
    core_result = core.search(hash_candidates)          # includes suffixes, readings, controls-free
    core_hits = core_result["hits"]
    k163_hits = []
    for label, b in hash_candidates:
        for hname, hf in k163.HASHES.items():
            digest = hf(b)
            m = k163.match(digest)
            if m:
                k163_hits.append({"label": label, "hash": hname, "match": m, "digest": digest.hex()})
    return core_hits, k163_hits, core_result["candidate_count"], len(hash_candidates)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("results"))
    args = parser.parse_args()

    direct_values, hash_candidates = build_corpus()
    direct_hits = run_direct(direct_values)
    core_hits, k163_hits, core_count, hash_count = run_hash(hash_candidates)

    result = {
        "experiment": "nothing-up-my-sleeve",
        "corpus_sha256": hashlib.sha256(
            json.dumps([(l, h) for l, h in direct_values]
                       + [(l, b.hex()) for l, b in hash_candidates]).encode()).hexdigest(),
        "direct_sources": len(direct_values),
        "hash_candidates": hash_count,
        "core_hash_evaluations": core_count,
        "direct_hits": direct_hits,
        "core_hash_hits": core_hits,
        "k163_hash_hits": k163_hits,
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "nothing-up-my-sleeve.json").write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8")
    total = len(direct_hits) + len(core_hits) + len(k163_hits)
    text = (f"nothing-up-my-sleeve: {len(direct_values)} direct sources, {hash_count} hash candidates; "
            f"direct {len(direct_hits)} hits, secp-core {len(core_hits)} hits, K-163 {len(k163_hits)} hits; "
            f"{total} total\n")
    (args.output_dir / "nothing-up-my-sleeve.txt").write_text(text, encoding="utf-8")
    print(text, end="", flush=True)
    for h in direct_hits + core_hits + k163_hits:
        print("HIT", h, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
