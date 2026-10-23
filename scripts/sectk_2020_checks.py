"""Re-run, in pure Python, the two searches in Dan's June 2020 Sage code, recovered
from the private factorable/secp256k1 repository on 23 Oct 2026 and archived in
references/crypto2019-rump/factorable-secp256k1/.

 1. sectk_small_x_srch.sage: for each sect*k1 curve, the x-coordinates of
    sigma^k(2^-j * G) + T for 0 <= j, k < m and T in E[h] (sigma = Frobenius),
    looking for anything short. Its recorded output is
    short_x_coordinate_search_sectXXXk1_curves.txt. The full m^2 * h grid is the
    Sage run's job; here each reported minimum is recomputed from its (k, j) and
    compared with the recorded value. With --full the whole grid is re-run
    (unattended job, ~1-2 h for all six curves in pure Python; runbook in
    references/crypto2019-rump/README.md).
 2. sectk_endomorphism_srch.sage: the hypothesis G = P + sigma(P) for a P with a
    short x, i.e. P = (1 + sigma)^-1 G, run there on sect233k1 only with no
    recorded result. Here it is run on all six curves. On the prime-order
    subgroup sigma acts as a scalar lambda, a root of lambda^2 - mu*lambda + 2
    (mu = (-1)^(1-a)), so (1 + sigma)^-1 G = ((1 + lambda)^-1 mod n) * G.

Run from the repository root:
  python3 scripts/sectk_2020_checks.py                       # 15 s: recorded minima + endomorphism test
  python3 scripts/sectk_2020_checks.py --full [curve ...]    # the whole grid, appends to results/sectk-2020-full-grid.txt
"""
import os
import random
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import binpts  # noqa: E402

# Parameters as in seck_curves.sage (SEC 2 v1.0 / v2.0). sect239k1's Gy carries a
# stray space in that file, which Sage's GMP-backed parser ignores; removed here.
SECTK = {
    "sect163k1": dict(m=163, taps=[7, 6, 3, 0], a=1, b=1, h=2,
                      Gx="02FE13C0537BBC11ACAA07D793DE4E6D5E5C94EEE8", Gy="0289070FB05D38FF58321F2E800536D538CCDAA3D9",
                      n="04000000000000000000020108A2E0CC0D99F8A5EF"),
    "sect233k1": dict(m=233, taps=[74, 0], a=0, b=1, h=4,
                      Gx="017232BA853A7E731AF129F22FF4149563A419C26BF50A4C9D6EEFAD6126",
                      Gy="01DB537DECE819B7F70F555A67C427A8CD9BF18AEB9B56E0C11056FAE6A3",
                      n="8000000000000000000000000000069D5BB915BCD46EFB1AD5F173ABDF"),
    "sect239k1": dict(m=239, taps=[158, 0], a=0, b=1, h=4,
                      Gx="29A0B6A887A983E9730988A68727A8B2D126C44CC2CC7B2A6555193035DC",
                      Gy="76310804F12E549BDB011C103089E73510ACB275FC312A5DC6B76553F0CA",
                      n="2000000000000000000000000000005A79FEC67CB6E91F1C1DA800E478A5"),
    "sect283k1": dict(m=283, taps=[12, 7, 5, 0], a=0, b=1, h=4,
                      Gx="0503213F78CA44883F1A3B8162F188E553CD265F23C1567A16876913B0C2AC2458492836",
                      Gy="01CCDA380F1C9E318D90F95D07E5426FE87E45C0E8184698E45962364E34116177DD2259",
                      n="01FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE9AE2ED07577265DFF7F94451E061E163C61"),
    "sect409k1": dict(m=409, taps=[87, 0], a=0, b=1, h=4,
                      Gx="0060F05F658F49C1AD3AB1890F7184210EFD0987E307C84C27ACCFB8F9F67CC2C460189EB5AAAA62EE222EB1B35540CFE9023746",
                      Gy="01E369050B7C4E42ACBA1DACBF04299C3460782F918EA427E6325165E9EA10E3DA5F6C42E9C55215AA9CA27A5863EC48D8E0286B",
                      n="7FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE5F83B2D4EA20400EC4557D5ED3E3E7CA5B4B5C83B8E01E5FCF"),
    "sect571k1": dict(m=571, taps=[10, 5, 2, 0], a=0, b=1, h=4,
                      Gx="026EB7A859923FBC82189631F8103FE4AC9CA2970012D5D46024804801841CA44370958493B205E647DA304DB4CEB08CBBD1BA39494776FB988B47174DCA88C7E2945283A01C8972",
                      Gy="0349DC807F4FBF374F4AEADE3BCA95314DD58CEC9F307A54FFC61EFC006D8A2C9D4979C0AC44AEA74FBEBBB9F772AEDCB620B01A7BA7AF1B320430C8591984F601CD4C143EF1C7A3",
                      n="020000000000000000000000000000000000000000000000000000000000000000000000131850E1F19A63E4B391A8DB917F4138B630D84BE5D639381E91DEB45CFE778F637C1001"),
}

