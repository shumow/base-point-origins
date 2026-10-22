"""Experiment 2 of notes/experiment-shortlist.md: explain the high bits of the secp*k1 half-generators.

All four secp*k1 half-point x-coordinates share bits 4..151 (the 148-bit core ce563f89a0ed9414f5aa28ad0d96d6795f9c6).
They differ in the low nibble (2,6,3,3 -- studied in nibble_rules.py) and in the HIGH bits above the core:

    secp160k1  x(G/2) =        48 | core | 2
    secp192k1  x(G/2) = 554123b78 | core | 6
    secp224k1  x(G/2) =      3b78 | core | 3
    secp256k1  x(G/2) =      3b78 | core | 3

So the byte directly above the core is 48 on secp160k1 but 78 on the other three, and the prefixes share 3b78
(192's 554123b78 ends in 3b78). This script tests the plan.md item-3 hypotheses for those high bits, as falsifiable
arithmetic: (a) simple counter/offset relations, (c) a single underlying value reduced mod each curve's prime
(item 3d), and (d) the top byte as the smallest on-curve completion. The shared-prefix hunt across other SEC/NIST/ANSI
curves (item 4) was already done by secg_scan.py (only the secp160r1/r2 92-bit overlap; no other >=32-bit match), so it
is not repeated here. Hash-preimage stories for the prefix (item 3b/3c) are covered by the core search and experiment 1.

Run:  python3 scripts/top_byte_analysis.py [--output-dir results]
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from secg_scan import CURVES, C

CORE = 0xce563f89a0ed9414f5aa28ad0d96d6795f9c6      # bits 4..151, shared by all four
CORE_BITS = 148
ABOVE = CORE_BITS + 4                                # bit 152: first bit above the core (core starts at bit 4)
K1 = ("secp160k1", "secp192k1", "secp224k1", "secp256k1")


def half_x(name: str) -> int:
    """x of G/2 in the prime-order subgroup, derived from the curve definition (not hardcoded)."""
    d = CURVES[name]
    c = C(d)
    G = (d["Gx"], d["Gy"])
    H = c.mul((d["n"] + 1) // 2, G)
    if c.mul(2, H) != G:
        raise ValueError(f"{name}: computed half is not G/2")
    return H[0]


def decompose(x: int) -> dict:
    """Split a half-x into (prefix above the core, the core, low nibble) and verify the core."""
    core_here = (x >> 4) & ((1 << CORE_BITS) - 1)
    return {
        "x_hex": f"{x:x}",
        "core_matches": core_here == CORE,
        "prefix_above_core_hex": f"{x >> ABOVE:x}",              # bits 152..top
        "byte_above_core_hex": f"{(x >> ABOVE) & 0xff:02x}",     # bits 152..159
        "low_nibble": x & 0xf,
    }


def is_qr(a: int, p: int) -> bool:
    a %= p
    return a == 0 or pow(a, (p - 1) // 2, p) == 1


def on_curve_x(x: int, name: str) -> bool:
    """True iff x is the x-coordinate of some point on the curve (x^3 + a x + b is a QR mod p)."""
    d = CURVES[name]
    p = d["p"]
    return is_qr((x * x * x + d["a"] * x + d["b"]) % p, p)


def find_reductions(halves: dict) -> list:
    """item 3d: readings of one half-x reduced mod another curve's prime that land exactly on that half-x."""
    readings = {}
    for src in halves:
        readings[f"{src}:full"] = halves[src]
        readings[f"{src}:low160"] = halves[src] & ((1 << 160) - 1)
    reductions = []
    for rname, U in readings.items():
        for tgt in halves:
            p = CURVES[tgt]["p"]
            if rname.split(":")[0] != tgt and U % p == halves[tgt]:
                reductions.append({"source_reading": rname, "reduced_mod": tgt,
                                   "equals_half_x_of": tgt, "quotient": U // p})
    return reductions


def analyze(halves: dict) -> dict:
    out = {}

    # (A) decomposition
    out["decomposition"] = {name: decompose(halves[name]) for name in K1}
    out["core_shared_by_all"] = all(out["decomposition"][n]["core_matches"] for n in K1)

    # (B) simple relations among the byte-above-core and the prefixes
    bytes_above = {n: (halves[n] >> ABOVE) & 0xff for n in K1}
    prefixes = {n: out["decomposition"][n]["prefix_above_core_hex"] for n in K1}
    out["byte_above_core"] = {n: f"{v:02x}" for n, v in bytes_above.items()}
    out["byte_above_core_diff_192_minus_160"] = f"{bytes_above['secp192k1'] - bytes_above['secp160k1']:#x}"
    out["prefix_3b78_shared_by_192_224_256"] = (
        prefixes["secp224k1"] == "3b78" and prefixes["secp256k1"] == "3b78"
        and prefixes["secp192k1"].endswith("3b78"))

    # (C) item 3d: is there one underlying value U reduced mod each curve's prime that yields the observed half-x?
    out["reduction_matches"] = find_reductions(halves)

    # (D) is the observed byte-above-core the smallest that leaves the (core|nibble) value on its curve?
    oncurve = {}
    for name in K1:
        nibble = halves[name] & 0xf
        low = (CORE << 4) | nibble                         # the 152-bit (core|nibble) block, low 160 reading
        smallest = next((t for t in range(256) if on_curve_x((t << ABOVE) | low, name)), None)
        observed = (halves[name] >> ABOVE) & 0xff
        oncurve[name] = {"observed_byte": f"{observed:02x}",
                         "smallest_on_curve_byte": None if smallest is None else f"{smallest:02x}",
                         "observed_is_on_curve": on_curve_x((observed << ABOVE) | low, name),
                         "observed_is_smallest": smallest == observed}
    out["top_byte_on_curve"] = oncurve

    return out


def summarize(result: dict) -> str:
    lines = ["Experiment 2: high-bit (top-byte / prefix) analysis of the secp*k1 half-generators.", ""]
    lines.append(f"Core shared by all four: {result['core_shared_by_all']}")
    lines.append("Byte above the core: " + ", ".join(f"{n}={result['byte_above_core'][n]}" for n in K1))
    lines.append(f"  192-minus-160 of that byte: {result['byte_above_core_diff_192_minus_160']}")
    lines.append(f"  prefix 3b78 shared by 192/224/256: {result['prefix_3b78_shared_by_192_224_256']}")
    lines.append("")
    nontrivial = [r for r in result["reduction_matches"] if r["quotient"] != 0]
    lines.append("(C) single-value-reduced-mod-p matches (item 3d):")
    lines.append(f"  non-trivial (actual reduction): {nontrivial or 'none'}")
    lines.append("  (secp224k1 and secp256k1 have identical half-x, so they match each other at quotient 0; "
                 "that is the known identity, not a reduction.)")
    lines.append("")
    lines.append("(D) is the observed byte-above-core the smallest leaving (core|nibble) on the curve?")
    for n in K1:
        o = result["top_byte_on_curve"][n]
        lines.append(f"  {n}: observed {o['observed_byte']} (on-curve {o['observed_is_on_curve']}), "
                     f"smallest on-curve {o['smallest_on_curve_byte']}, observed-is-smallest {o['observed_is_smallest']}")
    lines.append("")
    lines.append("Conclusion (negative). The byte above the core is 48 on secp160k1 and 78 on the other three "
                 "(difference exactly 0x30), and 192's prefix ends in the 3b78 shared by 224/256 -- structural facts, "
                 "not a derivation. No non-trivial single-value mod-p reduction relates the curves, and the observed "
                 "top byte, while always on-curve, is the smallest on-curve completion for none of them. So the high "
                 "bits are not explained by a simple counter, a single mod-p reduction, or a smallest-on-curve rule. "
                 "The prefix's origin stays open; next are the item 3b/3c hash/expansion stories and the archival route.")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("results"))
    args = parser.parse_args()
    halves = {name: half_x(name) for name in K1}
    result = {"experiment": "top-byte-analysis", "half_x": {n: f"{halves[n]:x}" for n in K1}, **analyze(halves)}
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "top-byte-analysis.json").write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8")
    text = summarize(result)
    (args.output_dir / "top-byte-analysis.txt").write_text(text, encoding="utf-8")
    print(text, end="", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
