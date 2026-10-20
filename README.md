# Where did the base points come from?

*A historical investigation of the generators of the standard elliptic curves — NIST FIPS 186, ANSI X9.62, SEC 2. Spun out of [ECDSA-Origins-Revealed-Followup](https://github.com/shumow/ECDSA-Origins-Revealed-Followup) on 20 October 2026, which stays focused on the skipped-seed question.*

## The framing

Nothing here is an attack, and nothing here suggests one. Anthropic's October 2026 result settled the curve *seeds*: `lrand48()` from the Unix clock, candidates drawn in order, no hash of anybody's sentence. The *base points* are the piece that is still unexplained for fourteen of the twenty NIST/ANSI curves — P-224, P-256, P-384, P-521, the five B curves and the five K curves — and for every SEC 2 curve beyond those. And the structure we can see in them is of a specific kind:

- secp224k1 and secp256k1 have the **identical** 166-bit *x*-coordinate at *G*/2: `3b78ce563f89a0ed9414f5aa28ad0d96d6795f9c63`.
- secp160k1 and secp192k1 carry the same 148-bit core with different top bits and last nibbles (`48ce563f…9c62`, `554123b78ce563f…9c66`).
- *x*(*G*/2) on secp160r2 shares its first 92 bits with *x*(*G*) on secp160r1.
- The half of the K-163 generator has a 126-bit *x*: `23e21d6019e1211f6bd47ec180256e97`.

These are not the fingerprints of a designer hiding a weakness; it is hard to even sketch an attack that would use a shared public *x*-coordinate. They look like what programmers and mathematicians leave behind when nobody is watching: a convenience constant reused across fields, a test value never replaced, an Easter egg. That is the historical observation, and it is reason enough to keep digging. The seeds went from lore to fact in a day once someone found the recipe. The generators are the last large piece of the standard parameter set with no account of their origin, and they now carry structure that says there is an account to be found.

The secp\*k1 observation was first made in the Heninger–Scholl–Shumow Crypto 2019 rump-session talk, whose title is *x*(*G*/2) on secp160k1.

## What is here

| | |
|---|---|
| [`HANDOFF.md`](HANDOFF.md) | **start here** — everything known, everything tried, what to do next |
| [`notes/plan.md`](notes/plan.md) | the hypotheses and the six-step search plan, with the steps already run marked |
| [`notes/record.md`](notes/record.md) | the full record of what has been computed so far (small-multiple scans, K-163, the SEC 2 curves) |
| [`notes/base-point-brief.md`](notes/base-point-brief.md) | the earlier hand-off brief |
| [`scripts/`](scripts/) | `secg_scan.py` (SEC 2 prime curves), `binpts.py`/`.gp` (NIST binary curves), `k163/` (hash-preimage harness), `secg_core_search.py` (core-matched search) |
| [`results/`](results/) | every number behind the statements above |

## Status

Two of the six steps in the plan have been run, both negative: no obvious acceptance rule selects the per-curve last nibbles 2, 6, 3, 3, and a 16.4-million-evaluation SHA-1/SHA-0/RIPEMD-160 search over NIST-era strings does not produce the 148-bit core. The Certicom-era string pass is the next experiment.

## Who

Dan Shumow. Computation and drafting with Claude (Anthropic). Thanks to Nadia Heninger and Travis Scholl.

Code CC0 1.0; text CC BY 4.0.
