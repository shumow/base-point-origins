"""Re-check, in pure Python, everything asserted by the 2019 investigation as
reconstructed in references/crypto2019-rump/halve_generators.sage (Oct 2026
mailbox survey), and tighten two statements the repository had made loosely.

Run from the repository root:  python3 scripts/verify_crypto2019.py

Sections
  1. x(G/2) on the four secp*k1 curves equals the 2019 values.
  2. The shared core is bits 4..155 (152 bits, `8ce563f...9c6`): only the top
     nibble (4 vs 7) and the last nibble (2, 6, 3, 3) vary. HANDOFF/record
     call it a 148-bit core (bits 4..151) and say the top *byte* varies; the
     byte is 48 vs 78, so its low nibble is shared too. The 2019 "256
     variants" John the Ripper list (top and bottom nibble) matches the
     152-bit core; the repo's 12,288-target hashcat list (top byte and bottom
     nibble) is a superset, one nibble looser.
  3. Dan Brown's "160-bit value + small counter, keep the first x that lifts"
     theory (H3 in the survey): counting up from a cleared low nibble / low 6
     bits / low byte, counting down, and varying the top nibble instead.
  4. secp256r1 control: x(G/2) is full size.
  5. sect163k1 (K-163): x(G/2) in the prime-order subgroup is 126 bits.
  6. Travis Scholl's derivation (email, 27 Oct 2019): p = 2^256 - 2^32 - 977 is
     the largest prime below 2^256 - 2^32 - 1 for which some j = 0 curve
     y^2 = x^3 + b has prime order, and that order is secp256k1's n.
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import binpts                      # noqa: E402  GF(2^m) curve arithmetic
from secg_scan import CURVES, C    # noqa: E402  prime-field curve arithmetic

EXPECTED_2019 = {
    "secp160k1": 0x48ce563f89a0ed9414f5aa28ad0d96d6795f9c62,
    "secp192k1": 0x554123b78ce563f89a0ed9414f5aa28ad0d96d6795f9c66,
    "secp224k1": 0x3b78ce563f89a0ed9414f5aa28ad0d96d6795f9c63,
    "secp256k1": 0x3b78ce563f89a0ed9414f5aa28ad0d96d6795f9c63,
}
K1 = list(EXPECTED_2019)
failures = []


def check(cond, msg):
    print(("  ok   " if cond else "  FAIL ") + msg)
    if not cond:
        failures.append(msg)


def half(c, G):
    H = c.mul((c.n + 1) // 2, G)
    assert c.add(H, H) == G
    return H


def is_x(c, x):
    rhs = (x**3 + c.a * x + c.b) % c.p
    return rhs == 0 or pow(rhs, (c.p - 1) // 2, c.p) == 1


# ---- 1. the half-generators ------------------------------------------------
print("1. x(G/2) on the secp*k1 curves")
curves, xs = {}, {}
for name in K1:
    c = C(CURVES[name]); curves[name] = c
    assert c.mul(c.n, (c.Gx, c.Gy)) is None
    x = half(c, (c.Gx, c.Gy))[0]; xs[name] = x
    check(x == EXPECTED_2019[name], f"{name}: {x:x} ({x.bit_length()} of {c.p.bit_length()} bits)")

# ---- 2. exactly what is shared --------------------------------------------
print("2. the shared core")
low160 = {n: xs[n] & ((1 << 160) - 1) for n in K1}
cores = {(v >> 4) & ((1 << 152) - 1) for v in low160.values()}
core = cores.pop() if len(cores) == 1 else None
check(core == 0x8ce563f89a0ed9414f5aa28ad0d96d6795f9c6,
      f"bits 4..155 (152 bits, 38 nibbles) agree on all four: {core:x}" if core else "bits 4..155 differ")
check({v >> 156 for v in low160.values()} == {4, 7}, "top nibble of the 160-bit block is 4 (160k1) or 7 (others)")
check([v & 15 for v in low160.values()] == [2, 6, 3, 3], "last nibbles 2, 6, 3, 3")
a, b, c_ = xs["secp160k1"], xs["secp192k1"], xs["secp224k1"]
check(c_ - a == 0x3b3 * 2**156 + 1, "224/256k1 value - 160k1 value = 0x3b3 * 2^156 + 1  (record.md 7.3.2 says 2^152: typo)")
check(b - c_ == 0x55412 * 2**168 + 3, "192k1 value - 224/256k1 value = 0x55412 * 2^168 + 3  (record.md 7.3.2 says 2^172: typo)")
print("     2019 JtR list: top and bottom nibble varied -> 16*16 = 256 digests, matches a 152-bit core;")
print("     repo make_targets.py: top byte and bottom nibble -> 4096 per reading, one nibble looser (superset).")

# ---- 3. Dan Brown's counter theory ----------------------------------------
print("3. 'core + small counter, keep the first x that lifts' (H3)")
for name in K1:
    c, x = curves[name], xs[name]
    for k in (4, 6, 8):
        base = x - (x % 2**k)
        valid = [d for d in range(2**k) if is_x(c, base + d)]
        down = [d for d in range(2**k - 1, -1, -1) if is_x(c, base + d)]
        print(f"     {name} low {k} bits: actual {x % 2**k:>3}, counting up first valid {valid[0]:>3} "
              f"(first few {valid[:5]}), counting down first valid {down[0]:>3}")
        check(valid[0] != x % 2**k, f"{name}: count-up over the low {k} bits does not pick the actual value")
    # vary the top nibble of the 160-bit block instead (bits 156..159), low bits fixed
    top_fixed_rest = x & ~(0xF << 156)
    lifts = [t for t in range(16) if is_x(c, top_fixed_rest | (t << 156))]
    print(f"     {name} top nibble of the 160-bit block: actual {x >> 156 & 15}, nibbles that lift {lifts}")

# ---- 4. control -------------------------------------------------------------
print("4. secp256r1 control")
p256 = C(dict(p=0xFFFFFFFF00000001000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFF, a=-3,
              b=0x5AC635D8AA3A93E7B3EBBD55769886BC651D06B0CC53B0F63BCE3C3E27D2604B,
              Gx=0x6B17D1F2E12C4247F8BCE6E563A440F277037D812DEB33A0F4A13945D898C296,
              Gy=0x4FE342E2FE1A7F9B8EE7EB4A7C0F9E162BCE33576B315ECECBB6406837BF51F5,
              n=0xFFFFFFFF00000000FFFFFFFFFFFFFFFFBCE6FAADA7179E84F3B9CAC2FC632551, h=1))
xr = half(p256, (p256.Gx, p256.Gy))[0]
check(xr.bit_length() == 254, f"x(G/2) on secp256r1 has {xr.bit_length()} bits: {xr:x}")

# ---- 5. sect163k1 -----------------------------------------------------------
print("5. sect163k1 / K-163")
m = 163
K163 = binpts.Curve(m, binpts.poly_from(m, [7, 6, 3, 0]), 1, 1, 0x04000000000000000000020108A2E0CC0D99F8A5EF, 2)
G2 = (0x02FE13C0537BBC11ACAA07D793DE4E6D5E5C94EEE8, 0x0289070FB05D38FF58321F2E800536D538CCDAA3D9)
assert K163.on(G2) and K163.mul(K163.n, G2) is None
H2 = K163.mul((K163.n + 1) // 2, G2); assert K163.add(H2, H2) == G2
check(H2[0] == 0x23e21d6019e1211f6bd47ec180256e97 and H2[0].bit_length() == 126,
      f"x(G/2) = {H2[0]:x} ({H2[0].bit_length()} of 163 bits)")

# ---- 6. Travis Scholl's derivation of the secp256k1 prime -----------------
print("6. the secp256k1 field prime via CM (Scholl, 27 Oct 2019)")


def is_prime(n, rounds=32):
    if n < 2: return False
    for q in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37):
        if n % q == 0: return n == q
    d, s = n - 1, 0
    while d % 2 == 0: d //= 2; s += 1
    rng = random.Random(2019)
    for _ in range(rounds):
        a = rng.randrange(2, n - 1); y = pow(a, d, n)
        if y in (1, n - 1): continue
        for _ in range(s - 1):
            y = y * y % n
            if y == n - 1: break
        else: return False
    return True


def sqrt_mod(a, p):  # Tonelli-Shanks
    a %= p
    if pow(a, (p - 1) // 2, p) != 1: return None
    if p % 4 == 3: return pow(a, (p + 1) // 4, p)
    q, s = p - 1, 0
    while q % 2 == 0: q //= 2; s += 1
    z = 2
    while pow(z, (p - 1) // 2, p) != p - 1: z += 1
    M, c, t, R = s, pow(z, q, p), pow(a, q, p), pow(a, (q + 1) // 2, p)
    while t != 1:
        i, tt = 0, t
        while tt != 1: tt = tt * tt % p; i += 1
        b = pow(c, 1 << (M - i - 1), p)
        M, c, t, R = i, b * b % p, t * b * b % p, R * b % p
    return R


def cornacchia(p):  # a^2 + 3 b^2 = p, exists iff p = 1 mod 3
    r = sqrt_mod(-3, p)
    if r is None: return None
    for r0 in (r, p - r):
        x, y = p, r0
        while y * y > p: x, y = y, x % y
        rem = p - y * y
        if rem % 3 == 0:
            bb = rem // 3; b = math.isqrt(bb)
            if b * b == bb: return y, b
    return None


lo_, hi_ = 2**256 - 2**32 - 977, 2**256 - 2**32
hits = []
for p in range(lo_ | 1, hi_, 2):
    if p % 3 != 1 or not is_prime(p): continue
    ab = cornacchia(p); assert ab is not None
    a_, b_ = ab; assert a_ * a_ + 3 * b_ * b_ == p
    # the six twists of y^2 = x^3 + b over F_p have orders p + 1 - t, t = +-2a, +-(a + 3b), +-(a - 3b)
    for t in (2 * a_, -2 * a_, a_ + 3 * b_, -(a_ + 3 * b_), a_ - 3 * b_, -(a_ - 3 * b_)):
        N = p + 1 - t
        if is_prime(N): hits.append((p, N))
check(hits == [(curves["secp256k1"].p, curves["secp256k1"].n)],
      "the only (p, prime order) pair with 2^256-2^32-977 <= p < 2^256-2^32 is secp256k1's (p, n)")

print()
print("ALL OK" if not failures else f"{len(failures)} FAILURE(S): " + "; ".join(failures))
sys.exit(1 if failures else 0)
