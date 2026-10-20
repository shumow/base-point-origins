# Record: base-point structure found so far

*Carried over verbatim from `notes/cm-hypothesis.md` Part C of [ECDSA-Origins-Revealed-Followup](https://github.com/shumow/ECDSA-Origins-Revealed-Followup) on 2026-10-20; section numbers 7, 7.1, 7.2 are the original ones. File paths refer to this repository's `scripts/` and `results/`, which carry the same names.*

## Part C. Base-point structure (separate from the skips)

## 7. Base-point structure

For all ten published prime-field generators (P-192, P-224, P-256, P-384, P-521, prime192v2/v3, prime239v1/v2/v3; parameters verified by n·G = O), computed k·G and (k⁻¹ mod n)·G for 2 ≤ k ≤ 2¹⁶ and recorded the bit length of x and of min(y, p − y) (so negations are covered). Looking for a hash-sized coordinate — 128 bits (MD5) or 160 bits (SHA-1) — or anything else far below the field size:

| Curve | G/2 x-coordinate | shortest x found, k ≤ 2¹⁶ either way | rough expected min of 2¹⁷ random |
|---|---|---|---|
| P-192 | full size | 174 bits (61807·G) | ~175 |
| prime192v2 | full size | 175 bits (G/7467) | ~175 |
| prime192v3 | full size | 176 bits (9061·G) | ~175 |
| P-224 | full size | 208 bits (G/42457) | ~207 |
| prime239v1 | full size | 222 bits (41569·G) | ~222 |
| prime239v2 | full size | 220 bits (G/40829) | ~222 |
| prime239v3 | full size | 221 bits (4319·G) | ~222 |
| P-256 | full size | 237 bits (G/53620) | ~239 |
| P-384 | full size | 367 bits (14971·G) | ~367 |
| P-521 | full size | 502 bits (10735·G) | ~504 |

Every reported minimum x is within two bits of the rough minimum expected from 2¹⁷ uniform field elements. The prime-field scan finds no bare 128/160-bit coordinate within its radius. For these cofactor-1 curves, subgroup division is unique. Expanded hashes, RNG seeds, scalar mappings, and larger multipliers remain possible; see `base-point-brief.md`.

### 7.1 Binary curves: the K-163 half-point

The same scan over GF(2^m) (PARI/GP with `ffgen`; parameters from the std-curves database, each verified by G ∈ E and n·G = O) for the ten NIST binary curves — k·G for 2 ≤ k ≤ 2¹⁶ and G/k for 2 ≤ k ≤ 2¹², negations covered via y ↦ x + y. Results (`binpts.gp`, `binpts.out`):

| Curve | h | G/2 x bits | shortest x found | random expectation |
|---|---|---|---|---|
| B-163 | 2 | 163 | 147 (37609·G) | ~147 |
| **K-163** | **2** | **126** | **126 (G/2)** | ~147 |
| B-233 | 2 | 232 | 215 (G/1579) | ~217 |
| K-233 | 4 | 232 | 219 | ~217 |
| B-283 | 2 | 283 | 267 | ~267 |
| K-283 | 4 | 281 | 267 | ~267 |
| B-409 | 2 | 408 | 391 | ~393 |
| K-409 | 4 | 409 | 393 | ~393 |
| B-571 | 2 | 571 | 554 | ~555 |
| K-571 | 4 | 555 | 555 | ~555 |

Nine of ten are random-looking. **K-163 is not.** Its half-point G/2 = ((n+1)/2)·G is

x = 0x23e21d6019e1211f6bd47ec180256e97 (126 bits), y = 161 bits,

a 128-bit-sized x-coordinate on a 163-bit curve. Under a uniform-coordinate heuristic, a specified x meets this threshold with probability 2⁻³⁷. There were 69,630 point evaluations per binary curve, 696,300 total, giving about 5.1 × 10⁻⁶ expected x-hits. Across both prime and binary scans, allowing x and both y signs gives a rough trial-count heuristic of 4.4 × 10⁻⁵, before other exploratory pattern choices. These are not calibrated discovery probabilities, and novelty has not been established.

A plausible reading is that a 128-bit x was chosen, y solved, and the cofactor applied. This is not a recovered recipe. Cofactor clearing has multiple rational preimages: if Q = [h⁻¹ mod n]G, they are Q + T for T in E(F_{2^m})[h], not just Q. Review checked all 28 such preimages across the ten binary curves. No additional 128-bit-x hit appears; K-163's other half has a 162-bit x. The larger k scans remain subgroup-only, so they do not exclude every cofactor-clearing construction.

**Coordinate and search correction (19 October).** `fromdigits(Vecrev(Vec(f.pol)),2)` reversed the 126 coefficient bits when printing the coordinate. The old value `3a5da90060df8af5be2121e601ae11f1` is that reversal, not the standard polynomial-basis integer. Removing `Vecrev` gives the coordinate above; the degree-based bit count was unaffected. All ten decimal exports and the hash-search target are corrected, and Python/PARI regression checks agree. The previous negative hash searches used the wrong target and do not apply to the corrected one; the full sweep was rerun against the corrected target on 19 October with the same string set and hash readings: 29,577,717 evaluations, no hits (`results/k163-search-rerun.txt`). The corrected 32-bit words have top bits 0,0,0,1, excluding four consecutive 31-bit `lrand48` words in that reading only.

### 7.2 The SEC 2 curves: a half-generator constant shared across four Koblitz curves

The same scan (k·G, k ≤ 2¹⁶; G/k, k ≤ 2¹²; all cofactor preimages where h > 1) run on the ten SEC 2 prime-field curves not already covered — secp112r1/r2, secp128r1/r2, secp160k1/r1/r2, secp192k1, secp224k1, secp256k1; parameters from SEC 2 v1.0 and v2.0, n·G = O verified for each (`scripts/secg_scan.py`, `results/secg-halfpoints.txt`). This reproduces, and extends to the full SEC 2 list, the observation in the Heninger–Scholl–Shumow Crypto 2019 rump-session talk, whose title *is* x(G/2) on secp160k1 (`48ce563f89a0ed9414f5aa28ad0d96d6795f9c62`).

Six of the ten look random: shortest coordinates within a few bits of the 2¹⁶ + 2¹² uniform expectation, and the cofactor preimages on the two h = 4 curves full-size. The four Koblitz curves do not:

```
secp160k1  x(G/2) =        48ce563f89a0ed9414f5aa28ad0d96d6795f9c62   (159 bits on 160)
secp192k1  x(G/2) = 554123b78ce563f89a0ed9414f5aa28ad0d96d6795f9c66   (187 on 192)
secp224k1  x(G/2) =      3b78ce563f89a0ed9414f5aa28ad0d96d6795f9c63   (166 on 224)
secp256k1  x(G/2) =      3b78ce563f89a0ed9414f5aa28ad0d96d6795f9c63   (166 on 256)
```

secp224k1 and secp256k1 have the *identical* 166-bit x at G/2. All four share the 148-bit core `ce563f89a0ed9414f5aa28ad0d96d6795f9c6`; three share `3b78` above it (192k1 has a further `55412` above that); the last nibbles are 2, 6, 3, 3. So the generators of Certicom's secp*k1 curves were built from one constant, by the recipe this record has been hypothesising for K-163 — choose x, solve y, double — and the constant was reused across fields. What produced the constant, why its high part differs between fields, and what set the last nibble are not resolved: a simple "smallest increment of …9c60 that lands on the curve" fails (…9c60 is already on secp160k1, …9c61 on secp256k1).

A second echo: x(G/2) on secp160r2 begins `4a96b5688ef573284664698`, the first 92 bits of x(G) on secp160r1 (`4a96b5688ef573284664698968c38bb913cbfc82`). The remaining 68 bits differ wholesale, which is not an increment either.

Against the rest: no shared substring of ≥ 32 bits between any SEC 2 half-generator and any NIST/ANSI prime or binary one, nor between any two NIST/ANSI ones; the K-163 value `23e21d6019e1211f6bd47ec180256e97` is not a substring or truncation of the secp constant. K-163 (sect163k1) is likewise a Certicom curve, so the secp*k1 pattern is the strongest external support so far for reading its short half as a chosen x. The things to try next on the constant itself are the same as for K-163 — fixed-width encodings and 1990s hashes of Certicom-era strings — but with a 148-bit core whose top and bottom are uncertain, so matching on the core rather than the full value.

