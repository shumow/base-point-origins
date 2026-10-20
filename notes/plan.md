# Future work: where the base points came from

*Written 2026-10-20 on the `base-points` branch. The skipped-seed question on `main` is an exploratory negative result; this document is the plan for the other provenance problem, the generators, which now has two concrete handles.*

## 1. The framing

Nothing in this document is an attack, and nothing here suggests one. Anthropic's result settled the seeds: `lrand48` from the clock, candidates in order, no hash of anybody's sentence. What is left over is a collection of oddities in how the *base points* were made — and the oddities we can now see are of a specific kind. A 166-bit constant reused verbatim across two curves. The same constant's core reused, with different top bits, on two more. A 92-bit prefix shared between one curve's generator and another's half-generator. A 126-bit x-coordinate sitting under the published K-163 generator. These are not the fingerprints of a designer hiding a weakness; it is hard to even sketch an attack that would use a shared public x-coordinate. They look like what programmers and mathematicians leave behind when nobody is watching: a convenience constant, a test value that was never replaced, an Easter egg.

That is the historical point, and it is reason enough to keep digging. The 1997–2000 generation of standard curves was done by a handful of people with ad hoc tools, and the record of *how* is mostly lost. Every recovered recipe — the `lrand48` seeds, the FreeLIP `zrandom` base points, and now whatever produced the secp\*k1 constant — replaces lore with fact. The base points are the last large piece of the NIST/SEC parameter set with no account of their origin, and they now carry structure that says there is an account to be found.

## 2. What we have (§7.1–7.2 of `cm-hypothesis.md`)

Subgroup half-generators x(G/2), i.e. ((n+1)/2)·G:

```
secp160k1   48ce563f89a0ed9414f5aa28ad0d96d6795f9c62              159 bits on 160
secp192k1   554123b78ce563f89a0ed9414f5aa28ad0d96d6795f9c66       187 bits on 192
secp224k1   3b78ce563f89a0ed9414f5aa28ad0d96d6795f9c63            166 bits on 224
secp256k1   3b78ce563f89a0ed9414f5aa28ad0d96d6795f9c63            166 bits on 256
K-163       23e21d6019e1211f6bd47ec180256e97                      126 bits on 163

secp160r1   x(G)   = 4a96b5688ef573284664698968c38bb913cbfc82
secp160r2   x(G/2) = 4a96b5688ef573284664698e81e1510fae4e8422      (first 92 bits shared)
```

Being precise about what is shared, since it constrains the hypotheses:

- The four secp\*k1 values agree on bits 4–151 — the 148-bit core `ce563f89a0ed9414f5aa28ad0d96d6795f9c6`.
- Bits 152–159 are `48` on secp160k1 and `78` on the other three. So it is *not* the case that the low 160 bits are fixed; the top byte of the 160-bit block differs on the 160-bit curve.
- Above bit 160: nothing on 160k1 (it would not fit), `3b` on 224k1/256k1, `554123b` on 192k1. The 192k1 value is 187 bits, so its extra high bits are not a truncation of a longer constant to the field size — the smaller field has *more* prefix than the larger ones.
- Last nibble: 2, 6, 3, 3.
- "Smallest i such that …9c60 + i is on the curve" does not reproduce the last nibbles: …9c60 is already on secp160k1, …9c61 on secp256k1.
- Every one of these values is far below its field prime, so no reduction mod p is in play for the published values themselves.

## 3. Hypotheses

**H1 — a SHA-1 digest with a small adjustment.** The 160-bit shape of the secp160k1 value and the shared 148-bit core point at a 160-bit hash in the low word, with the last nibble (and possibly the top byte) adjusted per curve. The adjustment would be whatever it took to get a point: incrementing x until the right-hand side is a square, or until the resulting point had some property (the published G is 2·P, so perhaps P was required to have prime order on an h > 1 curve, or the y-coordinate was required to have a certain parity). The fact that the increments are small (2, 3, 6) but not the *minimal* on-curve increments means the acceptance test was not plain "x is on the curve". Candidates: the parity of y (SEC 1 compressed-point convention), y < p/2, or "both ±y tested".

**H2 — the high bits are a counter or a second digest.** `3b78` on 224/256 and `554123b78` on 192 share `3b78`. One reading: the x-coordinate was assembled as (prefix ‖ digest) with the prefix depending on the field; another: x = H(s ‖ i) expanded X9.62-style to field length, which would give *different* high bits per curve and — crucially — would make the low 160 bits identical only if the expansion put the same digest in the low word. The `48` vs `78` disagreement on the 160-bit curve is the fact any expansion story has to explain.

**H3 — a test or debug constant.** The simplest story: the constant was a fixed number in the generation code (a hash of some string, a prior output, or a typed-in value), used as the starting x for every Koblitz curve, with per-curve search for an on-curve x nearby. This is the "Easter egg" reading and is consistent with the reuse; it predicts the constant is the digest of something short and human.

