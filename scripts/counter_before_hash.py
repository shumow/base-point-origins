"""Model the 'counter-before-hash' hypothesis for the secp160k1 top byte (HANDOFF
§4.2(b), §7.3.5). The idea: the half-generator constant is HASH(seed with a
counter folded into the INPUT), the counter incrementing until some acceptance
rule fires -- as opposed to the §7.3.3 test, which added a counter to the hash
OUTPUT. The question the name poses: can this explain why secp160k1's top byte
is 0x48 while the other three carry 0x78 over the identical low bits?

This script does three things, run from the repository root:

    python3 scripts/counter_before_hash.py            # model + demonstration
    python3 scripts/counter_before_hash.py --probe     # also run the bounded search

  A. The structural result. The four values share bits 4..155 exactly (152
     bits). If value = HASH(input), that forces one shared input, which forces
     the differing nibble at bits 156..159 (4 vs 7) to match too. So the top
     byte is NOT hash output under ANY counter-before-hash scheme; it is a
     post-hash edit. Proven, then shown by simulation: a per-curve acceptance
     loop yields statistically independent digests, nowhere near a shared core.

  B. The top nibble / high material as a post-hash counter: enumerated, and no
     single function of the field reproduces {160k1, 192k1, 224k1, 256k1}.

  C. --probe: a bounded counter-before-hash dictionary pass over the Certicom
     wordlist, sweeping a counter in the INPUT (the dimension §3/§4.1 did not),
     matched against the 148-bit core. Honestly scoped, with a manifest.

Pure standard library plus the repo's hash helpers.
"""
import argparse
import hashlib
import json
import os
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "k163"))
import high_bytes_analysis as hb          # noqa: E402  is_x, half_x
from secg_scan import CURVES, C           # noqa: E402
import secg_core_search as core           # noqa: E402  the 148-bit core matcher

K1 = ["secp160k1", "secp192k1", "secp224k1", "secp256k1"]

out_lines = []


def say(s=""):
    print(s)
    out_lines.append(s)


def window_156(v):
    """bits 4..155 (the 152-bit core) of a 160-bit value."""
    return (v >> 4) & ((1 << 152) - 1)


# --- counter-before-hash encoders: counter folded into the hashed input -----
def encoders(seed: bytes, i: int):
    """Ways a counter i can enter the hash input before hashing."""
    yield "suffix_be4", seed + struct.pack(">I", i)
    yield "suffix_be1", seed + bytes([i & 0xFF])
    yield "suffix_dec", seed + str(i).encode()
    yield "prefix_be4", struct.pack(">I", i) + seed
    yield "prefix_dec", str(i).encode() + seed
    # X9.62 'SEED + i' numeric style: add i to the seed read as an integer
    g = max(len(seed), 1)
    yield "seed_plus_i", ((int.from_bytes(seed, "big") + i) % (1 << (8 * g))).to_bytes(g, "big")


