# halve_generators.sage
# Reconstruction (Oct 2026) of the 2019 base-point-halving investigation with
# Nadia Heninger and Travis Scholl. The original Sage code was not found in mail;
# this re-implements the computations described in the Aug-Oct 2019 threads.
# Modern arithmetic reconstruction, not evidence of the original workflow.
# Primality checks use Sage's proof-enabled algorithms explicitly.

def bits(x): return ZZ(x).nbits()

# ---- SEC 2 prime-field Koblitz curves (y^2 = x^3 + b), cofactor 1 ----------
SECPK1 = {
 "secp160k1": (0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFAC73, 7,
               0x3B4C382CE37AA192A4019E763036F4F5DD4D7EBB,
               0x938CF935318FDCED6BC28286531733C3F03C4FEE,
               0x0100000000000000000001B8FA16DFAB9ACA16B6B3),
 "secp192k1": (0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFEE37, 3,
               0xDB4FF10EC057E9AE26B07D0280B7F4341DA5D1B1EAE06C7D,
               0x9B2F2F6D9C5628A7844163D015BE86344082AA88D95E2F9D,
               0xFFFFFFFFFFFFFFFFFFFFFFFE26F2FC170F69466A74DEFD8D),
 "secp224k1": (0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFE56D, 5,
               0xA1455B334DF099DF30FC28A169A467E9E47075A90F7E650EB6B7A45C,
               0x7E089FED7FBA344282CAFBD6F7E319F7C0B0BD59E2CA4BDB556D61A5,
               0x010000000000000000000000000001DCE8D2EC6184CAF0A971769FB1F7),
 "secp256k1": (0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F, 7,
               0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798,
               0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8,
               0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141),
}
EXPECTED = {
 "secp160k1": 0x48ce563f89a0ed9414f5aa28ad0d96d6795f9c62,
 "secp192k1": 0x554123b78ce563f89a0ed9414f5aa28ad0d96d6795f9c66,
 "secp224k1": 0x3b78ce563f89a0ed9414f5aa28ad0d96d6795f9c63,
 "secp256k1": 0x3b78ce563f89a0ed9414f5aa28ad0d96d6795f9c63,
}

def halve(G):
    n = G.order()
    H = ((n + 1) // 2) * G        # = (n-1)/2 * G up to sign; same x-coordinate
    assert 2 * H == G
    return H

print("== x((1/2)G) on the secpXXXk1 curves ==")
halves = {}
for name, (p, b, gx, gy, n) in SECPK1.items():
    E = EllipticCurve(GF(p), [0, b])
    G = E(gx, gy)
    n = ZZ(n); assert n * G == 0 and n.is_prime(proof=True)
    H = halve(G)
    x = ZZ(H[0]); halves[name] = (E, x)
    assert x == EXPECTED[name], name
    print(f"{name}: {x.hex()}  ({bits(x)} of {bits(p)} bits)")

# ---- Dan Brown's hypothesis: 160-bit core + small counter = first x that lifts
print("\n== smallest low-k-bit value that lifts to a point (upper bits fixed) ==")
for name, (E, x) in halves.items():
    for k in (4, 6):
        base = x - (x % 2^k)
        valid = [d for d in range(2^k) if E.is_x_coord(base + d)]
        print(f"{name} k={k}: actual={x % 2^k}, smallest valid={valid[0]}, first few={valid[:6]}")
# Result (verified): the actual low bits are NOT the smallest valid value for any
# curve, so a naive count-up-from-zero counter in the low 4 or 6 bits is ruled out.

# ---- Control: a random-looking curve (P-256) gives a full-length x ----------
p = 0xFFFFFFFF00000001000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFF
E = EllipticCurve(GF(p), [-3, 0x5AC635D8AA3A93E7B3EBBD55769886BC651D06B0CC53B0F63BCE3C3E27D2604B])
G = E(0x6B17D1F2E12C4247F8BCE6E563A440F277037D812DEB33A0F4A13945D898C296,
      0x4FE342E2FE1A7F9B8EE7EB4A7C0F9E162BCE33576B315ECECBB6406837BF51F5)
control_bits = bits(ZZ(halve(G)[0]))
assert control_bits == 254
print("\nsecp256r1 control:", control_bits, "bits")

# ---- Binary Koblitz curve sect163k1 (June 2020 follow-up) -------------------
R.<t> = GF(2)[]
K.<w> = GF(2^163, modulus=t^163 + t^7 + t^6 + t^3 + 1)
def K_from_int(v): return K([ (v >> i) & 1 for i in range(163) ])
def K_to_int(e):   return sum(ZZ(c) << i for i, c in enumerate(e.polynomial().list()))
E2 = EllipticCurve(K, [1, 1, 0, 0, 1])          # y^2 + xy = x^3 + x^2 + 1
G2 = E2(K_from_int(0x02FE13C0537BBC11ACAA07D793DE4E6D5E5C94EEE8),
        K_from_int(0x0289070FB05D38FF58321F2E800536D538CCDAA3D9))
n2 = 0x04000000000000000000020108A2E0CC0D99F8A5EF
assert n2 * G2 == 0
H2 = ((n2 + 1) // 2) * G2; assert 2 * H2 == G2     # the half inside the prime-order subgroup
x2 = K_to_int(H2[0])
assert x2 == 0x23e21d6019e1211f6bd47ec180256e97 and bits(x2) == 126
print("sect163k1:", hex(x2), f"({bits(x2)} of 163 bits)")  # 0x23e21d6019e1211f6bd47ec180256e97, 126 bits

# ---- Travis Scholl's derivation of the secp256k1 field prime (email, 27 Oct 2019)
Kq = QuadraticField(-3)
lo, hi = 2^256 - 2^32 - 977, 2^256 - 2^32
moduli = [ZZ(p) for p in range(lo, hi, 2) if ZZ(p).is_prime(proof=True)]
offsets = [hi - p for p in moduli]
assert offsets == [977, 949, 739, 487, 361, 359, 263]
cands = [p for p in moduli if p % 3 == 1]
assert len(cands) == 3
assert all(p % 3 == 2 and (p + 1) % 2 == 0 for p in moduli if p not in cands)
print("\n== CM window: proof-enabled primality ==")
print("primality mode: Sage is_prime(proof=True)")
print("proven prime offsets below 2^256-2^32:", offsets)
print("prime moduli: 7; split primes (p = 1 mod 3): 3")
print("For prime p = 2 mod 3, every j=0 curve has even order p+1.")
hits = []
orders_checked = 0
units = Kq.roots_of_unity()
assert len(units) == 6
for p in cands:
    pi = Kq.prime_above(p).gens_reduced()[0]
    assert pi.norm() == p
    for u in units:
        N = ZZ((u*pi - 1).norm())
        orders_checked += 1
        if N.is_prime(proof=True): hits.append((p, N))
assert orders_checked == 18
assert hits == [(2^256 - 2^32 - 977, 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141)]
print("CM candidate orders checked: 18; proven prime orders: 1")
print("secp256k1 p is the largest prime below 2^256-2^32-1 with a prime-order j=0 curve: OK")
print("This verifies the arithmetic relation, not the historical generation procedure.")
