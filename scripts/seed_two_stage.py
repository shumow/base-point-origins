"""Model stage 2 hashing the SEED, with candidate seeds (HANDOFF §4.2(b), the
branch §7.3.9 could not test).

§7.3.9 tested the two-stage construction with stage 2 hashing the DIGEST V (known)
and found nothing. The branch it could not reach: stage 2 hashes the unknown SEED,

    low 160 bits = V      = H1(seed)                 # stage 1
    high limb    = g(H2(seed, counter))              # stage 2, on the SEED

With a candidate seed in hand both stages become checkable at once. A seed only
counts if it does BOTH: produce V at stage 1 AND a high limb at stage 2. Stage 1
alone is the §3.2/§4.1 dictionary search, already 0 hits over the Certicom and
NIST corpora; this harness re-runs it jointly with stage 2 so a seed that passed
only one stage is never mistaken for a solution.

This is a BOUNDED search: a fixed candidate corpus (the Certicom wordlist and the
six curves' own parameters), a fixed set of hashes, placements, counters and
32-bit readings. A negative says no seed in that domain fits; it does not exclude
the construction for seeds, hashes or counters outside it.

Every hit is reported as a byte-exact witness: the seed bytes (input_hex), the
stage-1 hash and suffix, the stage-2 hash, placement, reading and counter and the
exact bytes hashed, so a positive can be reproduced from the report alone.

Candidate seeds: the Certicom wordlist (the established corpus) and the six
curves' own parameters. Run from the repository root:

    python3 scripts/seed_two_stage.py                 # joint + unified, base strings
    python3 scripts/seed_two_stage.py --out FILE

Three models are checked per seed:
  * JOINT    : H1(seed||s) gives V's core (stage 1) AND g(H2(seed||i)) a high limb.
  * UNIFIED  : the whole value (0x3b78..9c63 etc.) is a windowed slice of one wide
               hash of the seed -- stages 1 and 2 collapsed into a single hash.
  * STAGE2   : high limb alone, reported only to quantify its spurious rate.
"""
import argparse
import hashlib
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "k163"))
import secg_core_search as core            # noqa: E402  stage-1 (seed -> V core) matcher
import counter_second_hash as cs           # noqa: E402  word_readings, T32 high limbs
from secg_scan import CURVES, C            # noqa: E402

# full published values, for the unified single-hash-window model
FULL = {
    "secp160k1": 0x48ce563f89a0ed9414f5aa28ad0d96d6795f9c62,
    "secp192k1": 0x554123b78ce563f89a0ed9414f5aa28ad0d96d6795f9c66,
    "secp224k1": 0x3b78ce563f89a0ed9414f5aa28ad0d96d6795f9c63,
    "secp256k1": 0x3b78ce563f89a0ed9414f5aa28ad0d96d6795f9c63,
}

H1 = core.HASHES                 # stage-1 family (160-bit: sha1, sha0, ripemd160, doubles)
H2 = {                           # stage-2 family (fast)
    "sha1": lambda b: hashlib.sha1(b).digest(),
    "md5": lambda b: hashlib.md5(b).digest(),
    "ripemd160": lambda b: hashlib.new("ripemd160", b).digest(),
    "sha1(sha1)": lambda b: hashlib.sha1(hashlib.sha1(b).digest()).digest(),
}
WIDE = {                         # wide hashes for the unified window model
    "sha256": lambda b: hashlib.sha256(b).digest(),
    "sha512": lambda b: hashlib.sha512(b).digest(),
    "sha1||sha1(x||1)": lambda b: hashlib.sha1(b).digest() + hashlib.sha1(b + b"\x01").digest(),
}
DEFAULT_COUNTER_MAX = 256
DEFAULT_ENCS = ("ascii", "utf-16-le")

out_lines = []


def say(s=""):
    print(s)
    out_lines.append(s)


def stage1_suffixes():
    # X9.62-style: bare, and a small counter added before the hash (seed||i / seed+i)
    return core.SUFFIXES


def stage2_inputs(seed: bytes, i: int):
    """(placement name, bytes hashed) for a counter i folded into the seed."""
    yield "seed||be4", seed + struct.pack(">I", i)
    yield "seed||be1", seed + bytes([i & 0xFF])
    yield "seed||dec", seed + str(i).encode()
    yield "be4||seed", struct.pack(">I", i) + seed