def main(do_probe):
    curves = {n: C(CURVES[n]) for n in K1}
    xs = {n: hb.half_x(curves[n]) for n in K1}
    cores = {n: window_156(xs[n] & ((1 << 160) - 1)) for n in K1}
    assert len(set(cores.values())) == 1, "precondition: the 152-bit core is shared"

    say("Counter-before-hash on the secp160k1 top byte (HANDOFF §4.2(b))")
    say("=" * 70)
    for n in K1:
        v = xs[n]
        say(f"  {n:10s} top nibble (bits156-159)={v >> 156 & 0xF}  high={(v >> 160):#x}  "
            f"low152 core={window_156(v & ((1 << 160) - 1)):x}")
    say()

    # ---- A. the structural result ----------------------------------------
    say("A. Structural result: the top byte cannot be hash output")
    say("   All four share bits 4..155 (152 bits). The differing part the name calls")
    say("   the 'top byte' is really the nibble at bits 156..159: 0x4 on secp160k1,")
    say("   0x7 on the other three (bits 152..155 = 0x8 are shared, inside the core).")
    say("   Let value_k = HASH(input_k) for curve k, input_k = seed with a counter")
    say("   folded in (any encoding above). A good hash makes bits 4..155 of its")
    say("   output a function of the whole input with full avalanche, so:")
    say("     bits 4..155 equal across all four  =>  input_k all equal (else a")
    say("     152-bit coincidence, probability ~2^-152 per pair), and equal input")
    say("     gives equal output EVERYWHERE, including bits 156..159.")
    say("   But bits 156..159 are 4 vs 7. Contradiction. Therefore under EVERY")
    say("   counter-before-hash scheme the differing nibble is a POST-hash edit;")
    say("   the counter-in-the-input can produce the shared digest, never the split.")
    say()

    # ---- A'. demonstration: no counter-before-hash outcome shows the signature
    say("A'. Demonstration: the observed signature never arises")
    say("    The observed signature is a PAIR of curves whose low 152 bits (bits 4..155)")
    say("    are equal WHILE the top nibble (bits 156..159) differs. Model: for each")
    say("    curve, i = 0,1,2,... ; D = SHA1(seed || i_be4); accept the first D that")
    say("    lifts to a point. Two outcomes are possible and neither is the signature:")
    say("    curves land on the same i (identical FULL digest, top nibble included), or")
    say("    on different i (independent digests). Count signature pairs across seeds.")
    import random
    rng = random.Random(42)
    seeds = [b"Certicom", b"secp", b"Koblitz", b"SEC2"] + \
            [bytes(rng.randrange(256) for _ in range(20)) for _ in range(60)]
    sig_pairs = 0
    total_pairs = 0
    for seed in seeds:
        accepted = {}
        for n in K1:
            c = curves[n]
            for i in range(100000):
                d = hashlib.sha1(seed + struct.pack(">I", i)).digest()
                if hb.is_x(c, int.from_bytes(d, "big") % c.p):
                    accepted[n] = int.from_bytes(d, "big")
                    break
        for a in K1:
            for b in K1:
                if a >= b:
                    continue
                total_pairs += 1
                va, vb = accepted[a] & ((1 << 160) - 1), accepted[b] & ((1 << 160) - 1)
                if window_156(va) == window_156(vb) and (va >> 156 & 0xF) != (vb >> 156 & 0xF):
                    sig_pairs += 1          # the observed signature
    say(f"    {len(seeds)} seeds, {total_pairs} curve-pairs examined.")
    say(f"    pairs matching the observed signature (shared 152-bit core, DIFFERENT top")
    say(f"    nibble) = {sig_pairs}.  (The real data has this on all three pairs within")
    say(f"    {{192,224,256}} and between them and 160k1 -- 5 of 6 pairs.)")
    say("    => counter-before-hash yields either an identical digest (same top nibble")
    say("       too) or an independent one; it never produces shared-low/split-top.")
    say()

    # ---- B. the top nibble / high material as a post-hash counter ---------
    say("B. If the edit is itself a counter/tag, does one rule fit all four?")
    tags = {n: (xs[n] >> 156) for n in K1}   # everything above the shared core
    for n in K1:
        say(f"    {n:10s} field {curves[n].p.bit_length():3d} bits, tag above bit156 = {tags[n]:#x}")
    say("    secp224k1 and secp256k1: identical tag 0x3b7 over DIFFERENT fields;")
    say("    secp192k1: 0x554123b7, the LARGEST tag over the SMALLEST of the three")
    say("    extended fields; secp160k1: 0x4, no high material. No monotone function")
    say("    of the field size, and no per-curve counter (224=256), produces this set.")
    say("    The tag tracks which curves reuse a value, not the field -- consistent")
    say("    with a hand-written limb, not a computed or counted one.")
    say()

    probe = None
    if do_probe:
        probe = run_probe()

    say("CONCLUSION")
    say("  Counter-before-hash is modelled and excluded as the SOURCE OF THE TOP BYTE:")
    say("  the shared 152-bit core forces a single hashed input, which cannot also")
    say("  yield a different top nibble. A counter in the input can only explain the")
    say("  shared digest; the 0x78->0x48 edit on secp160k1 (and the 0x3b / 0x554123b")
    say("  high material) is a post-hash step, matching the §7.3.7 'hand-assigned tag'")
    say("  reading. What remains genuinely untested is a counter before a SECOND hash")
    say("  or transform applied to the digest -- a different, more baroque hypothesis.")
    if probe is not None:
        say(f"  The bounded input-counter probe added {probe['evaluations']:,} evaluations "
            f"over the Certicom list: {len(probe['hits'])} hit(s).")
    return probe