# The minima recorded in short_x_coordinate_search_sectXXXk1_curves.txt (June 2020).
RECORDED_2020 = {
    "sect163k1": (126, 0, 1, "23e21d6019e1211f6bd47ec180256e97"),
    "sect233k1": (215, 89, 45, "661f999262551200178956536e047d906dbdee0dec0c7597f53ae3"),
    "sect239k1": (219, 56, 153, "4f8c144480033052df685ab429878f71c42aa841ca1519db38298a5"),
    "sect283k1": (266, 18, 13, "3750cacdb38706fa100dfa62919bd3015ef8a5ba82051ad7e6701daa609b2c7c677"),
    "sect409k1": (390, 134, 139, "20539cf83831d530ea184d469f6879ec06add32aa47c41d834819ff6a4652fa20d4737bd7f31fcdf938e6d79191379833b"),
    "sect571k1": (549, 261, 265, "11d12cc87a035e5bd8f908be3c6af41b7fe69e71ca6c914e8570461863aed5e576b863eb535a1b5f30c896c3860efde2fc22310889b06f7398cd263da94b3bda953fda1590"),
}


def gf_inv_eea(a, poly, m):
    """Inverse in GF(2^m) by the binary extended Euclidean algorithm (Hankerson,
    Menezes, Vanstone, Alg. 2.48). Replaces binpts.gf_inv's Fermat exponentiation,
    which costs ~2m field multiplications; this costs ~2m big-int shifts."""
    if a == 0:
        raise ZeroDivisionError
    u, v, g1, g2 = a, poly, 1, 0
    while u != 1:
        j = u.bit_length() - v.bit_length()
        if j < 0:
            u, v, g1, g2, j = v, u, g2, g1, -j
        u ^= v << j
        g1 ^= g2 << j
    return g1


def install_fast_inverse(check_m=163, trials=25):
    """Swap in the EEA inverse after checking it against the Fermat one."""
    poly = binpts.poly_from(check_m, SECTK["sect163k1"]["taps"])
    rng = random.Random(2020)
    for _ in range(trials):
        a = rng.randrange(1, 1 << check_m)
        assert gf_inv_eea(a, poly, check_m) == binpts.gf_inv(a, poly, check_m)
        assert binpts.gf_mul(a, gf_inv_eea(a, poly, check_m), poly, check_m) == 1
    binpts.gf_inv = gf_inv_eea


def sqrt_mod(a, p):  # Tonelli-Shanks
    a %= p
    if a == 0: return 0
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