**H4 — K-163 belongs to the same procedure.** sect163k1 is a Certicom curve from the same years. Its half has a 126-bit x, not 160-bit, and shares nothing with the secp constant. If the procedure was "hash a string, use the digest as x", a 128-bit digest (MD5) on the binary curve and a 160-bit one (SHA-1) on the prime curves is a perfectly plausible pair; the top two bits being zero on K-163 would then be either chance (¼) or a masking step.

## 4. Search plan

1. **Core-matched preimage search.** *First pass done 2026-10-20* (`scripts/secg_core_search.py`, `results/secg-core-search.txt`): the existing K-163 string set (Solinas-lore phrases, names, organisations, curve names, every 1997–98 date in 13 formats, run timestamps; case/punctuation/encoding variants; X9.62-style counters) under SHA-1, SHA-0, RIPEMD-160, SHA-1∘SHA-1 and SHA-1∘MD5, three byte orders, matching bits 4–151 against the core — no hit. The string set is NIST/NSA-centred; the Certicom-era extension below has not been run. Reuse `scripts/k163/search.py` with a matcher that tests *bits 4–151 only* of each candidate digest against the core, for SHA-1, SHA-0, RIPEMD-160 (160-bit) and, for completeness, MD5/MD4/RIPEMD-128 against the K-163 value. Inputs: the existing Certicom-era string set, extended with SEC/SECG/Certicom names, people (Vanstone, Menezes, Qu, Brown, Gallant, Lambert, Johnson, Solinas), curve names in every spelling (secp256k1, sec256k1, "Koblitz 256", ansip256k1), the SEC 1/2 draft dates (1999–2000), and the SEC 2 SEEDs of the r-curves (which embed the ASCII "Minghua Qu" — the same people were clearly putting names into constants).
2. **Explain the per-curve tail.** *Partly done 2026-10-20.* For …9c60 + i, i = 0…15, on each curve (`-` not on curve, `on` on curve, `G` the used x; `e`/`o` parity of y(P), `<`/`>` y(P) below/above p/2 — for the used x this is the actual P = G/2, for the others the textbook root):

   ```
   secp160k1  0:one< 1:ono> 2:Ge> 3:ono> 4:- 5:- 6:ono> 7:- 8:- 9:- 10:- 11:- 12:ono> 13:ono> 14:- 15:one<
   secp192k1  0:ono> 1:one> 2:- 3:- 4:- 5:- 6:Ge> 7:ono< 8:- 9:one> 10:ono> 11:ono> 12:- 13:- 14:ono> 15:-
   secp224k1  0:- 1:- 2:ono> 3:Ge> 4:- 5:one< 6:- 7:- 8:one< 9:- 10:ono> 11:- 12:one< 13:ono> 14:- 15:ono>
   secp256k1  0:- 1:one< 2:- 3:Ge> 4:one< 5:- 6:- 7:- 8:ono< 9:- 10:one< 11:ono< 12:ono> 13:- 14:- 15:one<
   ```

   The used P has even y above p/2 on all four — but "first x whose even root is above p/2" picks i = 0 on secp192k1, and "first x on the curve" picks 0, 0, 2, 1. Neither parity nor the half-plane of y, alone or together, selects 2, 6, 3, 3. So either the last nibble is not an increment from …9c60 (it could be part of the constant, with the four curves derived from slightly different inputs — hard to square with 148 shared bits), or the acceptance test involves something else: the doubled point, a prime-order check that is vacuous here but was coded anyway, or a property of the compressed encoding.
3. **Explain the top byte.** Test whether `48`/`78` and `3b`/`554123b` are consistent with (a) a counter, (b) the top bytes of a second digest of the same string with a counter, (c) the X9.62 seed-to-field expansion applied to a 160-bit input, (d) a value reduced mod p for a *different* p than the curve's own (e.g. the 160-bit value reduced mod the secp160k1 prime, then reused).
4. **secp160r1 / secp160r2.** 92 shared leading bits between x(G) on r1 and x(G/2) on r2 is the same kind of fact: find what fixes the top 92 bits and what varies the bottom 68. Compute the half-generators of the *other* SEC 1 curves (sect\*, including the binary r-curves) and the ANSI X9.62 binary examples for shared prefixes.
5. **Archival.** SEC 1 and SEC 2 drafts (1999–2000), the IEEE P1363 working-group archives, WTLS, the ANSI X9.62 and X9.63 drafts, and Certicom's own test-vector documents. A changed generator in any draft dates the constant; a generator *with* a stated derivation ends the search.
6. **Then the NIST curves.** P-224/256/384/521 showed nothing in the subgroup scan. Rerun with the complete cofactor-preimage sets (trivial for h = 1) and with the lookup widened to X9.62-style expansions of candidate strings, in case the NIST-era program hashed-and-expanded where Certicom hashed-and-adjusted.

## 5. Where things live

- `scripts/secg_scan.py`, `results/secg-halfpoints.txt` — the SEC 2 prime-curve scan.
- `scripts/binpts.*`, `results/binpts.out` — the NIST binary curves (K-163 half at §7.1).
- `scripts/k163/` — the hash-search harness; `search.py` takes a 16-byte target today and needs the core-matcher of step 1.
- `notes/base-point-brief.md` — the earlier hand-off document; §2a–2b there are superseded by this file where they disagree.