# fast (OpenSSL) 160-bit hashes for the probe; pure-Python SHA-0 is left out for
# time. The structural result in A excludes the hypothesis regardless of the
# dictionary, so the probe only needs to sweep the input-counter dimension.
PROBE_HASHES = {
    "sha1": lambda b: hashlib.sha1(b).digest(),
    "ripemd160": lambda b: hashlib.new("ripemd160", b).digest(),
}


def run_probe():
    """C. Bounded counter-before-hash dictionary pass over the Certicom list."""
    say("C. Bounded probe: counter folded into the input, matched against the core")
    words = (ROOT / "wordlists" / "certicom.txt").read_text(
        encoding="utf-8", errors="ignore").splitlines()
    words = [w for w in words if w]
    COUNTER_MAX = 128
    ENCS = ("ascii", "utf-16-le")
    n = 0
    hits = []
    manifest_inputs = hashlib.sha256()
    for w in words:
        for enc in ENCS:
            try:
                seed = w.encode(enc)
            except Exception:
                continue
            for i in range(COUNTER_MAX):
                for ename, msg in encoders(seed, i):
                    manifest_inputs.update(msg)
                    for hname, hf in PROBE_HASHES.items():
                        d = hf(msg)
                        n += 1
                        m = core.check(d)
                        if m:
                            hit = dict(word=w, enc=enc, counter=i, placement=ename,
                                       algorithm=hname, match=m)
                            hits.append(hit)
                            say(f"    HIT {hit}")
    placements = [e for e, _ in encoders(b"x", 0)]
    manifest = dict(
        status="completed", wordlist="wordlists/certicom.txt", words=len(words),
        counter_range=[0, COUNTER_MAX - 1], encodings=list(ENCS),
        placements=placements, algorithms=list(PROBE_HASHES),
        matcher="secg_core_search.check (148-bit core, bits 4..151, + full 160-bit forms)",
        evaluations=n, hits=hits,
        input_sequence_sha256=manifest_inputs.hexdigest(),
        python_version=sys.version,
        note=("Bounded: base strings only (no case/punctuation variants), counter "
              "0..127, two encodings, six input placements, two OpenSSL 160-bit "
              "hashes (SHA-0 omitted for time). This sweeps the input-counter "
              "dimension omitted by §3/§4.1, not an exhaustive search; the "
              "structural result in A excludes the hypothesis independent of any "
              "dictionary."))
    say(f"    {n:,} evaluations over {len(words)} base strings, counter 0..{COUNTER_MAX-1}, "
        f"{len(ENCS)} encodings, {len(placements)} placements, {len(PROBE_HASHES)} hashes: "
        f"{len(hits)} hit(s).")
    (ROOT / "results" / "counter-before-hash-probe.json").write_text(
        json.dumps(manifest, indent=2) + "\n")
    say("    manifest -> results/counter-before-hash-probe.json")
    say()
    return manifest


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--probe", action="store_true", help="also run the bounded dictionary probe")
    ap.add_argument("--out", help="tee the report to a file")
    args = ap.parse_args()
    probe = main(args.probe)
    if args.out:
        Path(args.out).write_text("\n".join(out_lines) + "\n")
    sys.exit(0)
