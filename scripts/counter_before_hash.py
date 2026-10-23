"""Model the 'counter-before-hash' hypothesis for the secp160k1 top byte (HANDOFF
§4.2(b), §7.3.5). The idea: the half-generator constant is HASH(seed with a
counter folded into the INPUT), the counter incrementing until some acceptance
rule fires -- as opposed to the §7.3.3 test, which added a counter to the hash
OUTPUT. The question the name poses: can this explain why secp160k1's top byte
is 0x48 while the other three carry 0x78 over the identical low bits?

This script does three things, run from the repository root:

    python3 scripts/counter_before_hash.py            # model + demonstration
    python3 scripts/counter_before_hash.py --probe     # also run the bounded search

  A. The heuristic argument. The four values share bits 4..155 exactly (152
     bits). If value = HASH(input), then under an independent-hash heuristic two
     different inputs agree on 152 bits with probability ~2^-152, so the four
     almost certainly share one hashed input, and one input gives one output
     everywhere -- including bits 156..159, which differ (4 vs 7). The likely
     reading is a post-hash edit. This is probabilistic, not a proof: a 152-bit
     projection is many-to-one and nothing makes it injective. A small
     simulation of per-curve acceptance loops illustrates it; it cannot
     establish impossibility.

  B. The top nibble / high material as a post-hash counter or tag: enumerated;
     no monotone function of the field size reproduces {160k1, 192k1, 224k1,
     256k1}, and 224 = 256 disfavours a free-running per-curve counter (a
     counter restarted per run, or reused buffer state, would repeat and is
     not excluded).

  C. --probe: a bounded counter-before-hash dictionary pass over the Certicom
     wordlist, sweeping a counter in the INPUT (the dimension §3/§4.1 did not),
     matched against the core. Its domain is explicit and recorded in a
     manifest; it is a negative over that domain only, independent of A.

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
    say("A. Heuristic argument: the top nibble is unlikely to be hash output")
    say("   All four share bits 4..155 (152 bits). The differing part the name calls")
    say("   the 'top byte' is really the nibble at bits 156..159: 0x4 on secp160k1,")
    say("   0x7 on the other three (bits 152..155 = 0x8 are shared, inside the core).")
    say("   Let value_k = HASH(input_k) for curve k, input_k = seed with a counter")
    say("   folded in (any encoding above). Projection onto 152 bits is many-to-one,")
    say("   so equal projections do NOT prove equal inputs. But under an")
    say("   independent-hash heuristic two different inputs agree on bits 4..155 with")
    say("   probability ~2^-152 per pair, so with overwhelming likelihood the four")
    say("   share one hashed input -- and one input gives one output everywhere,")
    say("   including bits 156..159, which are 4 vs 7. The likely reading: the")
    say("   differing nibble is a post-hash edit, and a counter in the input, if there")
    say("   was one, produced only the shared digest. This is a probabilistic")
    say("   heuristic, not a proof, and it is separate from the bounded probe in C.")
    say()

    # ---- A'. illustration: the signature does not arise in a sample of runs
    say("A'. Illustration (a sample, not an impossibility result)")
    say("    The observed signature is a PAIR of curves whose low 152 bits (bits 4..155)")
    say("    are equal WHILE the top nibble (bits 156..159) differs. Model: for each")
    say("    curve, i = 0,1,2,... ; D = SHA1(seed || i_be4); accept the first D that")
    say("    lifts to a point. The two outcomes seen are: curves land on the same i")
    say("    (identical FULL digest, top nibble included), or on different i")
    say("    (independent digests). Count signature pairs across seeds.")
    M160 = (1 << 160) - 1
    real_pairs = sum(1 for a in K1 for b in K1 if a < b
                     and window_156(xs[a] & M160) == window_156(xs[b] & M160)
                     and (xs[a] >> 156 & 0xF) != (xs[b] >> 156 & 0xF))
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
    say(f"    nibble) = {sig_pairs}.  (The real data shows it on {real_pairs} of 6 pairs:")
    say("    secp160k1 against each of the other three; the pairs among 192/224/256")
    say("    share the top nibble 7 as well as the core, so they are not the signature.)")
    say("    => in this sample, counter-before-hash yields either an identical digest")
    say("       (same top nibble too) or an independent one. A sample of 64 seeds")
    say("       illustrates the heuristic in A; it does not rule the signature out.")
    say()

    # ---- B. the top nibble / high material as a post-hash counter ---------
    say("B. If the edit is itself a counter/tag, does one rule fit all four?")
    tags = {n: (xs[n] >> 156) for n in K1}   # everything above the shared core
    for n in K1:
        say(f"    {n:10s} field {curves[n].p.bit_length():3d} bits, tag above bit156 = {tags[n]:#x}")
    say("    secp224k1 and secp256k1: identical tag 0x3b7 over DIFFERENT fields;")
    say("    secp192k1: 0x554123b7, the LARGEST tag over the SMALLEST of the three")
    say("    extended fields; secp160k1: 0x4, no high material. No monotone function")
    say("    of the field size produces this set, and 224 = 256 disfavours a")
    say("    free-running per-curve counter. Not excluded: a counter restarted for")
    say("    each run, or buffer state reused between runs, either of which repeats.")
    say("    The tag tracks which curves reuse a value, not the field -- consistent")
    say("    with a hand-written limb, which stays the working hypothesis.")
    say()

    probe = None
    if do_probe:
        probe = run_probe()

    say("CONCLUSION")
    say("  Counter-before-hash as the SOURCE OF THE TOP BYTE is disfavoured, not")
    say("  disproved: under the independent-hash heuristic the shared 152-bit core")
    say("  points to a single hashed input, which would give one top nibble, so the")
    say("  0x78->0x48 edit on secp160k1 (and the 0x3b / 0x554123b high material) most")
    say("  likely happened after the hash -- consistent with the §7.3.7 working")
    say("  hypothesis of hand-assigned tags, which this does not establish. A counter")
    say("  in the input could still explain the shared digest itself. Separately,")
    say("  the bounded probe below is a negative over its stated domain only.")
    say("  Untested here: a counter before a SECOND hash or transform of the digest")
    say("  (modelled next, counter_second_hash.py) and any input outside the probe.")
    if probe is not None:
        say(f"  The bounded input-counter probe: {probe['evaluations']:,} evaluations over "
            f"{probe['words']} Certicom base strings, counter 0..{probe['counter_range'][1]}, "
            f"{len(probe['encodings'])} encodings, {len(probe['placements'])} placements, "
            f"hashes {probe['algorithms']}: {len(probe['hits'])} hit(s) on the core.")
    return probe


# fast (OpenSSL) 160-bit hashes for the probe; pure-Python SHA-0 is left out for
# time. The probe is a bounded negative over exactly the domain in its manifest;
# it stands on its own and does not rely on the heuristic in A.
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
              "dimension omitted by §3/§4.1; it is a negative over this domain "
              "only, not an exhaustive search and not a proof about inputs "
              "outside it."))
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
