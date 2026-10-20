"""Emit hashcat target lists for the base-point constants.
secp*k1 core: all 2^12 completions of bits 4..151 (top byte x last nibble), in three readings -> 12,288 SHA-1 targets (mode 100).
K-163: the 126-bit value with all four settings of the top two bits -> 4 MD5 targets (mode 0).
usage: python3 make_targets.py outdir"""
import sys, os
CORE = 0xce563f89a0ed9414f5aa28ad0d96d6795f9c6
K163 = 0x23e21d6019e1211f6bd47ec180256e97
out = sys.argv[1] if len(sys.argv) > 1 else "targets"; os.makedirs(out, exist_ok=True)
def readings(b):
    yield b
    yield b[::-1]
    yield b"".join(b[i:i+4][::-1] for i in range(0, len(b), 4))
seen = set()
with open(f"{out}/secp_core_sha1.txt", "w") as f:
    for top in range(256):
        for low in range(16):
            v = (top << 152) | (CORE << 4) | low
            for r in readings(v.to_bytes(20, "big")):
                h = r.hex()
                if h not in seen: seen.add(h); f.write(h + "\n")
with open(f"{out}/k163_md5.txt", "w") as f:
    for top in range(4):
        f.write(((top << 126) | K163).to_bytes(16, "big").hex() + "\n")
print(f"wrote {len(seen)} SHA-1 targets and 4 MD5 targets to {out}/")
# self-check: the published secp224k1/256k1 and secp160k1 160-bit values must be in the SHA-1 list
assert "3b78ce563f89a0ed9414f5aa28ad0d96d6795f9c63"[-40:] in seen and "48ce563f89a0ed9414f5aa28ad0d96d6795f9c62" in seen