def windows(digest: int, dbits: int, width: int):
    """All bit-offset windows of `width` bits inside a dbits-bit digest."""
    for off in range(0, dbits - width + 1):
        yield off, (digest >> off) & ((1 << width) - 1)


def candidate_seeds():
    """(label, text) candidate seeds: the Certicom wordlist + curve parameters."""
    wl = ROOT / "wordlists" / "certicom.txt"
    for line in wl.read_text(encoding="utf-8", errors="ignore").splitlines():
        if line:
            yield ("wl", line)
    for name in FULL:
        c = C(CURVES[name])
        yield (name + ".p", "%x" % c.p)
        yield (name + ".n", "%x" % c.n)
        yield (name + ".p_dec", str(c.p))
        yield (name + ".n_dec", str(c.n))


def main(seeds=None, counter_max=DEFAULT_COUNTER_MAX, encs=DEFAULT_ENCS):
    """Run the joint search. `seeds` is an iterable of (label, text) and defaults to
    candidate_seeds(); tests pass a planted one. Returns a dict with the witness
    lists stage1_hits, stage2_hits, joint_hits, unified_hits and the check counts.
    Each witness carries label, text, enc and input_hex (the exact seed bytes),
    plus the stage's hash / suffix or placement / reading / counter / bytes hashed."""
    say("Stage-2-hashes-the-seed, with candidate seeds (HANDOFF §4.2(b))")
    say("=" * 70)
    say("A seed counts only if it clears BOTH stages. Stage 1 (seed -> V) is the")
    say("§3.2/§4.1 search, already 0 hits over these corpora; it is re-run here")
    say("jointly with stage 2 so no half-match is mistaken for a hit.")
    say(f"stage-1 hashes: {list(H1)}   suffixes: {len(stage1_suffixes())} (X9.62-style)")
    say(f"stage-2 hashes: {list(H2)}   placements: {[p for p, _ in stage2_inputs(b'x', 0)]}   "
        f"counters: 0..{counter_max - 1}   high limbs: {[hex(t) for t in cs.T32]}")
    say(f"wide hashes (unified): {list(WIDE)}   encodings: {list(encs)}")
    say()

    s1_hits, s2_hits, joint_hits, uni_hits = [], [], [], []
    n1 = n2 = nu = 0
    nseeds = 0

    for label, text in (seeds if seeds is not None else candidate_seeds()):
        for enc in encs:
            try:
                seed = text.encode(enc)
            except Exception:
                continue
            nseeds += 1
            w0 = dict(label=label, text=text, enc=enc, input_hex=seed.hex())

            # --- stage 1: does this seed hash to V's core? ---
            s1_here = []
            for suf in stage1_suffixes():
                for hn, hf in H1.items():
                    n1 += 1
                    m = core.check(hf(seed + suf))
                    if m:
                        s1_here.append(dict(w0, stage=1, hash=hn, suffix_hex=suf.hex(),
                                            msg_hex=(seed + suf).hex(), reading=m))
                        say(f"  STAGE1 HIT {s1_here[-1]}")
            s1_hits.extend(s1_here)

            # --- stage 2: does this seed (||counter) give a high limb? ---
            s2_here = []
            for i in range(counter_max):
                for pname, msg in stage2_inputs(seed, i):
                    for hn, hf in H2.items():
                        d = hf(msg)
                        for rname, w in cs.word_readings(d):
                            n2 += 1
                            if w in cs.T32:
                                s2_here.append(dict(w0, stage=2, hash=hn, placement=pname,
                                                    reading=rname, counter=i,
                                                    limb=f"{w:#010x}", msg_hex=msg.hex()))
            s2_hits.extend(s2_here)

            # --- joint: same seed clears both ---
            if s1_here and s2_here:
                joint_hits.append(dict(w0, stage1=s1_here, stage2=s2_here))
                say(f"  JOINT HIT input_hex={seed.hex()} label={label} text={text!r} enc={enc}")
                for h in s1_here:
                    say(f"    stage 1: {h['hash']} suffix_hex={h['suffix_hex']!r} "
                        f"msg_hex={h['msg_hex']} -> {h['reading']}")
                for h in s2_here:
                    say(f"    stage 2: {h['hash']} placement={h['placement']} reading={h['reading']} "
                        f"counter={h['counter']} msg_hex={h['msg_hex']} -> limb {h['limb']}")

            # --- unified: the whole value is a window of one wide hash ---
            for hn, hf in WIDE.items():
                d = hf(seed)
                dbits = len(d) * 8
                dint = int.from_bytes(d, "big")
                for cname, val in FULL.items():
                    width = val.bit_length()
                    for off, w in windows(dint, dbits, width):
                        nu += 1
                        if w == val:
                            uni_hits.append(dict(w0, hash=hn, curve=cname, offset=off,
                                                 width=width, digest_hex=d.hex()))
                            say(f"  UNIFIED HIT {uni_hits[-1]}")

    say()
    say(f"candidate seed-encodings: {nseeds}")
    say(f"stage-1 checks {n1:,} -> {len(s1_hits)} hit(s)  (expected 0; matches §4.1)")
    say(f"stage-2 checks {n2:,} -> {len(s2_hits)} high-limb hit(s)")
    say(f"unified  checks {nu:,} -> {len(uni_hits)} hit(s)")
    say(f"JOINT (same seed clears both stages): {len(joint_hits)} hit(s)")
    say()

    # read the stage-2 count correctly: both targets are full 32-bit limbs
    say("Reading the stage-2 count: the limbs are matched as full 32-bit words,")
    say("0x0000003b (224/256k1, 26 leading zero bits) and 0x0554123b (192k1), each a")
    say(f"~2^-32 event; {n2:,} checks give ~{n2 / 2**32:.2f} expected spurious per target.")
    say("So stage 2 is itself discriminating here, not a 1-in-64 nibble match, and a")
    say("hit would carry weight -- but it is only evidence on a seed that ALSO clears")
    say("stage 1 (a JOINT hit). A narrower low-6-bit reading of 0x3b was deliberately")
    say("not used: at 1/64 it would carry no information.")
    n_3b = sum(1 for h in s2_hits if h["limb"] == "0x0000003b")
    n_554 = sum(1 for h in s2_hits if h["limb"] == "0x0554123b")
    say(f"    of {len(s2_hits)} stage-2 hits: {n_3b} are 0x0000003b, {n_554} are 0x0554123b.")
    say()

    say("CONCLUSION")
    if joint_hits:
        say(f"  {len(joint_hits)} candidate seed(s) clear BOTH stages -- a real lead; byte-exact witnesses above.")
    elif uni_hits:
        say(f"  {len(uni_hits)} seed(s) reproduce a full value as a single wide-hash window -- verify (witnesses above).")
    else:
        say("  No candidate seed clears both stages, and no seed reproduces a full value")
        say("  as a window of one wide hash. This is a bounded negative over an explicit")
        say(f"  domain: {nseeds} seed-encodings (the Certicom wordlist and the curves' p and n,")
        say(f"  encodings {list(encs)}), stage-1 hashes {list(H1)} with the X9.62-style")
        say(f"  suffixes, stage-2 hashes {list(H2)}, four placements, counters below")
        say(f"  {counter_max}, 32-bit readings, and wide hashes {list(WIDE)}. It says nothing")
        say("  about seeds outside that corpus, other hashes, or larger counters. Stage 1")
        say("  alone is 0 hits here, as in §4.1. Together with §7.3.8 and §7.3.9 the")
        say("  seed-input two-stage construction is unsupported in every domain tested so")
        say("  far; the working hypothesis for the high material stays hand-assigned tags")
        say("  (§7.3.7), which these searches do not establish either.")
    return dict(stage1_hits=s1_hits, stage2_hits=s2_hits, unified_hits=uni_hits,
                joint_hits=joint_hits, seeds=nseeds, n1=n1, n2=n2, nu=nu)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", help="tee the report to a file")
    args = ap.parse_args()
    main()
    if args.out:
        Path(args.out).write_text("\n".join(out_lines) + "\n")
    sys.exit(0)
