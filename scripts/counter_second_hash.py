"""Model the counter-before-SECOND-hash variant for the secp*k1 high material
(HANDOFF §4.2(b), the one branch §7.3.8 left open).

§7.3.8 excluded a counter folded into the hash that produces the shared block
V = 78ce563f89a0ed9414f5aa28ad0d96d6795f9c6? : sharing 152 bits forces one input,
so the counter cannot also split the top nibble. That theorem does NOT cover a
TWO-STAGE construction:

    low 160 bits = V = H1(seed)                      # counter-free, so V stays shared
    high material = g(H2(digest, counter))           # a second hash/transform, per curve

Here the counter never touches H1, so V can be identical across curves while the
high words differ. And because the second stage operates on the DIGEST (which we
have: V), the model is directly testable without knowing the seed.

The observed high words, as 32-bit limbs above V:
    secp224k1 = secp256k1 : 0x0000003b
    secp192k1             : 0x0554123b   (28 bits)
    secp160k1             : none (top byte of V cleared 0x78->0x48 instead)

Run from the repository root:
    python3 scripts/counter_second_hash.py                 # transforms + fast-hash sweep
    python3 scripts/counter_second_hash.py --slow          # also pure-Python hashes
    python3 scripts/counter_second_hash.py --out FILE
"""
import argparse
import hashlib
import struct
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "k163"))
from hashes import md4, sha0, ripemd128, ripemd160_best  # noqa: E402

# V in 20 bytes, top byte 0x78; the last nibble is soft, so test a few forms.
V_FORMS = {
    "V(..c60)": 0x78ce563f89a0ed9414f5aa28ad0d96d6795f9c60,
    "V(..c63)": 0x78ce563f89a0ed9414f5aa28ad0d96d6795f9c63,   # 224/256 low 160
    "V(..c66)": 0x78ce563f89a0ed9414f5aa28ad0d96d6795f9c66,   # 192 low 160
}
# targets: the high 32-bit limb above V, and the 28-bit bare form for 192.
T32 = {0x0000003b: "secp224k1/256k1 high limb", 0x0554123b: "secp192k1 high limb"}
T28 = {0x554123b: "secp192k1 high (28-bit)", 0x3b: "secp224k1/256k1 high (6-bit)"}

out_lines = []


def say(s=""):
    print(s)
    out_lines.append(s)


# --- second-stage hashes H2 (fast = OpenSSL; slow = pure Python) -------------
FAST_H2 = {
    "sha1": lambda b: hashlib.sha1(b).digest(),
    "md5": lambda b: hashlib.md5(b).digest(),
    "ripemd160": ripemd160_best,
    "sha256": lambda b: hashlib.sha256(b).digest(),
    "sha1(sha1)": lambda b: hashlib.sha1(hashlib.sha1(b).digest()).digest(),
    "sha1(md5)": lambda b: hashlib.sha1(hashlib.md5(b).digest()).digest(),
}
SLOW_H2 = {"sha0": sha0, "md4": md4, "ripemd128": ripemd128}


def word_readings(d):
    """32-bit windows of a digest d: each big-endian word, each byte-swapped
    word, the top and bottom 32 bits, and the whole digest mod 2^32."""
    for i in range(0, len(d) - 3, 4):
        w = int.from_bytes(d[i:i + 4], "big")
        yield f"be_word{i // 4}", w
        yield f"le_word{i // 4}", int.from_bytes(d[i:i + 4], "little")
    whole = int.from_bytes(d, "big")
    yield "top32", whole >> (len(d) * 8 - 32)
    yield "low32", whole & 0xFFFFFFFF


def counter_inputs(vbytes, i):
    """Ways a counter enters the SECOND hash's input (which is the digest)."""
    yield "V||be4", vbytes + struct.pack(">I", i)
    yield "V||be1", vbytes + bytes([i & 0xFF])
    yield "V||dec", vbytes + str(i).encode()
    yield "be4||V", struct.pack(">I", i) + vbytes
    yield "i_only", struct.pack(">I", i)          # second hash of just the counter


def transforms_no_counter(vbytes):
    """Plain transforms of the digest, no counter -- the cheapest 'or transform'."""
    whole = int.from_bytes(vbytes, "big")
    words = [int.from_bytes(vbytes[i:i + 4], "big") for i in range(0, 20, 4)]
    yield "crc32", zlib.crc32(vbytes)
    yield "crc32_le", zlib.crc32(vbytes[::-1])
    yield "adler32", zlib.adler32(vbytes)
    yield "sum_words_mod32", sum(words) & 0xFFFFFFFF
    yield "xor_words", words[0] ^ words[1] ^ words[2] ^ words[3] ^ words[4]
    yield "top32", whole >> 128
    yield "low32", whole & 0xFFFFFFFF