class Sect:
    def __init__(s, name, d, G=None):
        """G overrides the published generator (tests plant one of known construction)."""
        s.name, s.m, s.a, s.b, s.h = name, d["m"], d["a"], d["b"], d["h"]
        s.poly = binpts.poly_from(s.m, d["taps"])
        s.C = binpts.Curve(s.m, s.poly, s.a, s.b, int(d["n"], 16), s.h)
        s.n = s.C.n
        s.G = G or (int(d["Gx"], 16), int(d["Gy"], 16))
        assert s.C.on(s.G), name + ": G not on curve"
        assert s.C.mul(s.n, s.G) is None, name + ": n*G != O"
        # E[h] = the F_2-rational points: the group order is h*n with n odd, so the
        # 2-part of E(F_2^m) is E(F_2) exactly when |E(F_2)| = h, which holds here.
        s.cofactor_group = [None] + [(x, y) for x in (0, 1) for y in (0, 1) if s.C.on((x, y))]
        assert len(s.cofactor_group) == s.h, name + ": E(F_2) is not E[h]"
        for T in s.cofactor_group[1:]:
            assert s.C.mul(s.h, T) is None
        # Frobenius eigenvalue on <G>: lambda^2 - mu*lambda + 2 = 0 mod n, mu = (-1)^(1-a)
        mu = 1 if s.a == 1 else -1
        r = sqrt_mod(mu * mu - 8, s.n)
        assert r is not None
        inv2 = pow(2, -1, s.n)
        sG = s.frob(s.G, 1)
        s.lam = None
        for cand in ((mu + r) * inv2 % s.n, (mu - r) * inv2 % s.n):
            if s.C.mul(cand, s.G) == sG:
                s.lam = cand
        assert s.lam is not None, name + ": Frobenius eigenvalue not found"

    def frob(s, P, k):
        x, y = P
        for _ in range(k):
            x = binpts.gf_mul(x, x, s.poly, s.m)
            y = binpts.gf_mul(y, y, s.poly, s.m)
        return (x, y)

    def coset_x_bits(s, P):
        """(bits, x) of the shortest x among P + T, T in E[h]."""
        best = None
        for T in s.cofactor_group:
            Q = s.C.add(P, T)
            if Q is None: continue
            cand = (Q[0].bit_length(), Q[0])
            if best is None or cand < best: best = cand
        return best

    def grid_point(s, k, j):
        """sigma^k(2^-j G), the point sectk_small_x_srch.sage examines at (k, j)."""
        P = s.C.mul(pow(pow(2, j, s.n), -1, s.n), s.G)
        return s.frob(P, k)


def full_grid(c, js=None, progress=None):
    """The whole 2020 search on one curve: the shortest x over sigma^k(2^-j G) + T
    for j in js (default 0..m-1), 0 <= k < m, T in E[h]. Returns (bits, x, k, j).
    progress(j_done, j_total, elapsed_s) is called after each j."""
    js = range(c.m) if js is None else js
    best, t0 = None, time.time()
    for i, j in enumerate(js):
        P = c.C.mul(pow(pow(2, j, c.n), -1, c.n), c.G)
        for k in range(c.m):
            if k: P = c.frob(P, 1)
            cand = c.coset_x_bits(P)
            if best is None or cand < best[:2]: best = (cand[0], cand[1], k, j)
        if progress: progress(i + 1, len(js), time.time() - t0)
    return best


