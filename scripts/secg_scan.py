"""Short-coordinate scan of the SEC 2 prime-field generators not already covered by the NIST/ANSI sweep.
k*G for 2 <= k <= 2^16 and G/k for 2 <= k <= 2^12 (subgroup inverse); every cofactor preimage of G where h > 1.
Reports the shortest x and the shortest y (min(y, p-y)) found, and anything >= 32 bits short of the field."""
import json, sys

CURVES = {
 "secp112r1": dict(p=0xDB7C2ABF62E35E668076BEAD208B, a=0xDB7C2ABF62E35E668076BEAD2088, b=0x659EF8BA043916EEDE8911702B22,
                   Gx=0x09487239995A5EE76B55F9C2F098, Gy=0xA89CE5AF8724C0A23E0E0FF77500, n=0xDB7C2ABF62E35E7628DFAC6561C5, h=1),
 "secp112r2": dict(p=0xDB7C2ABF62E35E668076BEAD208B, a=0x6127C24C05F38A0AAAF65C0EF02C, b=0x51DEF1815DB5ED74FCC34C85D709,
                   Gx=0x4BA30AB5E892B4E1649DD0928643, Gy=0xADCD46F5882E3747DEF36E956E97, n=0x36DF0AAFD8B8D7597CA10520D04B, h=4),
 "secp128r1": dict(p=0xFFFFFFFDFFFFFFFFFFFFFFFFFFFFFFFF, a=0xFFFFFFFDFFFFFFFFFFFFFFFFFFFFFFFC, b=0xE87579C11079F43DD824993C2CEE5ED3,
                   Gx=0x161FF7528B899B2D0C28607CA52C5B86, Gy=0xCF5AC8395BAFEB13C02DA292DDED7A83, n=0xFFFFFFFE0000000075A30D1B9038A115, h=1),
 "secp128r2": dict(p=0xFFFFFFFDFFFFFFFFFFFFFFFFFFFFFFFF, a=0xD6031998D1B3BBFEBF59CC9BBFF9AEE1, b=0x5EEEFCA380D02919DC2C6558BB6D8A5D,
                   Gx=0x7B6AA5D85E572983E6FB32A7CDEBC140, Gy=0x27B6916A894D3AEE7106FE805FC34B44, n=0x3FFFFFFF7FFFFFFFBE0024720613B5A3, h=4),
 "secp160k1": dict(p=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFAC73, a=0, b=7,
                   Gx=0x3B4C382CE37AA192A4019E763036F4F5DD4D7EBB, Gy=0x938CF935318FDCED6BC28286531733C3F03C4FEE, n=0x0100000000000000000001B8FA16DFAB9ACA16B6B3, h=1),
 "secp160r1": dict(p=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF7FFFFFFF, a=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF7FFFFFFC, b=0x1C97BEFC54BD7A8B65ACF89F81D4D4ADC565FA45,
                   Gx=0x4A96B5688EF573284664698968C38BB913CBFC82, Gy=0x23A628553168947D59DCC912042351377AC5FB32, n=0x0100000000000000000001F4C8F927AED3CA752257, h=1),
 "secp160r2": dict(p=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFAC73, a=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFAC70, b=0xB4E134D3FB59EB8BAB57274904664D5AF50388BA,
                   Gx=0x52DCB034293A117E1F4FF11B30F7199D3144CE6D, Gy=0xFEAFFEF2E331F296E071FA0DF9982CFEA7D43F2E, n=0x0100000000000000000000351EE786A818F3A1A16B, h=1),
 "secp192k1": dict(p=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFEE37, a=0, b=3,
                   Gx=0xDB4FF10EC057E9AE26B07D0280B7F4341DA5D1B1EAE06C7D, Gy=0x9B2F2F6D9C5628A7844163D015BE86344082AA88D95E2F9D, n=0xFFFFFFFFFFFFFFFFFFFFFFFE26F2FC170F69466A74DEFD8D, h=1),
 "secp224k1": dict(p=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFE56D, a=0, b=5,
                   Gx=0xA1455B334DF099DF30FC28A169A467E9E47075A90F7E650EB6B7A45C, Gy=0x7E089FED7FBA344282CAFBD6F7E319F7C0B0BD59E2CA4BDB556D61A5,
                   n=0x010000000000000000000000000001DCE8D2EC6184CAF0A971769FB1F7, h=1),
 "secp256k1": dict(p=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F, a=0, b=7,
                   Gx=0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798, Gy=0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8,
                   n=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141, h=1),
}