def main(do_slow):
    say("Counter-before-second-hash model for the secp*k1 high material (§4.2(b))")
    say("=" * 72)
    say("Stage 1 gives the shared V; the counter lives only in stage 2, so V stays")
    say("shared and §7.3.8 does not apply. Stage 2 operates on the digest V (known),")
    say("so the model is testable. Targets (high 32-bit limb above V):")
    for t, who in T32.items():
        say(f"    {t:#010x}  {who}")
    say()

    hits = []

    # ---- A. plain transforms of the digest, no counter -------------------
    say("A. Plain transforms of V (no counter): CRC32, Adler32, word sum/xor, slices")
    for vname, v in V_FORMS.items():
        vbytes = v.to_bytes(20, "big")
        for tname, val in transforms_no_counter(vbytes):
            if val in T32:
                hits.append(("transform", vname, tname, None, f"{val:#010x}", T32[val]))
                say(f"    HIT {vname} {tname} = {val:#010x}  ({T32[val]})")
    say(f"    checked {len(V_FORMS)} forms x 7 transforms; {len(hits)} hit(s) so far.")
    say()

    # ---- B. second hash of the digest, no counter ------------------------
    say("B. Windows of H2(V) with no counter (is the limb a slice of a re-hash?)")
    H2 = dict(FAST_H2)
    if do_slow:
        H2.update(SLOW_H2)
    nB = 0
    for vname, v in V_FORMS.items():
        vbytes = v.to_bytes(20, "big")
        for hname, hf in H2.items():
            d = hf(vbytes)
            for rname, w in word_readings(d):
                nB += 1
                if w in T32:
                    hits.append(("H2(V)", vname, hname, rname, f"{w:#010x}", T32[w]))
                    say(f"    HIT {vname} {hname} {rname} = {w:#010x}  ({T32[w]})")
    say(f"    {nB:,} window checks over {len(H2)} hashes; "
        f"{sum(1 for h in hits if h[0] == 'H2(V)')} limb hit(s).")
    say()

    # ---- C. counter before the second hash -------------------------------
    say("C. Counter before the second hash: windows of H2(enc(V, i)), small i,")
    say("   for each V form (the 192k1 limb sits above V(..c66), the 224/256 limb above V(..c63))")
    FAST_N, SLOW_N = 1 << 16, 1 << 12
    found32 = {t: [] for t in T32}      # (hash, enc, reading, counter, V form) producing each 32-bit limb
    nC = 0
    for vname, v in V_FORMS.items():
        vbytes = v.to_bytes(20, "big")
        for hname, hf in H2.items():
            N = SLOW_N if hname in SLOW_H2 else FAST_N
            for i in range(N):
                for ename, msg in counter_inputs(vbytes, i):
                    d = hf(msg)
                    for rname, w in word_readings(d):
                        nC += 1
                        if w in T32:
                            found32[w].append((hname, ename, rname, i, vname))
    say(f"    {nC:,} window checks over {len(V_FORMS)} V forms (fast hashes to i<{FAST_N}, "
        f"{'slow to i<%d' % SLOW_N if do_slow else 'slow hashes off'}).")
    for t, who in T32.items():
        lst = found32[t]
        if not lst:
            say(f"    {t:#010x} ({who}): no small-counter second-hash window produces it.")
        else:
            say(f"    {t:#010x} ({who}): {len(lst)} window(s), smallest e.g. {lst[0]}")
    # joint test: one (hash,enc,reading) giving BOTH limbs at small counters
    say("    Joint recipe (one hash+enc+reading yielding both 0x0000003b and 0x0554123b):")
    joint = []
    by_recipe = {}
    for t in T32:
        for (hname, ename, rname, i, vname) in found32[t]:
            by_recipe.setdefault((hname, ename, rname), {}).setdefault(t, (i, vname))
    for recipe, d in by_recipe.items():
        if len(d) == len(T32):
            joint.append((recipe, d))
            say(f"      CANDIDATE {recipe}: counters {d}")
    if not joint:
        say("      none: no single second-hash recipe reproduces both limbs at small i.")
    say()

    # ---- D. honest limits ------------------------------------------------
    say("D. Limits of this test")
    say("    * If stage 2 hashes the SEED (not the digest), its input is unknown and")
    say("      this cannot test it; only the digest-input form is checkable.")
    say("    * The limb is 6 bits (224/256) or 28-32 bits (192). A 6-bit target is")
    say("      met by ~1/64 of counters, so a 0x3b match alone means nothing; a 32-bit")
    say("      match (0x0000003b, 0x0554123b) at a SMALL counter would be meaningful.")
    say("    * A large counter could match any 32-bit target by luck (~1 per 2^32); a")
    say("      bounded sweep tests the small-counter regime a real recipe would use,")
    say("      not impossibility.")
    say("    * Step inversion (scripts/sha1_steps.py) needs a full 160-bit target to")
    say("      run backwards; we observe only a 6-32 bit limb, so it does not apply.")
    say()

    say("CONCLUSION")
    wide_hits = [h for h in hits if h[-1] and "6-bit" not in str(h)]
    if joint:
        say("  A single second-hash recipe reproduces BOTH high limbs at small counters")
        say("  (see CANDIDATE above) -- a real lead; verify the seed/stage-1 side.")
    elif wide_hits:
        say("  A plain transform or re-hash window equals a high limb (see HIT above) --")
        say("  check whether it also fits the other curves before believing it.")
    else:
        say("  No plain transform of V, no window of H2(V), and no small-counter second")
        say("  hash H2(V||i) reproduces the 32-bit high limbs 0x0000003b / 0x0554123b,")
        say("  and no single recipe yields both. The counter-before-second-hash variant")
        say("  is not supported in the digest-input, small-counter regime. With §7.3.8")
        say("  (counter in stage 1) already excluded, the high material still reads as a")
        say("  hand-assigned tag (§7.3.7), not a computed one. Only the seed-input form")
        say("  of stage 2 remains beyond reach.")
    return hits, joint


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--slow", action="store_true", help="also sweep pure-Python hashes (to i<2^12)")
    ap.add_argument("--out", help="tee the report to a file")
    args = ap.parse_args()
    main(args.slow)
    if args.out:
        Path(args.out).write_text("\n".join(out_lines) + "\n")
    sys.exit(0)
