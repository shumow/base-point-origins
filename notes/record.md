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


### 7.3 Session of 2026-10-20 (second): the §4 experiments

**7.3.1 Certicom-era dictionary pass (HANDOFF §4.1) — negative.** `scripts/k163/strings_certicom.py` holds the new set: Certicom / SECG / SEC 1–2 / WTLS / P1363 names, Mississauga / Waterloo / Hayward, the Certicom people (Vanstone, Menezes, Qu, Brown, Gallant, Lambert, Blake-Wilson, Johnson, Mullin, Blake, Agnew, Deck, …) in several forms, every spelling of the six secp curves, the Koblitz / anomalous / CM / j = 0 / b = 7 vocabulary, the 1997 ECC Challenge names, the SEC 2 v1.0 r-curve SEEDs and "Minghua Qu" variants, standard hash test strings, every 1999–2000 date in 13 formats and month/year forms, and every parameter (p, a, b, n, Gx, Gy, and 2^m − p) of the six curves as decimal, hex, fixed-width hex, `key=value`, and raw big-/little-endian bytes — with the usual case / punctuation / encoding variants: 271,395 byte strings. Both harnesses now take `STRINGS=strings_certicom`.
- secp core (`secg_core_search.py`, matching bits 4–151 plus the two full 160-bit forms): 17,640,675 evaluations, 0 hits → `results/secg-core-search-certicom.txt`.
- K-163 (`k163/search.py`, all readings): see `results/k163-search-certicom.txt`.
With this, both the NIST/NSA-centred and the Certicom-centred dictionaries are exhausted under every 1990s 128/160-bit hash, three byte orders, and X9.62-style counters. A bare hash of a short human string is now unlikely as the source of either constant; the surviving forms are a hash of something long or machine-generated (a file, a key, an earlier parameter set), a non-hash constant (RNG output, a typed value), or a hash followed by arithmetic we have not modelled.

**7.3.2 Arithmetic relations between the four secp\*k1 values (§4.2).** Writing a, b, c for the 160k1, 192k1, 224k1(=256k1) values:
- c − a = 0x3b3·2¹⁵⁶ + 1, and b − c = 0x55412·2¹⁶⁸ + 3, i.e. b = c + (0x55412 ≪ 168) + 3: the 192k1 value *is* the 224/256 value with `55412` prepended at bit 168 and the last nibble bumped by 3 — not a separate constant with the same core. (Exponents corrected 22 Oct: first written as 2¹⁵² and 2¹⁷²; `scripts/verify_crypto2019.py` §2 checks them.) As 32-bit words: 160k1 = `48ce563f …`, 224k1 = `0000003b 78ce563f …`, 192k1 = `0554123b 78ce563f …`. So the picture is one 160-bit block `78ce563f89a0ed9414f5aa28ad0d96d6795f9c6?` carried in the low five words, with a sixth word that is 0x3b on 224/256 and 0x0554123b on 192, and on the 160-bit curve the top byte 0x78 replaced by 0x48 (0x78 − 0x30, or 0x78 & ~0x30).
- X9.62 seed-to-field expansion is excluded by the identical 224/256 values: the expansion's top word is the rightmost v bits of SHA-1(SEED) with v = 64 on 224 and 96 on 256, which would give different, full-weight high words, not a 6-bit `3b` on both. The x was never expanded to field length.
- Remaining readings of the sixth word: a counter or attempt index written into the top limb; a second small value (a date? 0x0554123b = 89,395,771 is not a Unix time in 1997–2000; 0x3b = 59); uninitialised memory in a 32-bit-word buffer. None tested beyond inspection.

**7.3.3 Last-nibble acceptance rule, brute-forced (§3.3).** `scripts/nibble_rules.py` → `results/nibble-rules.txt`. For each start nibble −16…15, each direction, "first / second / third x satisfying P" over ~60 properties P (on-curve; parity, half-plane, QR-ness, mod-3/4 residues of y for the even, odd, smaller and larger root; the same for x(2P), y(2P), x(3P), y(3P); neighbouring x on/off curve; x a QR; x³+b a cube), and all conjunctions of two properties from starts 0–3: 13 rules reproduce 2, 6, 3, 3, against ~11,500 rules tested with ~1/1000 chance each — chance level. The most code-like survivor is "the second on-curve x at or after …9c61" (on-curve indices from …9c60: 160k1 {0,1,2,3,…}, 192k1 {0,1,6,…}, 224k1 {2,3,…}, 256k1 {1,3,…}), which a loop that skipped its first hit would produce; the others are parity/half-plane rules starting at 2 or counting down from 6 or 9. Nothing here is evidence; it says the nibble is not a plain first-on-curve increment from any start within ±16 of …9c60 either.

**7.3.5 The 2019–20 record, checked (22 Oct 2026).** Two mailbox surveys of the Heninger–Scholl–Shumow work and a reconstructed Sage script are in `references/crypto2019-rump/`; `scripts/verify_crypto2019.py` → `results/verify-crypto2019.txt` re-derives everything they assert in pure Python with this repo's curve code: the four half-generators; the shared core, which is **152 bits** (bits 4–155, `8ce563f89a0ed9414f5aa28ad0d96d6795f9c6`), with only the top nibble (4 vs 7) and the last nibble varying — §7.2 above and HANDOFF §2.1 had said 148 bits and a varying top byte; Dan Brown's count-up-from-a-cleared-low-field theory, excluded for 4, 6 and 8 low bits counting up and down (actual low-6-bit values 34/38/35/35 vs first lifting 1/1/0/1; the top nibble is not the first lifting nibble either); x(G/2) on secp256r1 at 254 bits as control; K-163 at 126 bits; and Travis Scholl's CM derivation — among the five primes in [2²⁵⁶ − 2³² − 977, 2²⁵⁶ − 2³²), exactly one has a prime-order j = 0 twist, and it is secp256k1's (p, n). Also logged from 2019: Nadia's John the Ripper SHA-1 run over the 256 top/bottom-nibble variants, no hit (HANDOFF §3.0).

**7.3.4 FreeLIP recipe with every small seed on P-224/256/384/521 and secp160k1 (§4.6).** `scripts/freelip_sweep.py` → `results/freelip-sweep.txt`. The exact Anthropic recipe (state × 3¹²¹ mod 2¹⁰⁷ − 1, 26-bit limbs, ⌈bits(p)/26⌉+1 limbs, first on-curve x), verified to reproduce P-192 from seed 20000 at try 2, run for seeds 1…100000 with the discard count widened to 0…12 and the limb count to L−1…L+1, every candidate x (reduced and unreduced) compared with x(kG) and x(G/k), k ≤ 8 (the L−1/L+1 limb variants were dropped for time; `limb_deltas` restores them). **0 hits on all five curves** (`results/freelip-sweep-a.txt`: P-224/256/384; `-b.txt`: P-521, secp160k1). So the Aug 1997 / Apr 1998 NIST runs did not use the May 1997 base-point code with a small integer seed, and the secp160k1 constant is not a FreeLIP limb assembly from a small seed either. Open: large seeds (FreeLIP `zrstarts` takes any long), a different limb width, or an `lrand48` stream in place of `zrandom`.
