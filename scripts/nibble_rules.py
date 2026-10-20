"""Brute-force the last-nibble acceptance rule (HANDOFF §3.3 / plan step 2).
For each secp*k1 curve, the used half-point x is ...9c60 + i with i = 2, 6, 3, 3. For each candidate start nibble b
(x0 = ...9c60 + b, searching upward through x0, x0+1, ...) and a battery of boolean point properties, find the first x on
the curve satisfying the property, and report every (b, property) that reproduces the used i on all four curves.
Also tries downward searches and "take the k-th on-curve x" rules."""
import sys, itertools
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from secg_scan import CURVES, C

CORE = 0xce563f89a0ed9414f5aa28ad0d96d6795f9c6
BASES = {"secp160k1": 0x48ce563f89a0ed9414f5aa28ad0d96d6795f9c60, "secp192k1": 0x554123b78ce563f89a0ed9414f5aa28ad0d96d6795f9c60,
         "secp224k1": 0x3b78ce563f89a0ed9414f5aa28ad0d96d6795f9c60, "secp256k1": 0x3b78ce563f89a0ed9414f5aa28ad0d96d6795f9c60}
USED = {"secp160k1": 2, "secp192k1": 6, "secp224k1": 3, "secp256k1": 3}

def sqrt_mod(a, p):
    a %= p
    if pow(a, (p - 1) // 2, p) != 1: return None
    if p % 4 == 3: return pow(a, (p + 1) // 4, p)
    # Tonelli–Shanks
    q, s = p - 1, 0
    while q % 2 == 0: q //= 2; s += 1
    z = 2
    while pow(z, (p - 1) // 2, p) != p - 1: z += 1
    m, c, t, r = s, pow(z, q, p), pow(a, q, p), pow(a, (q + 1) // 2, p)
    while t != 1:
        i, t2 = 0, t
        while t2 != 1: t2 = t2 * t2 % p; i += 1
        b = pow(c, 1 << (m - i - 1), p); m, c, t, r = i, b * b % p, t * b * b % p, r * b % p
    return r

def features(c, x):
    """Return dict of boolean features for x on curve c, or None if not on curve."""
    p = c.p; rhs = (x**3 + c.a * x + c.b) % p; y = sqrt_mod(rhs, p)
    if y is None: return None
    ye, yo = (y, p - y) if y % 2 == 0 else (p - y, y)      # even root, odd root
    ylo, yhi = min(y, p - y), max(y, p - y)
    f = {}
    for tag, yy in (("ye", ye), ("yo", yo), ("ylo", ylo), ("yhi", yhi)):
        P = (x, yy); Q = c.add(P, P); x2, y2 = Q; T = c.add(Q, P)
        f[f"{tag}:y<p/2"] = yy < p / 2
        f[f"{tag}:y(2P)even"] = y2 % 2 == 0
        f[f"{tag}:y(2P)<p/2"] = y2 < p / 2
        f[f"{tag}:x(2P)even"] = x2 % 2 == 0
        f[f"{tag}:x(2P)<p/2"] = x2 < p / 2
        f[f"{tag}:x(2P)<x"] = x2 < x
        f[f"{tag}:x(2P)>x"] = x2 > x
        f[f"{tag}:y(3P)even"] = T[1] % 2 == 0
        f[f"{tag}:x(3P)even"] = T[0] % 2 == 0
        f[f"{tag}:yQR"] = pow(yy, (p - 1) // 2, p) == 1
        f[f"{tag}:y(2P)QR"] = pow(y2, (p - 1) // 2, p) == 1
        f[f"{tag}:x(2P)QR"] = pow(x2, (p - 1) // 2, p) == 1
        f[f"{tag}:y%4==1"] = yy % 4 == 1
        f[f"{tag}:y%4==3"] = yy % 4 == 3
        f[f"{tag}:y%3==0"] = yy % 3 == 0
        f[f"{tag}:y(2P)%3==0"] = y2 % 3 == 0
        f[f"{tag}:y>x"] = yy > x
        f[f"{tag}:y(2P)>x(2P)"] = y2 > x2
    f["on"] = True
    f["xQR"] = pow(x, (p - 1) // 2, p) == 1
    f["xNQR"] = not f["xQR"]
    f["rhsCube"] = pow(rhs, (p - 1) // 3, p) == 1 if p % 3 == 1 else True
    f["rhsNotCube"] = not f["rhsCube"]
    f["x%3==0"] = x % 3 == 0; f["x%3==1"] = x % 3 == 1; f["x%3==2"] = x % 3 == 2
    f["x%4==2"] = x % 4 == 2; f["x%4==3"] = x % 4 == 3
    f["x%5==?"] = False
    f["x+1 on"] = sqrt_mod((x + 1)**3 + c.a * (x + 1) + c.b, p) is not None
    f["x-1 on"] = sqrt_mod((x - 1)**3 + c.a * (x - 1) + c.b, p) is not None
    f["x+1 off"] = not f["x+1 on"]; f["x-1 off"] = not f["x-1 on"]
    f["y!=y(2P) parity"] = (ye % 2) != (c.add((x, ye), (x, ye))[1] % 2)
    return f

def main(used=None, span=48, pairs=True, verbose=True):
    """Returns the list of matching rules. `used` maps curve -> index of the x actually used (default: the published 2,6,3,3);
    tests plant a synthetic `used` to check the search finds a known rule."""
    USED_ = used or USED
    tables = {}
    def say(*a):
        if verbose: print(*a)
    for name in USED_:
        c = C(CURVES[name]); tables[name] = [features(c, BASES[name] + i) for i in range(-16, span)]
    names = list(USED_); keys = sorted({k for t in tables.values() for row in t if row for k in row})
    def first(name, b, key, direction=1, kth=1):
        t = tables[name]; i = b; hits = 0
        while -16 <= i < span:
            row = t[i + 16]
            if row and row.get(key, False):
                hits += 1
                if hits == kth: return i
            i += direction
        return None
    found = []
    for b in range(-16, 16):
        for key in keys:
            for direction in (1, -1):
                for kth in (1, 2, 3):
                    if all(first(n, b, key, direction, kth) == USED_[n] for n in names):
                        say(f"MATCH start={b:+d} dir={direction:+d} kth={kth} prop={key}"); found.append((b, direction, kth, key))
    # pairs of properties (conjunction), upward from start 0..3, first hit
    for b in (range(0, 4) if pairs else ()):
        for k1, k2 in itertools.combinations(keys, 2):
            def firstc(name):
                t = tables[name]
                for i in range(b, span):
                    row = t[i + 16]
                    if row and row.get(k1, False) and row.get(k2, False): return i
            if all(firstc(n) == USED_[n] for n in names):
                say(f"MATCH2 start={b} prop={k1} AND {k2}"); found.append((b, 1, 1, f"{k1} AND {k2}"))
    say("done, matches:", len(found))
    # dump the per-curve on-curve indices for reference
    for n in names:
        say(n, f"on-curve i in [-16,{span}):", [i - 16 for i, r in enumerate(tables[n]) if r])
    return found

if __name__ == "__main__":
    main()