def run_full_grid(names, out_path):
    """The unattended job: every (k, j) on each named curve, one result line per
    curve appended to out_path as soon as that curve finishes (so a killed run
    keeps what it had), progress with an ETA on stderr. Exit 1 if any curve's
    global minimum differs from the 2020 record."""
    install_fast_inverse()
    failures = []
    with open(out_path, "a") as out:
        out.write(f"# full grid sigma^k(2^-j G) + T, 0 <= j,k < m, T in E[h]; started {time.strftime('%Y-%m-%d %H:%M:%S %Z')}\n")
        out.flush()
        for name in names:
            c = Sect(name, SECTK[name])

            def progress(done, total, elapsed, name=name):
                if done % max(1, total // 20) == 0 or done == total:
                    eta = elapsed / done * (total - done)
                    print(f"{name}: j {done}/{total}  elapsed {elapsed / 60:.1f} min  eta {eta / 60:.1f} min", file=sys.stderr, flush=True)

            t0 = time.time()
            bits, x, k, j = full_grid(c, progress=progress)
            rbits, rk, rj, rxhex = RECORDED_2020[name]
            ok = (bits, x) == (rbits, int(rxhex, 16))
            expect = c.m - (c.m * c.m * c.h).bit_length() + 1
            line = (f"{name}: global minimum {bits} of {c.m} bits at (k={k}, j={j}): {x:x}  "
                    f"[2020 record: {rbits} bits at (k={rk}, j={rj}); uniform ~{expect} bits]  "
                    f"{'MATCHES the 2020 record' if ok else 'DIFFERS from the 2020 record'}  ({(time.time() - t0) / 60:.1f} min)")
            print(line); out.write(line + "\n"); out.flush()
            if not ok: failures.append(name)
        out.write("# done; " + ("all curves match the 2020 record" if not failures else "MISMATCH on " + ", ".join(failures)) + "\n")
    return 1 if failures else 0


def main(argv):
    import argparse
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--full", action="store_true", help="run the whole m^2*h grid on each named curve (long; see the runbook)")
    ap.add_argument("--out", default="results/sectk-2020-full-grid.txt", help="--full: file to append per-curve results to")
    ap.add_argument("curves", nargs="*", default=list(SECTK), help="--full: curves to run (default: all six, smallest first)")
    args = ap.parse_args(argv)
    if args.full:
        unknown = [n for n in args.curves if n not in SECTK]
        if unknown: ap.error("unknown curve(s): " + ", ".join(unknown))
        return run_full_grid(args.curves, args.out)

    install_fast_inverse()
    failures = []

    def check(cond, msg):
        print(("  ok   " if cond else "  FAIL ") + msg)
        if not cond: failures.append(msg)

    print("1. the June 2020 grid search sigma^k(2^-j G) + T: recorded minima recomputed")
    curves = {}
    for name, d in SECTK.items():
        t0 = time.time()
        c = Sect(name, d); curves[name] = c
        bits, k, j, xhex = RECORDED_2020[name]
        got_bits, got_x = c.coset_x_bits(c.grid_point(k, j))
        expect = c.m - (c.m * c.m * c.h).bit_length() + 1
        check(got_bits == bits and got_x == int(xhex, 16),
              f"{name}: at (k={k}, j={j}) shortest coset x has {got_bits} of {c.m} bits = {got_x:x}"
              f"  [grid of m^2*h = {c.m * c.m * c.h} points; uniform minimum ~{expect} bits]  ({time.time() - t0:.1f}s)")

    print("2. the endomorphism hypothesis G = P + sigma(P): x bits of (1 + sigma)^-1 G + T")
    for name, c in curves.items():
        P = c.C.mul(pow(1 + c.lam, -1, c.n), c.G)
        # confirm the construction: P + sigma(P) == G
        assert c.C.add(P, c.frob(P, 1)) == c.G
        rows = []
        for T in c.cofactor_group:
            Q = c.C.add(P, T)
            rows.append(Q[0].bit_length())
        short = [b for b in rows if b < 0.75 * c.m]
        check(not short, f"{name}: coset x bit lengths {rows} of {c.m}; nothing short" if not short
              else f"{name}: SHORT x found: {rows}")
        # for completeness, the same with (1 - sigma): P - sigma(P) == G
        P2 = c.C.mul(pow(1 - c.lam, -1, c.n), c.G)
        rows2 = [c.C.add(P2, T)[0].bit_length() for T in c.cofactor_group]
        print(f"       (1 - sigma)^-1 G + T: {rows2}")

    print("3. control: x(G/2) + T on each curve (record 7.1 already has these)")
    for name, c in curves.items():
        rows = [c.C.add(c.C.mul((c.n + 1) // 2, c.G), T)[0].bit_length() for T in c.cofactor_group]
        print(f"       {name}: {rows} of {c.m}")

    print()
    print("ALL OK" if not failures else f"{len(failures)} FAILURE(S): " + "; ".join(failures))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
