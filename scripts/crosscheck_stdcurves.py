"""Cross-check this repo's SECG curve parameters against an independent source,
J08nY/std-curves (vendored at references/std-curves/secg-curves.json).

The whole base-point investigation rests on the published (p, a, b, G, n, h) of
the secp*k1 and sect*k1 curves. This confirms those values field-by-field against
a second, independently assembled catalog, so a transcription slip in either
source would show up rather than propagate. On a mismatch the primary SEC 2 text
(verified in-repo by n*G = O) governs; this only catches typos.

Sources compared:
  * prime curves   -> scripts/secg_scan.py CURVES          (10 curves)
  * sect*k1 binary -> scripts/sectk_2020_checks.py SECTK    (6 curves)
  * NIST binary    -> data/bincurves.json                  (B/K-163..571, by alias)

Run from the repository root:  python3 scripts/crosscheck_stdcurves.py
Exit 0 iff every compared field agrees. `--out FILE` tees the report.
"""
import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from secg_scan import CURVES, C          # noqa: E402
import sectk_2020_checks as s2020        # noqa: E402

STD_PATH = ROOT / "references" / "std-curves" / "secg-curves.json"

out_lines = []


def say(s=""):
    print(s)
    out_lines.append(s)


def load_std():
    d = json.loads(STD_PATH.read_text())
    by_name, by_alias = {}, {}
    for c in d["curves"]:
        by_name[c["name"]] = c
        for a in c.get("aliases", []):
            by_alias[a.lower()] = c
    return by_name, by_alias


def h2i(x):
    return int(x, 16) if isinstance(x, str) else int(x)


def std_poly_int(entry):
    """Reduction polynomial of a binary-field std entry as an integer bitmask."""
    v = 0
    for term in entry["field"]["poly"]:
        v |= h2i(term["coeff"]) << term["power"]
    return v


def compare(label, rows):
    """rows: list of (field, ours, theirs). Returns list of mismatches."""
    bad = []
    for field, ours, theirs in rows:
        ok = ours == theirs
        if not ok:
            bad.append((field, ours, theirs))
    flag = "ok  " if not bad else "FAIL"
    say(f"  [{flag}] {label}: {len(rows)} fields" +
        ("" if not bad else "  <-- " + ", ".join(m[0] for m in bad)))
    for field, ours, theirs in bad:
        say(f"         {field}: ours={ours:#x} theirs={theirs:#x}")
    return bad


def main():
    by_name, by_alias = load_std()
    say(f"Cross-check vs references/std-curves/secg-curves.json "
        f"({len(by_name)} SECG curves)")
    say("=" * 70)
    mism = []

    # ---- prime curves -----------------------------------------------------
    say("Prime curves (secg_scan.CURVES):")
    for name in CURVES:
        if name not in by_name:
            say(f"  [MISS] {name}: absent from std-curves")
            mism.append((name, "absent"))
            continue
        c, s = C(CURVES[name]), by_name[name]
        p = h2i(s["field"]["p"])
        rows = [
            ("p", c.p, p),
            ("a", c.a % c.p, h2i(s["params"]["a"]["raw"]) % p),
            ("b", c.b % c.p, h2i(s["params"]["b"]["raw"]) % p),
            ("Gx", c.Gx, h2i(s["generator"]["x"]["raw"])),
            ("Gy", c.Gy, h2i(s["generator"]["y"]["raw"])),
            ("n", c.n, h2i(s["order"])),
            ("h", c.h, h2i(s["cofactor"])),
        ]
        mism += [(name, *b) for b in compare(name, rows)]

    # ---- sect*k1 binary curves -------------------------------------------
    say("Binary sect*k1 (sectk_2020_checks.SECTK):")
    for name, v in s2020.SECTK.items():
        if name not in by_name:
            say(f"  [MISS] {name}: absent from std-curves")
            mism.append((name, "absent"))
            continue
        s = by_name[name]
        from binpts import poly_from
        ours_poly = poly_from(v["m"], v["taps"])
        rows = [
            ("poly", ours_poly, std_poly_int(s)),
            ("a", v["a"], h2i(s["params"]["a"]["raw"])),
            ("b", v["b"], h2i(s["params"]["b"]["raw"])),
            ("Gx", h2i(v["Gx"]), h2i(s["generator"]["x"]["raw"])),
            ("Gy", h2i(v["Gy"]), h2i(s["generator"]["y"]["raw"])),
            ("n", h2i(v["n"]), h2i(s["order"])),
            ("h", v["h"], h2i(s["cofactor"])),
        ]
        mism += [(name, *b) for b in compare(name, rows)]

    # ---- NIST binary curves via alias (data/bincurves.json) --------------
    say("NIST binary curves (data/bincurves.json), matched by std-curves alias:")
    from binpts import poly_from
    binc = json.loads((ROOT / "data" / "bincurves.json").read_text())
    for nist_name, v in binc.items():
        alias = f"nist/{nist_name}"
        s = by_alias.get(alias.lower())
        if s is None:
            say(f"  [MISS] {nist_name}: no std-curves entry aliased {alias}")
            mism.append((nist_name, "absent"))
            continue
        rows = [
            ("poly", poly_from(v["m"], v["taps"]), std_poly_int(s)),
            ("a", h2i(v["a"]), h2i(s["params"]["a"]["raw"])),
            ("b", h2i(v["b"]), h2i(s["params"]["b"]["raw"])),
            ("Gx", h2i(v["Gx"]), h2i(s["generator"]["x"]["raw"])),
            ("Gy", h2i(v["Gy"]), h2i(s["generator"]["y"]["raw"])),
            ("n", h2i(v["n"]), h2i(s["order"])),
            ("h", v["h"], h2i(s["cofactor"])),
        ]
        mism += [(f"{nist_name}={s['name']}", *b) for b in compare(f"{nist_name} = {s['name']}", rows)]

    # ---- aliases for the Koblitz curves (archival cross-refs) -------------
    say("Aliases of the Koblitz curves (for notes/archival.md):")
    for name in list(CURVES) + list(s2020.SECTK):
        if name in by_name and "k1" in name:
            al = by_name[name].get("aliases", [])
            say(f"  {name}: {', '.join(al) if al else '(none)'}")

    say()
    if mism:
        say(f"RESULT: {len(mism)} mismatch(es) -- investigate (primary SEC 2 governs).")
    else:
        say("RESULT: every compared field agrees with std-curves. The secp*k1 and")
        say("sect*k1 generators, fields, orders and cofactors this project analyses")
        say("are confirmed against an independent catalog.")
    return mism


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", help="tee the report to a file")
    args = ap.parse_args()
    bad = main()
    if args.out:
        Path(args.out).write_text("\n".join(out_lines) + "\n")
    sys.exit(1 if bad else 0)