class C:
    def __init__(s, d): s.__dict__.update(d)
    def on(s, P): x, y = P; return (y * y - x**3 - s.a * x - s.b) % s.p == 0
    def add(s, P, Q):
        if P is None: return Q
        if Q is None: return P
        x1, y1 = P; x2, y2 = Q; p = s.p
        if x1 == x2:
            if (y1 + y2) % p == 0: return None
            l = (3 * x1 * x1 + s.a) * pow(2 * y1, -1, p) % p
        else: l = (y2 - y1) * pow(x2 - x1, -1, p) % p
        x3 = (l * l - x1 - x2) % p; return (x3, (l * (x1 - x3) - y1) % p)
    def mul(s, k, P):
        R = None
        while k:
            if k & 1: R = s.add(R, P)
            P = s.add(P, P); k >>= 1
        return R

K, KD = 2**16, 2**12
out = {}
for name, d in CURVES.items():
    c = C(d); p, n, h = c.p, c.n, c.h; m = p.bit_length(); G = (c.Gx, c.Gy)
    assert c.on(G), name; assert c.mul(n, G) is None, name
    # order of the full group is h*n; check with a random-ish point? skip; n*G = O suffices for the subgroup.
    thr = m - 32; bestx = (m + 1, ""); besty = (m + 1, ""); found = []
    def rec(P, lab):
        global bestx, besty
        x, y = P; bx = x.bit_length(); by = min(y, p - y).bit_length()
        if bx < bestx[0]: bestx = (bx, lab)
        if by < besty[0]: besty = (by, lab)
        if bx <= thr or by <= thr: found.append(f"{lab}: x {bx} bits, y {by} bits, x={x:x}")
    Q = G
    for k in range(2, K + 1):
        Q = c.add(Q, G); rec(Q, f"{k}*G")
    for k in range(2, KD + 1):
        rec(c.mul(pow(k, -1, n), G), f"G/{k}")
    half = c.mul((n + 1) // 2, G)
    pre = []
    if h > 1:
        # cofactor preimages: Q + T for T in E[h]; find a point of order h by h-th roots... use x-search: points P with n*P != O and n*h*P==O.
        # For h = 4: full group order 4n; find T of order dividing 4 as (hn/4)... simpler: scan small x for a point, multiply by n to land in E[h].
        Qh = c.mul(pow(h, -1, n), G); tors = set()
        x = 0
        while len(tors) < h and x < 5000:
            rhs = (x**3 + c.a * x + c.b) % p
            if p % 4 == 3:
                y = pow(rhs, (p + 1) // 4, p)
                if y * y % p == rhs:
                    T = c.mul(n, (x, y)); R = T
                    for _ in range(h):
                        tors.add(R); R = c.add(R, T)
                        if R is None: break
            x += 1
        tors = [t for t in tors if t is None or c.mul(h, t) is None]
        for T in set(tors):
            R = c.add(Qh, T) if T is not None else Qh
            assert c.mul(h, R) == G
            pre.append((R[0].bit_length(), f"{R[0]:x}"))
    out[name] = dict(bits=m, h=h, half_x_bits=half[0].bit_length(), half_x=f"{half[0]:x}", shortest_x=bestx, shortest_y=besty,
                     found=found, cofactor_preimage_x_bits=sorted(b for b, _ in pre), rough_expected_min=m - 17)
    print(name, "m=%d h=%d  G/2 x: %d bits  shortest x: %d at %s  shortest y: %d at %s  found: %s  preimages: %s" %
          (m, h, half[0].bit_length(), bestx[0], bestx[1], besty[0], besty[1], found or "none", sorted(b for b, _ in pre)), flush=True)
json.dump(out, open("secg_scan.json", "w"), indent=1)
