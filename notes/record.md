# Record: base-point structure found so far

*Carried over verbatim from `notes/cm-hypothesis.md` Part C of [ECDSA-Origins-Revealed-Followup](https://github.com/shumow/ECDSA-Origins-Revealed-Followup) on 2026-10-20; section numbers 7, 7.1, 7.2 are the original ones. File paths refer to this repository's `scripts/` and `results/`, which carry the same names.*

## Part C. Base-point structure (separate from the skips)

### Integration update (24 October 2026)

Selectively ported the structured-value experiment from
`claude/determined-ride-l5ppv0` (`9a6095e`), not the branch's older research
notes or overlapping top-byte script. The corrected run of
[`nothing_up_my_sleeve.py`](../scripts/nothing_up_my_sleeve.py) records
20 direct sources, 66 hash inputs, **4,290** secp-core evaluations and
**594** unsuffixed K-163 evaluations, all without hits
([manifest](../results/nothing-up-my-sleeve.json),
[summary](../results/nothing-up-my-sleeve.txt)).
The branch mislabeled 66 candidates as 66 secp hash evaluations and duplicated
the little-endian MD5 IV under the word-order label; both are corrected.
The search deliberately keeps the existing broader 148-bit mask even though
the actual shared block is 152 bits. Direct checks cover only as-is and
hex-character-reversed substrings, not byte reversal, complements or modular
reduction; the precise corpus, encodings and matcher coverage are in
[`experiment-shortlist.md`](experiment-shortlist.md) §1.

The additional bounded reduction check from the top-byte experiment is now
§8 of [`high_bytes_analysis.py`](../scripts/high_bytes_analysis.py)
([regenerated report](../results/high-bytes-analysis.txt)):
reduce each observed full half-x and its low-160 form modulo each other curve's
prime, compare to the observed full target. Only the known 224k1/256k1
identity matches (quotient zero); no nonzero-quotient match.
This does not exclude an arbitrary common integer before reduction or any
unexamined counter/expansion construction. Planted reduction and hash controls,
corpus precision checks, and manifest-count regressions accompany the port.

Validation: the 26 focused tests pass on native Windows Python. The existing
`python scripts/local.py test` launcher verifies container isolation and runs
120 tests in restricted local WSL/Docker, with no failures and one skip
(SageMath is not installed in that image); the PARI check passes. Re-running
the corpus in the sandbox reproduces all results, coverage metadata and
checksums from the Windows run; only the recorded Python/OpenSSL versions
differ. No GPU campaign was launched.

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
- Remaining readings of the sixth word: a counter or attempt index written into the top limb; a second small value (a date? 0x0554123b = 89,395,771 is not a Unix time in 1997–2000; 0x3b = 59); uninitialised memory in a 32-bit-word buffer. These were tested on 23 Oct — see §7.3.7.

**7.3.3 Last-nibble acceptance rule, brute-forced (§3.3).** `scripts/nibble_rules.py` → `results/nibble-rules.txt`. For each start nibble −16…15, each direction, "first / second / third x satisfying P" over ~60 properties P (on-curve; parity, half-plane, QR-ness, mod-3/4 residues of y for the even, odd, smaller and larger root; the same for x(2P), y(2P), x(3P), y(3P); neighbouring x on/off curve; x a QR; x³+b a cube), and all conjunctions of two properties from starts 0–3: 13 rules reproduce 2, 6, 3, 3, against ~11,500 rules tested with ~1/1000 chance each — chance level. The most code-like survivor is "the second on-curve x at or after …9c61" (on-curve indices from …9c60: 160k1 {0,1,2,3,…}, 192k1 {0,1,6,…}, 224k1 {2,3,…}, 256k1 {1,3,…}), which a loop that skipped its first hit would produce; the others are parity/half-plane rules starting at 2 or counting down from 6 or 9. Nothing here is evidence; it says the nibble is not a plain first-on-curve increment from any start within ±16 of …9c60 either.

**7.3.4 FreeLIP recipe with every small seed on P-224/256/384/521 and secp160k1 (§4.6).** `scripts/freelip_sweep.py` → `results/freelip-sweep.txt`. The exact Anthropic recipe (state × 3¹²¹ mod 2¹⁰⁷ − 1, 26-bit limbs, ⌈bits(p)/26⌉+1 limbs, first on-curve x), verified to reproduce P-192 from seed 20000 at try 2, run for seeds 1…100000 with the discard count widened to 0…12 and the limb count to L−1…L+1, every candidate x (reduced and unreduced) compared with x(kG) and x(G/k), k ≤ 8 (the L−1/L+1 limb variants were dropped for time; `limb_deltas` restores them). **0 hits on all five curves** (`results/freelip-sweep-a.txt`: P-224/256/384; `-b.txt`: P-521, secp160k1). So the Aug 1997 / Apr 1998 NIST runs did not use the May 1997 base-point code with a small integer seed, and the secp160k1 constant is not a FreeLIP limb assembly from a small seed either. Open: large seeds (FreeLIP `zrstarts` takes any long), a different limb width, or an `lrand48` stream in place of `zrandom`.

**7.3.5 The 2019–20 record, checked (22 Oct 2026).** Two mailbox surveys of the Heninger–Scholl–Shumow work and a reconstructed Sage script are in `references/crypto2019-rump/` (the README there says what rests on the slides, on mail, and on computation). `scripts/verify_crypto2019.py` → `results/verify-crypto2019.txt` re-derives everything they assert in pure Python with this repo's curve code, and `halve_generators.sage` → `results/verify-crypto2019-sage.txt` does the same in Sage with proof-enabled primality; `tests/test_crypto2019.py` runs both: the four half-generators; the shared core, which is **152 bits** (bits 4–155, `8ce563f89a0ed9414f5aa28ad0d96d6795f9c6`), with only the top nibble (4 vs 7) and the last nibble varying — §7.2 above and HANDOFF §2.1 had said 148 bits and a varying top byte; Dan Brown's count-from-a-cleared-low-field theory, excluded for 4, 6 and 8 low bits counting up and down (actual low-6-bit values 34/38/35/35 vs first lifting 1/1/0/1), and for the top nibble in both directions; a counter applied before a hash or other transform is not tested; x(G/2) on secp256r1 at 254 bits as control; K-163 at 126 bits; and Travis Scholl's CM derivation — the window [2²⁵⁶ − 2³² − 977, 2²⁵⁶ − 2³²) holds **seven** primes (offsets 977, 949, 739, 487, 361, 359, 263), three of them 1 mod 3, whose 18 j = 0 twist orders include exactly one prime: secp256k1's (p, n). Also logged from 2019: Nadia's John the Ripper SHA-1 run over the 256 top/bottom-nibble variants, no hit, candidate coverage unknown (HANDOFF §3.0).

**7.3.6 Dan's June 2020 sect\*k1 searches, recovered and replicated (23 Oct 2026).** The private `factorable/secp256k1` repo turned out to hold five files, all Dan's (`references/crypto2019-rump/factorable-secp256k1/`): parameter checks, a search, its output, and an endomorphism test. `scripts/sectk_2020_checks.py` → `results/sectk-2020-checks.txt` re-runs them in pure Python on this repo's binary-curve code (with an extended-Euclid field inverse swapped in for `binpts.gf_inv`, checked against it). (a) The 2020 search examined, for each sect\*k1 curve, x(σᵏ(2⁻ʲ·G) + T) for 0 ≤ j, k < m and T ∈ E[h] = E(F₂): m²·h points, a scalar set disjoint from the k ≤ 2¹⁶ scans of §7.1. Its recorded minima are reproduced exactly from their (k, j): 126 bits on sect163k1 (G/2 itself), then 215, 219, 266, 390, 549 bits on sect233/239/283/409/571k1 against uniform expectations of 216, 222, 265, 390, 551 — nothing but K-163. The full grid was re-run here on 23 Oct 2026 (`python3 scripts/sectk_2020_checks.py --full`, ~25 min CPU, exit 0; `results/sectk-2020-full-grid.txt`): the recorded minimum is the **global** minimum of the m²·h grid on every one of the six curves, each at the recorded (k, j) — sect163k1 (k=0, j=1), sect233k1 (k=89, j=45), sect239k1 (k=56, j=153), sect283k1 (k=18, j=13), sect409k1 (k=134, j=139), sect571k1 (k=261, j=265) — so the 2020 search missed no shorter coordinate, and K-163 remains the sole short one. (b) The hypothesis G = P + σ(P) with P short, which the 2020 file tested on sect233k1 only and recorded no answer for: on the prime-order subgroup σ is the scalar λ (root of λ² − μλ + 2 mod n, μ = (−1)^(1−a), confirmed by σ(G) = λG), so P = (1 + λ)⁻¹·G; its x, and the x of P + T for every T ∈ E[h], are full-size on all six curves, and likewise for (1 − λ)⁻¹·G. Planted controls in `tests/test_sectk2020.py`: a generator built as P₀ + σ(P₀) is inverted back to P₀, and the grid evaluation returns the planted point's coset minimum.

**7.3.7 The top byte and the 192k1 prefix, tested (23 Oct 2026, §4.2; scope narrowed 23 Oct after review).** `scripts/high_bytes_analysis.py` → `results/high-bytes-analysis.txt` (controls in `tests/test_high_bytes.py`, 8 tests). The structure is confirmed invertibly: one 160-bit block `V = 78ce563f89a0ed9414f5aa28ad0d96d6795f9c6?` (middle 152 bits fixed, top and bottom nibbles soft) underlies all four; secp224k1 and secp256k1 are **byte-for-byte identical** at x(G/2) (same V, same high byte 0x3b, same last nibble 3). Above V the high material is 0x3b on 192/224/256 (with 0x55412 extra on 192k1) and absent on 160k1, which instead has 0x30 cleared from V's top byte (0x78 → 0x48). What each test establishes, with its scope:
  - *FIPS 186 / X9.62 field-element expansion from one seed — **excluded exactly**.* It would MATCH the shared low-160 bits of 192/224/256 (those are W₁ = SHA-1(SEED+1)), which is why it looked plausible; but a single seed forces the rightmost 32 bits of SHA-1(SEED) to be both `0554123b` (from 192k1) and `0000003b` (from 224k1), a contradiction, and the high field would be a full-weight hash slice, not a 6-bit `3b` (weight ≈ 2⁻⁵⁸). So the x was never expanded to field length from one seed. (Second, cleaner route to the §7.3.2 exclusion.)
  - *Truncation of one long constant to field size, or a byte stream read longer for bigger fields — **excluded exactly**.* secp192k1 carries **more** high material (27 bits) than secp224k1/256k1 (6 bits) over a **smaller** field.
  - *Per-curve counter or uninitialised top limb — **disfavoured, not excluded**.* 224k1 and 256k1 carry the identical 0x3b and 192k1 shares it as its low high-byte; a free-running counter or leftover memory would be expected to differ between runs. A counter restarted for each run, or buffer state reused between runs, would repeat and is not excluded.
  - *A function of the curve's own parameters — **bounded**.* None of 0x3b, 0x55412, 0x554123b equals any curve's Mersenne offset (2^f − p), the low word of p or n, the trace p+1−n, or b; and V and the full values are not SHA-1/MD5/SHA-256 of p or n in six byte/ASCII encodings (0 hits). Those five quantities and three hashes are all that was tried; arbitrary other functions of p or n are untested.
  - *A forced top byte on 160k1 — **no field-level cause found**.* 0x78-topped `78ce…9c62` is < p(secp160k1) (no reduction), has the same 159-bit length as the published value (no length mask), and both 0x48 and 0x78 top bytes admit on-curve lifts at the published nibble 2. A deliberate 2-bit edit is the simplest reading.
  Net: the high bytes are small, reused where curves share V, and not produced by the specific expansions, truncations, counters, dates or parameter quantities tried. **Working hypothesis, not a result:** they are hand-assigned tags written into the top 32-bit limb of a fixed-width buffer holding V. The sub-constant most worth naming is the 0x3b shared by three curves (=59, ASCII ';'); 0x55412 on 192k1 and the 0x30 top-byte clear on 160k1 are the two curve-specific extras. Still open: what 0x3b, 0x55412 and the 0x30 clear *mean*; the counter-before-hash readings are tested in §7.3.8–7.3.10, each in a bounded domain.

**7.3.8 Counter-before-hash on the secp160k1 top byte, modelled (23 Oct 2026, §4.2(b); restated as a heuristic 23 Oct after review).** `scripts/counter_before_hash.py` → `results/counter-before-hash.txt` (controls `tests/test_counter_before_hash.py`, 8 tests). The §7.3.3 test added a counter to the hash *output*; this models a counter folded into the hash *input* (SHA-1(seed‖i), SHA-1(seed+i), several placements), as Dan Brown's theory (§7.3.5) suggests. **Result: disfavoured as the source of the top byte, on a probabilistic heuristic — not disproved.** The "top byte" difference is really the nibble at bits 156–159 (0x4 on 160k1, 0x7 on the others; bits 152–155 = 0x8 lie inside the shared core). If value = HASH(input), then under an independent-hash heuristic two different inputs agree on bits 4–155 with probability ≈ 2⁻¹⁵² per pair, so with overwhelming likelihood the four share one hashed input, and one input gives one output everywhere — including bits 156–159. The likely reading is that the split top nibble is a post-hash edit and a counter in the input, if any, produced only the shared digest V. A 152-bit projection is many-to-one and no hash property makes it injective, so this is a heuristic, not a contradiction, and it does not show that every counter-before-hash scheme requires a post-hash edit. Illustration, not proof: over 64 seeds (384 curve-pairs) a per-curve accept-first-lift loop yields **0** pairs with the observed signature (shared 152-bit core but different top nibble); the real data shows that signature on 3 of 6 pairs (secp160k1 against each of the other three; the pairs among 192/224/256 share the top nibble 7 as well as the core). Separately, a bounded input-counter dictionary probe (Certicom wordlist, 6,939 base strings, counter 0..127, two encodings, six input placements, SHA-1 and RIPEMD-160, 21,316,608 evaluations; manifest `results/counter-before-hash-probe.json`) finds 0 hits on the core in that domain — a negative over that domain only, consistent with §3.2/§4.1. Untested here: a counter before a *second* hash or transform of the digest (§7.3.9) and any input outside the probe.

**7.3.9 Counter-before-second-hash (the two-stage variant), modelled (23 Oct 2026, §4.2(b)).** `scripts/counter_second_hash.py` → `results/counter-second-hash.txt` (controls `tests/test_counter_second_hash.py`, 4 tests, incl. a planted-counter recovery). This is the branch §7.3.8 does **not** reach: a construction where the low 160 bits are V = H1(seed), counter-free (so V stays shared across curves), and the high limb above V is a second hash or transform of the digest with a per-curve counter — `high = g(H2(V, i))`. Because stage 2 operates on the digest V, which we know, it is directly testable without the seed. Tested, against the 32-bit high limbs 0x0000003b (224/256k1) and 0x0554123b (192k1): (A) plain transforms of V (CRC32, Adler32, word sum/xor, top/low 32) — 0 hits; (B) windows of H2(V) with no counter for nine hashes — 0 limb hits; (C) counter before the second hash, `H2(enc(V, i))` for six fast hashes to i < 2¹⁶ and three pure-Python hashes to i < 2¹², five input placements, fourteen 32-bit window readings, and each of the three V forms (`…9c60`, `…9c63`, `…9c66` — so the 192k1 limb is tested above its own low-160 block; the first run of 23 Oct used `…9c63` only and was widened the same day), **76,677,120 window checks** — no small counter reproduces either limb, and **no single (hash, encoding, reading) yields both**. Limits recorded in the script: a 6-bit target (0x3b) is met by ~1/64 of counters so means nothing alone; a large counter could hit any 32-bit target by luck (~2⁻³²), so the bounded sweep tests the small-counter regime a real recipe would use, not impossibility; other transforms, hashes, placements or larger counters are untested; if stage 2 hashes the **seed** rather than the digest it is modelled over candidate seeds in §7.3.10; and SHA-1 step inversion (`sha1_steps.py`) needs a full 160-bit target, not a 6–32 bit limb, so it does not apply. Net: in the domain tested (three V forms, nine hashes, five placements, the counters and readings above) the two-stage digest-input variant is unsupported; the working hypothesis for the high material stays a hand-assigned tag (§7.3.7), which this does not establish.

**7.3.10 Stage 2 hashing the seed, with candidate seeds (23 Oct 2026, §4.2(b); witnesses and scope revised 23 Oct after review).** `scripts/seed_two_stage.py` → `results/seed-two-stage.txt` (controls `tests/test_seed_two_stage.py`, 6 tests, incl. a planted joint hit driven through the production entry point `main` and recovered as a byte-exact witness). §7.3.9 could not reach the form where stage 2 hashes the unknown *seed* rather than the digest; with candidate seeds it becomes checkable, because a seed must now clear **both** stages — produce V at stage 1 (the §3.2/§4.1 search) *and* a high limb at stage 2 — and a seed clearing only one is not a solution. Every hit is reported with the seed bytes (`input_hex`), the stage-1 hash and suffix, and the stage-2 hash, placement, reading, counter and exact bytes hashed, so a positive would be reproducible from the report alone. Candidate corpus: the Certicom wordlist and the six curves' own p, n (hex and decimal), in ASCII and UTF-16-LE, 13,910 seed-encodings. Three models over them, all negative: **stage 1** (seed → V core, five 160-bit hashes with the X9.62-style suffixes, 904,150 checks) 0 hits, re-confirming §4.1 in the joint harness; **stage 2** (high limb as a full 32-bit word 0x0000003b or 0x0554123b from `H2(seed‖i)`, four placements, counter 0..255, four hashes, twelve window readings, 655,216,640 checks) 0 hits — both limbs are 32-bit targets here (~2⁻³² each, ~0.3 expected spurious total), so the negative is discriminating, not a throwaway 6-bit reading; **unified** (the whole value 0x48ce…/0x3b78…/0x554123b78… as a windowed slice of one wide hash — SHA-256, SHA-512, SHA-1‖SHA-1 — of the seed, every bit offset, 32,410,300 checks) 0 hits; and **joint** (one seed clearing both stages) 0. This is a bounded negative over that corpus, those hashes, placements and counters; it does not exclude the construction for a seed outside the corpus (a long or machine-generated input, or any string not in the wordlist), another hash, or a larger counter. With §7.3.8 and §7.3.9 the counter-before-hash family is unsupported in every domain tested so far, each domain being explicit above. The working hypothesis for the high material stays a hand-assigned tag (§7.3.7), which these searches do not establish.
