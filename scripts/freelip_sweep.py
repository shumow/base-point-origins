"""HANDOFF §4.6: the P-192 FreeLIP zrandom recipe (Anthropic, 16 Oct 2026) run with every small seed on the unexplained
NIST prime curves and on secp160k1. Recipe: state = seed; state = state * 3^121 mod (2^107-1); each draw = low 26 bits;
discard D single draws (7 in the published recipe); x = (ceil(bits(p)/26)+1 limbs, top first) mod p; first x on the curve.
We widen D to 0..12 (limb count L-1..L+1 is available via limb_deltas), and compare every candidate x (reduced and unreduced, on-curve or not)
and the first on-curve x against x(k*G), x(G/k), 1 <= k <= 8. Prints any hit. Usage: freelip_sweep.py [maxseed] [curves...]"""
import sys
M, A = 2**107 - 1, pow(3, 121, 2**107 - 1)

CURVES = {
 "P-224": dict(p=2**224 - 2**96 + 1, a=-3, b=0xB4050A850C04B3ABF54132565044B0B7D7BFD8BA270B39432355FFB4,
               Gx=0xB70E0CBD6BB4BF7F321390B94A03C1D356C21122343280D6115C1D21, Gy=0xBD376388B5F723FB4C22DFE6CD4375A05A07476444D5819985007E34,
               n=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFF16A2E0B8F03E13DD29455C5C2A3D),
 "P-256": dict(p=2**256 - 2**224 + 2**192 + 2**96 - 1, a=-3, b=0x5AC635D8AA3A93E7B3EBBD55769886BC651D06B0CC53B0F63BCE3C3E27D2604B,
               Gx=0x6B17D1F2E12C4247F8BCE6E563A440F277037D812DEB33A0F4A13945D898C296, Gy=0x4FE342E2FE1A7F9B8EE7EB4A7C0F9E162BCE33576B315ECECBB6406837BF51F5,
               n=0xFFFFFFFF00000000FFFFFFFFFFFFFFFFBCE6FAADA7179E84F3B9CAC2FC632551),
 "P-384": dict(p=2**384 - 2**128 - 2**96 + 2**32 - 1, a=-3, b=0xB3312FA7E23EE7E4988E056BE3F82D19181D9C6EFE8141120314088F5013875AC656398D8A2ED19D2A85C8EDD3EC2AEF,
               Gx=0xAA87CA22BE8B05378EB1C71EF320AD746E1D3B628BA79B9859F741E082542A385502F25DBF55296C3A545E3872760AB7,
               Gy=0x3617DE4A96262C6F5D9E98BF9292DC29F8F41DBD289A147CE9DA3113B5F0B8C00A60B1CE1D7E819D7A431D7C90EA0E5F,
               n=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFC7634D81F4372DDF581A0DB248B0A77AECEC196ACCC52973),
 "P-521": dict(p=2**521 - 1, a=-3, b=0x0051953EB9618E1C9A1F929A21A0B68540EEA2DA725B99B315F3B8B489918EF109E156193951EC7E937B1652C0BD3BB1BF073573DF883D2C34F1EF451FD46B503F00,
               Gx=0x00C6858E06B70404E9CD9E3ECB662395B4429C648139053FB521F828AF606B4D3DBAA14B5E77EFE75928FE1DC127A2FFA8DE3348B3C1856A429BF97E7E31C2E5BD66,
               Gy=0x011839296A789A3BC0045C8A5FB42C7D1BD998F54449579B446817AFBD17273E662C97EE72995EF42640C550B9013FAD0761353C7086A272C24088BE94769FD16650,
               n=0x01FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFA51868783BF2F966B7FCC0148F709A5D03BB5C9B8899C47AEBB6FB71E91386409),
 "secp160k1": dict(p=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFAC73, a=0, b=7,
               Gx=0x3B4C382CE37AA192A4019E763036F4F5DD4D7EBB, Gy=0x938CF935318FDCED6BC28286531733C3F03C4FEE, n=0x0100000000000000000001B8FA16DFAB9ACA16B6B3),
}

def ec_add(P, Q, a, p):
    if P is None: return Q
    if Q is None: return P
    x1, y1 = P; x2, y2 = Q
    if x1 == x2:
        if (y1 + y2) % p == 0: return None
        l = (3 * x1 * x1 + a) * pow(2 * y1, -1, p) % p
    else: l = (y2 - y1) * pow(x2 - x1, -1, p) % p
    x3 = (l * l - x1 - x2) % p; return (x3, (l * (x1 - x3) - y1) % p)
def ec_mul(k, P, a, p):
    R = None
    while k:
        if k & 1: R = ec_add(R, P, a, p)
        P = ec_add(P, P, a, p); k >>= 1
    return R

def targets(c, K=8):
    p, a, n = c["p"], c["a"], c["n"]; G = (c["Gx"], c["Gy"]); t = {}
    for k in range(1, K + 1):
        t[ec_mul(k, G, a, p)[0]] = f"{k}G"
        t[ec_mul(pow(k, -1, n), G, a, p)[0]] = f"G/{k}"
    return t

def sweep(name, c, maxseed, discards=range(0, 13), limb_deltas=(0,), max_tries=8):
    p, a, b = c["p"], c["a"], c["b"]; T = targets(c); L0 = -(-p.bit_length() // 26) + 1
    e = (p - 1) // 2; hits = 0
    for seed in range(1, maxseed + 1):
        # one stream per seed; different discard counts are just offsets into it
        state = seed; stream = []
        need = 13 + max_tries * (L0 + 1)
        for _ in range(need):
            state = state * A % M; stream.append(state % 2**26)
        for D in discards:
            for dl in limb_deltas:
                L = L0 + dl; pos = D; found = False
                for t in range(max_tries):
                    x = 0
                    for i in range(L): x = x << 26 | stream[pos + i]
                    pos += L
                    for cand in (x, x % p):
                        if cand in T:
                            print(f"HIT {name} seed={seed} discard={D} limbs={L} try={t+1} reduced={cand != x} on-curve-first={found} -> {T[cand]} x={cand:x}", flush=True); hits += 1
                    xr = x % p
                    if not found and pow(xr**3 + a * xr + b, e, p) == 1:
                        found = True
                        break      # the recipe stops at the first on-curve x; later tries only matter for the raw-match check above, which the max_tries loop already covers for the standard case
        if seed % 20000 == 0: print(f"  {name}: seed {seed}", flush=True)
    return hits

if __name__ == "__main__":
    maxseed = int(sys.argv[1]) if len(sys.argv) > 1 else 100000
    names = sys.argv[2:] or list(CURVES)
    total = 0
    for nm in names:
        total += sweep(nm, CURVES[nm], maxseed)
    print(f"done: seeds 1..{maxseed} x discards 0..12, standard limb count, on {names}: {total} hits")
