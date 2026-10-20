"""Core-matched preimage search for the secp*k1 half-generator constant.
Tests whether bits 4..151 of any 160-bit digest (SHA-1, SHA-0, RIPEMD-160, doubled variants) of the k163 string set,
with the usual readings (as-is, byte-reversed, word-swapped) and X9.62-style counters, equal the shared 148-bit core
ce563f89a0ed9414f5aa28ad0d96d6795f9c6. Also tests the full secp224k1/256k1 value as the low 160 bits with top byte 78,
and the secp160k1 value 48ce...9c62 exactly."""
import hashlib, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent / "k163"))
from hashes import sha0
from strings import all_strings

CORE = 0xce563f89a0ed9414f5aa28ad0d96d6795f9c6          # bits 4..151 of every secp*k1 half x
MASK = (1 << 148) - 1
FULL = {0x48ce563f89a0ed9414f5aa28ad0d96d6795f9c62: "secp160k1 x(G/2)",
        0x78ce563f89a0ed9414f5aa28ad0d96d6795f9c63: "low 160 bits of secp224k1/256k1 x(G/2)",
        0x3b78ce563f89a0ed9414f5aa28ad0d96d6795f9c63 & ((1 << 160) - 1): "same"}

HASHES = {
    "sha1": lambda b: hashlib.sha1(b).digest(),
    "sha0": sha0,
    "ripemd160": lambda b: hashlib.new("ripemd160", b).digest(),
    "sha1(sha1)": lambda b: hashlib.sha1(hashlib.sha1(b).digest()).digest(),
    "sha1(md5)": lambda b: hashlib.sha1(hashlib.md5(b).digest()).digest(),
}
try: HASHES["ripemd160"](b"")
except Exception: del HASHES["ripemd160"]

def readings(d):
    yield "d", d
    yield "rev", d[::-1]
    yield "wswap", b"".join(d[i:i+4][::-1] for i in range(0, len(d), 4))

def check(d):
    for name, r in readings(d):
        v = int.from_bytes(r, "big")
        if (v >> 4) & MASK == CORE: return name + " core"
        if v in FULL: return name + " full"
    return None

def main():
    n = 0; hits = []
    for label, b in all_strings():
        for hname, hf in HASHES.items():
            for suffix in (b"",) + tuple(cb for c in range(4) for cb in (bytes([c]), str(c).encode(), c.to_bytes(4, "big"))):
                m = check(hf(b + suffix)); n += 1
                if m: hits.append((label, hname, suffix, m)); print("HIT", label, hname, suffix, m, flush=True)
    print(f"done: {n} evaluations, {len(hits)} hits")

if __name__ == "__main__":
    main()
