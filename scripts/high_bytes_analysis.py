"""Characterize the high-order material of the four secp*k1 x(G/2) values (HANDOFF §4.2).

The four half-generators share a 160-bit block V = 0x78ce563f...9c6? in their
low bits.  Above bit 160 they carry different small "high material", and
secp160k1 alone has the top byte of its 160-bit block reduced from 0x78 to
0x48.  This script pins the structure down and tests every hypothesis in
HANDOFF §4.2 for where the high material and the top byte come from, under the
hard constraint that a single source must yield 0x48 on secp160k1 and 0x78 on
the other three.

Run from the repository root:  python3 scripts/high_bytes_analysis.py
Writes nothing itself; `--out FILE` tees the report.  Pure standard library.

Nothing here assumes the core is a hash; §3.2/§4.1 already exhausted the
dictionary angle.  The point is the *arithmetic* of the high bytes.
"""
import hashlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from secg_scan import CURVES, C    # noqa: E402  prime-field curve arithmetic

K1 = ["secp160k1", "secp192k1", "secp224k1", "secp256k1"]

out_lines = []


def say(s=""):
    print(s)
    out_lines.append(s)


def half_x(c):
    G = (c.Gx, c.Gy)
    assert c.mul(c.n, G) is None, "n*G != O"
    H = c.mul((c.n + 1) // 2, G)
    assert c.add(H, H) == G, "2*(G/2) != G"
    return H[0]


def is_x(c, x):
    """Does x lift to an affine point on c?"""
    if not (0 <= x < c.p):
        return False
    rhs = (x ** 3 + c.a * x + c.b) % c.p
    return rhs == 0 or pow(rhs, (c.p - 1) // 2, c.p) == 1


def main():
    curves = {n: C(CURVES[n]) for n in K1}
    xs = {n: half_x(curves[n]) for n in K1}

    say("secp*k1 half-generators x(G/2), recomputed from the published G:")
    for n in K1:
        say(f"  {n:10s} {xs[n]:x}   ({xs[n].bit_length()} of {curves[n].p.bit_length()} bits)")
    say()

    # ---- 1. exact decomposition ------------------------------------------
    say("1. Exact structure")
    MASK160 = (1 << 160) - 1
    low160 = {n: xs[n] & MASK160 for n in K1}
    high = {n: xs[n] >> 160 for n in K1}           # material above bit 160
    topbyte = {n: (low160[n] >> 152) & 0xFF for n in K1}   # byte 19 (bits 152-159)
    core = {n: (low160[n] >> 4) & ((1 << 152) - 1) for n in K1}  # bits 4..155
    lastnib = {n: xs[n] & 0xF for n in K1}

    same_core = len(set(core.values())) == 1
    say(f"  152-bit core (bits 4..155) identical on all four: {same_core}  ({core['secp256k1']:x})")
    say(f"  top byte of the 160-bit block (bits 152..159): " +
        ", ".join(f"{n[4:]}={topbyte[n]:#04x}" for n in K1))
    say(f"  material above bit 160:                        " +
        ", ".join(f"{n[4:]}={high[n]:#x}" for n in K1))
    say(f"  last nibble (bits 0..3):                       " +
        ", ".join(f"{n[4:]}={lastnib[n]}" for n in K1))
    # the shared 160-bit value V with top byte normalised to 0x78 and last nibble 0
    V = {n: (low160[n] & ~(0xFF << 152) & ~0xF) | (0x78 << 152) for n in K1}
    say(f"  normalise top byte->0x78, last nibble->0: all four give the same 160-bit V: "
        f"{len(set(V.values())) == 1}")
    say(f"      V = {V['secp256k1']:x}")
    say("  => one 160-bit block V shared by all four; 192/224/256 prepend high")
    say("     material, 160k1 instead clears 0x30 from V's top byte. 224k1 and 256k1")
    say("     are byte-for-byte identical (same V, same high 0x3b, same last nibble 3).")
    say()

    # ---- 2. the 192k1 anomaly: longer prefix, smaller field --------------
    say("2. The ordering obstruction (kills every truncate-one-constant story)")
    for n in K1:
        say(f"  {n:10s} field {curves[n].p.bit_length():3d} bits, high material {high[n].bit_length():2d} bits "
            f"({high[n]:#x})")
    say("  secp192k1 carries MORE high material (27 bits) than secp224k1/secp256k1")
    say("  (6 bits) over a SMALLER field. So the four are not low windows of one long")
    say("  constant truncated to field size, nor a byte stream read longer for bigger")
    say("  fields. Any generator must explain why the 192-bit curve got the most.")
    say()

    # ---- 3. FIPS 186 / X9.62 field-element expansion ---------------------
    say("3. FIPS 186 / X9.62 'verifiably random' field-element expansion")
    say("   Expansion of a seed S to a t-bit field element F(S,t):")
    say("     H0 = SHA1(S); W0 = rightmost (t-160*floor((t-1)/160)) bits of H0;")
    say("     Wi = SHA1(S+i); F = W0 || W1 || ... (W0 most significant).")
    say("   Prediction that MATCHES the data: for t in {192,224,256}, s=1, so the")
    say("   low 160 bits of F are W1 = SHA1(S+1) -- a block common to those three,")
    say("   exactly as 192/224/256 share V in their low 160 bits.")
    say("   Prediction that FAILS: the high field is the rightmost h bits of H0=SHA1(S),")
    say("   a full-weight hash slice; observed high material is tiny.")
    h_bits = {"secp192k1": 32, "secp224k1": 64, "secp256k1": 96}
    for n, h in h_bits.items():
        say(f"     {n}: h={h} -> expect ~{h}-bit random high field; observed {high[n]:#x} "
            f"({high[n].bit_length()} bits).")
    # the shared-seed contradiction, proven by arithmetic, no seed needed
    say("   Single-seed contradiction (192 vs 224): a common S would force")
    say(f"     rightmost 32 bits of H0 = {high['secp192k1']:#x}  and")
    say(f"     rightmost 64 bits of H0 = {high['secp224k1']:#x};")
    low32_of_h0 = high["secp192k1"] & 0xFFFFFFFF
    low32_from_224 = high["secp224k1"] & 0xFFFFFFFF
    say(f"     but rightmost 64 bits already fix rightmost 32 bits = {low32_from_224:#x} "
        f"!= {low32_of_h0:#x}. Contradiction.")
    # weight argument
    say("   Weight: a SHA-1 slice equalling a 6-bit value needs ~58 leading zero bits")
    say("   (probability ~2^-58); the high material is not hash output.")
    say("   => X9.62/FIPS expansion is excluded. (Confirms §7.3.2 by a second route;")
    say("      its matching low-160 prediction is why the idea looked plausible.)")
    say()

    # ---- 4. the top byte 0x78 -> 0x48 on secp160k1 -----------------------
    say("4. The secp160k1 top-byte reduction 0x78 -> 0x48")
    say(f"   0x78 - 0x48 = {0x78 - 0x48:#x};  0x78 ^ 0x48 = {0x78 ^ 0x48:#x};  "
        f"0x78 & ~0x30 = {0x78 & ~0x30:#x} (clear bits 4,5).")
    # not forced by the field: 0x78ce... is far below p160, so no reduction mod p
    c160 = curves["secp160k1"]
    unflipped = (xs["secp160k1"] & ~(0xFF << 152)) | (0x78 << 152)  # 160k1 value with 0x78 top byte
    say(f"   0x78-topped value = {unflipped:x}")
    say(f"   it is < p(secp160k1): {unflipped < c160.p}  (so no reduction mod p forces 0x48)")
    say(f"   its bit length {unflipped.bit_length()} == 0x48 value's bit length "
        f"{xs['secp160k1'].bit_length()}: {unflipped.bit_length() == xs['secp160k1'].bit_length()} "
        "(so not a bit-length mask either)")
    # functional test: which low nibbles lift, for each top byte, on secp160k1
    say("   On-curve lift test on secp160k1 (does the value lift to a point? any point")
    say("   has order n here, h=1, so any lift is a legal x(G/2)):")
    for tb in (0x48, 0x78):
        base = (xs["secp160k1"] & ~(0xFF << 152) & ~0xF) | (tb << 152)
        lifts = [d for d in range(16) if is_x(c160, base + d)]
        say(f"     top byte {tb:#04x}: low nibbles that lift = {lifts}"
            + ("  <- includes the published nibble 2" if 2 in lifts else ""))
    say("   Reading: both top bytes admit on-curve points, so 0x48 was not forced by")
    say("   lifting, by reduction mod p, or by bit length. No field-level cause found;")
    say("   a deliberate 2-bit edit to V's top byte on the one curve without high")
    say("   material is the simplest reading, not an established one.")
    say()

    # ---- 5. high material vs curve parameters & counters -----------------
    say("5. Is the high material a counter, date, or function of the curve parameters?")
    say(f"   values in generation-size order: 160k1->(none), 224k1->{high['secp224k1']:#x}, "
        f"256k1->{high['secp256k1']:#x}, 192k1->{high['secp192k1']:#x}")
    say("   224k1 and 256k1 share the SAME high byte 0x3b (and the same V): reuse, not a")
    say("   per-curve counter. 192k1's 0x554123b ends in 0x3b too, with 0x55412 above it.")
    say("   So 0x3b is a shared constant on three curves; 0x55412 is extra on 192k1 only.")
    # compare 0x3b and 0x55412 / 0x554123b to parameter-derived quantities
    say("   Candidate sources for 0x3b = %d and 0x554123b = %d / 0x55412 = %d:"
        % (0x3b, 0x554123b, 0x55412))
    for n in K1:
        c = curves[n]
        f = c.p.bit_length()
        pref = {
            "p mod 2^32": c.p & 0xFFFFFFFF,
            "n mod 2^32": c.n & 0xFFFFFFFF,
            "2^f - p (Mersenne offset)": (1 << f) - c.p,
            "p+1-n (trace)": c.p + 1 - c.n,
            "b": c.b,
        }
        say(f"     {n}: " + ", ".join(f"{k}={v:#x}" for k, v in pref.items()
                                      if v < (1 << 40)))
    say("   None of 0x3b, 0x55412, 0x554123b equals any curve's Mersenne offset,")
    say("   low word of p or n, trace, or b (see the table). As a Unix time 0x554123b")
    say("   = 89,395,771 s is 31 Oct 1972, not 1997-2000. So: not a Unix date, not a")
    say("   free-running per-curve counter (224 = 256), and not one of the five raw")
    say("   parameter quantities tried. Arbitrary other functions of p or n are not")
    say("   excluded by this -- only those five.")
    say()

    # ---- 6. structured-hash check (seeded from the curve's own numbers) --
    say("6. Is V (or a full value) a hash of the curve's own p or n?")
    targets = set()
    for n in K1:
        targets.add(V[n] & MASK160)
        targets.add(xs[n])
        targets.add(xs[n] & MASK160)
    hits = []
    algos = {"sha1": lambda b: hashlib.sha1(b).digest(),
             "md5": lambda b: hashlib.md5(b).digest(),
             "sha256": lambda b: hashlib.sha256(b).digest()}
    for n in K1:
        c = curves[n]
        flen = (c.p.bit_length() + 7) // 8
        encs = {
            "p_be": c.p.to_bytes(flen, "big"),
            "n_be": c.n.to_bytes((c.n.bit_length() + 7) // 8, "big"),
            "p_dec": str(c.p).encode(),
            "n_dec": str(c.n).encode(),
            "p_hex": ("%x" % c.p).encode(),
            "n_hex": ("%x" % c.n).encode(),
        }
        for ename, eb in encs.items():
            for aname, fn in algos.items():
                d = fn(eb)
                for width in (160, 128):
                    for off in (0, len(d) * 8 - width):
                        if off < 0:
                            continue
                        val = (int.from_bytes(d, "big") >> off) & ((1 << width) - 1)
                        if val in targets:
                            hits.append((n, ename, aname, width, off, "%x" % val))
    say(f"   {len(algos)} algorithms x {6} encodings x 4 curves, 160/128-bit windows,")
    say(f"   top and bottom alignment, matched against V and the full values: "
        f"{len(hits)} hit(s).")
    for hrow in hits:
        say(f"     HIT {hrow}")
    say()

    # ---- 7. the 32-bit-word / leftover-buffer reading (4.2(d)) -----------
    say("7. The 32-bit-word layout, and the 'uninitialised top limb' reading")
    say("   Big-endian 32-bit words (word0 = most significant):")
    for n in K1:
        nbytes = ((xs[n].bit_length() + 31) // 32) * 4
        words = [(xs[n] >> (8 * (nbytes - 4 - 4 * i))) & 0xFFFFFFFF
                 for i in range(nbytes // 4)]
        say(f"     {n:10s} " + " ".join(f"{w:08x}" for w in words))
    say("   The low five words are the block [78ce563f 89a0ed94 14f5aa28 ad0d96d6")
    say("   795f9c6?]; the sixth word is 0x0000003b (224/256), 0x0554123b (192), or")
    say("   absent (160k1, whose top word's high byte is 0x48 not 0x78).")
    say("   If the sixth word were uninitialised buffer or a free-running counter it")
    say("   would be expected to differ between runs; instead secp224k1 and secp256k1")
    say("   carry the identical 0x3b and share it as the low byte of secp192k1's word.")
    say("   That disfavours leftover or free-running values. It does not exclude a")
    say("   counter restarted for each run, or buffer state reused between runs, both")
    say("   of which would repeat too; a value assigned by hand is the simplest reading.")
    say()

    # ---- summary ---------------------------------------------------------
    say("SUMMARY")
    say("  * One 160-bit block V = 78ce563f89a0ed9414f5aa28ad0d96d6795f9c6? underlies all")
    say("    four; its middle 152 bits are fixed, its top and bottom nibbles are soft.")
    say("  * secp224k1 and secp256k1 are byte-identical at x(G/2): V, high byte 0x3b,")
    say("    last nibble 3. A chosen x reused verbatim across two fields.")
    say("  * The high material above V is 0x3b on 192/224/256 (0x55412 extra on 192) and")
    say("    absent on 160k1, which instead has 0x30 cleared from V's top byte.")
    say("  * Excluded exactly: FIPS/X9.62 field-element expansion from one seed (the")
    say("    single-seed contradiction, plus the weight argument) and truncation of one")
    say("    long constant to field size (192 carries more prefix than 224/256).")
    say("  * Disfavoured or tested only in a bounded form: a free-running per-curve")
    say("    counter or leftover buffer (224 = 256 repeats; a restarted counter or")
    say("    reused buffer state would too), a Unix date, the five raw parameter")
    say("    quantities tried (not arbitrary functions of p or n), and SHA-1/MD5/SHA-256")
    say("    of p or n in six encodings.")
    say("  * The top-byte 0x30 clear on 160k1 is not forced by the field; a deliberate")
    say("    2-bit edit is the simplest reading.")
    say("  * Working hypothesis, not a result: the high bytes are small hand-assigned")
    say("    tags written into the top limb of a fixed-width buffer holding V. 0x3b")
    say("    (=';'=59) shared by three curves is the sub-constant most worth identifying.")

    failures = []
    if not same_core:
        failures.append("core not shared")
    if len(set(V.values())) != 1:
        failures.append("V not shared")
    if hits:
        failures.append("unexpected hash hit (investigate, not a failure of structure)")
    return failures


if __name__ == "__main__":
    args = sys.argv[1:]
    outpath = None
    if "--out" in args:
        outpath = args[args.index("--out") + 1]
    fails = main()
    if outpath:
        with open(outpath, "w") as fh:
            fh.write("\n".join(out_lines) + "\n")
    # exit 0 even on the hash "hit" note: section 6 is exploratory, not a control
    sys.exit(1 if any(f for f in fails if "hash hit" not in f) else 0)
