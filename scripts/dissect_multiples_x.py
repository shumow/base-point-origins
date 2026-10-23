"""Reconcile this repo's half-generator scan with DiSSECT's `multiples_x` trait.

Checking crocs-muni/DiSSECT for base-point provenance turned up no prose
derivation (its curve DB is the same neuromancer/std-curves catalog already
vendored and cross-checked). What it does contain is an analytic trait,
`dissect/traits/multiples_x.py`, that independently formalises the exact
phenomenon behind this project:

    multiple = 1/k mod n ;  H = multiple * G ;  report bitlength of x(H)
    and the "difference" = bitlength(cardinality) - bitlength(x(H)).

At k = 2 this is x(G/2) -- the half-generator. This script reimplements the
trait in pure Python (the repo's own curve arithmetic) for the secp*k1 curves
and K-163, and asserts the k=2 value equals the x(G/2) in `notes/record.md`.
That ties the CRoCS trait to this repo's numbers: both measure the same thing,
and the famous short coordinates are what the trait's "difference" column flags.

Run from the repository root:  python3 scripts/dissect_multiples_x.py
Exit 0 iff k=2 reproduces the recorded x(G/2) on every curve. `--out FILE` tees.
"""
import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from secg_scan import CURVES, C          # noqa: E402  prime-field arithmetic
import binpts                            # noqa: E402  GF(2^m) arithmetic

# x(G/2) from notes/record.md (the values this project analyses)
RECORDED_HALF = {
    "secp160k1": 0x48ce563f89a0ed9414f5aa28ad0d96d6795f9c62,
    "secp192k1": 0x554123b78ce563f89a0ed9414f5aa28ad0d96d6795f9c66,
    "secp224k1": 0x3b78ce563f89a0ed9414f5aa28ad0d96d6795f9c63,
    "secp256k1": 0x3b78ce563f89a0ed9414f5aa28ad0d96d6795f9c63,
    "K-163":     0x23e21d6019e1211f6bd47ec180256e97,
}

out_lines = []


def say(s=""):
    print(s)
    out_lines.append(s)


def trait_multiples_x(order, cardinality, mul, G, k):
    """DiSSECT multiples_x.compute(), transcribed: x of (1/k mod n)*G."""
    inv = pow(k, -1, order)
    H = mul(inv, G)
    Hx = H[0]
    bits = Hx.bit_length()
    difference = cardinality.bit_length() - bits
    return Hx, bits, difference


def main():
    say("DiSSECT multiples_x trait, reimplemented and reconciled with x(G/2)")
    say("=" * 70)
    say("trait: multiple = 1/k mod n; H = multiple*G; report bitlength(x(H)) and")
    say("difference = bitlength(cardinality) - bitlength(x(H)). k=2 is x(G/2).")
    say("")
    say(f"{'curve':10s} {'k=2 x(H) bits':>13s} {'diff':>5s}   {'k=2 x(H) == recorded x(G/2)':>28s}")
    bad = []

    # prime secp*k1 curves
    for name in ("secp160k1", "secp192k1", "secp224k1", "secp256k1"):
        c = C(CURVES[name])
        G = (c.Gx, c.Gy)
        card = c.n * c.h
        Hx, bits, diff = trait_multiples_x(c.n, card, c.mul, G, 2)
        ok = Hx == RECORDED_HALF[name]
        bad += [] if ok else [name]
        say(f"{name:10s} {bits:>13d} {diff:>5d}   {str(ok):>28s}")

    # K-163 (sect163k1), binary field, cofactor 2
    K = binpts.Curve(163, binpts.poly_from(163, [7, 6, 3, 0]), 1, 1,
                     0x04000000000000000000020108A2E0CC0D99F8A5EF, 2)
    G = (0x02FE13C0537BBC11ACAA07D793DE4E6D5E5C94EEE8,
         0x0289070FB05D38FF58321F2E800536D538CCDAA3D9)
    card = K.n * K.h
    Hx, bits, diff = trait_multiples_x(K.n, card, K.mul, G, 2)
    ok = Hx == RECORDED_HALF["K-163"]
    bad += [] if ok else ["K-163"]
    say(f"{'K-163':10s} {bits:>13d} {diff:>5d}   {str(ok):>28s}")

    # the short-coordinate anomaly across k=1..10 on secp256k1, for context
    say("")
    say("secp256k1, k = 1..10 (the trait's default range), x(1/k * G) bitlength:")
    c = C(CURVES["secp256k1"]); G = (c.Gx, c.Gy); card = c.n * c.h
    row = []
    for k in range(1, 11):
        _, bits, diff = trait_multiples_x(c.n, card, c.mul, G, k)
        row.append(f"k={k}:{bits}({diff})")
    say("  " + "  ".join(row))
    say("  (bits(diff); k=2 is the short one: 166 bits, ~90 short of the 256-bit group.)")

    say("")
    if bad:
        say(f"RESULT: MISMATCH on {bad} -- investigate.")
    else:
        say("RESULT: DiSSECT's multiples_x at k=2 reproduces the recorded x(G/2) on all")
        say("five curves. The CRoCS trait and this repo measure the same quantity; the")
        say("short half-generators are exactly what its 'difference' column flags. DiSSECT")
        say("states no derivation for the base points -- it measures the anomaly, as we do.")
    return bad


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", help="tee the report to a file")
    args = ap.parse_args()
    bad = main()
    if args.out:
        Path(args.out).write_text("\n".join(out_lines) + "\n")
    sys.exit(1 if bad else 0)
