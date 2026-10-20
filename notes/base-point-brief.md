# Brief: the unexplained NIST base points (P-224, P-256, P-384, P-521)

*Hand-off document, written 2026-10-17 and corrected after review on 2026-10-19. The skipped-seed investigation is an exploratory negative result, not a closed question (see `cm-hypothesis.md`).*

*Working branch:* base-point work from 2026-10-20 on lives on the `base-points` branch, so that `main` stays the curve-selection (skipped-seed) story until something here is ready to merge.

## 1. What is settled

- **Fourteen recovered seeds out of fifteen NIST/ANSI prime and binary seeds**: the ten prime-field seeds and four binary-field seeds match `lrand48()` output (Anthropic, "Claude reveals ECDSA curve origins", 2026-10-16). B-163 remains unexplained. The phrase-hash story does not describe the fourteen recovered seeds.
- **Square-root convention**: for every published curve over p ≡ 3 (mod 4), b = (−27/c)^((p+1)/4) mod p, never the other root (seven of seven). This is evidence for the textbook routine, not proof of every code path or of the y-coordinate convention.
- **Base points for P-192 and the five ANSI X9.62 example curves** (prime192v2/v3, prime239v1/v2/v3): x-coordinates come from FreeLIP's `zrandom` (state × 3¹²¹ mod 2¹⁰⁷ − 1), seeded with small integers (20000, 20420, 20507, 20509, 20512, 20517), seven outputs discarded, 26-bit limbs assembled into x, first x on the curve taken. Reproducer on the Anthropic page. These were generated in May 1997.
- **Skipped viable seeds** (11 across the four prime runs, against 8 published): none of the tested rules separates them. This does not exclude other numerical criteria, run-specific code, intermediate-arithmetic bugs, or variable RNG consumption. Full write-up: `cm-hypothesis.md`.

## 2. What is open

- **Base points for P-224, P-256, P-384, P-521.** No derivation known to anyone. Anthropic tested the FreeLIP recipe and it does not fit. These curves were generated Aug 1997 (P-521, P-256, P-384) and Apr 1998 (P-224) — after the May 1997 FreeLIP-era runs, so the base-point code may have changed between runs.
- **Base points for the binary curves** (B-163 … B-571; also K-curves). Unexplained.
- **B-163 seed.** Unexplained.

## 2a. New lead: K-163 (found 2026-10-17, after this brief was first written)

On K-163 (Koblitz, b = 1, cofactor 2), the subgroup half-point G/2 = ((n+1)/2)·G has x = **0x23e21d6019e1211f6bd47ec180256e97** — 126 bits — with full-size y. Python and PARI independently verify G ∈ E, n·G = O, and 2·(G/2) = G. Choosing a 128-bit x and cofactor-clearing is a plausible explanation, not an established recipe. **The corrected primary target is `23e21d60 19e1211f 6bd47ec1 80256e97`.**

The initial PARI export reversed polynomial coefficients. Its earlier target `3a5da90060df8af5be2121e601ae11f1` is the reversal of the 126 coefficient bits, not the standard encoded coordinate. The reported ≈29.6 million negative evaluations used that wrong target and must not be treated as exclusions for the corrected value. The search script is corrected and the full sweep was repeated against the corrected target on 19 October: 29,577,717 evaluations, no hits (`results/k163-search-rerun.txt`). Four mistyped prime-run timestamps in the phrase inputs have also been corrected. Hash-function test vectors and bounded search controls are in `scripts/test_research.py`.

For cofactor clearing, the subgroup inverse is not the only input: all P with [h]P = G form Q + E(F_{2^m})[h]. All 28 rational cofactor preimages across the ten binary curves have now been checked. K-163 remains the only 128-bit-x hit; its other half has x = `389ff55b1717d231e466c6a90bef265d7ad1ca9a4` (162 bits). The larger k-multiple scans still cover subgroup points only.

## 2a′. The SEC 2 prime curves (added 2026-10-20)

The scan extended to secp112/128/160/192k1/224k1/256k1 (`results/secg-halfpoints.txt`, cm-hypothesis §7.2): secp224k1 and secp256k1 share x(G/2) = `3b78ce563f89a0ed9414f5aa28ad0d96d6795f9c63` exactly, and secp160k1/192k1 carry the same 148-bit core — the Crypto 2019 rump-session observation, now with all four. Certicom demonstrably built those generators as 2·P with a chosen x reused across fields. Work item: identify the constant (match on the core `ce563f89a0ed9414f5aa28ad0d96d6795f9c6`, since its top and last nibble vary), and explain the 92-bit prefix that x(G/2) of secp160r2 shares with x(G) of secp160r1.

## 2b. The binary-curve side (B and K curves)

Anthropic's post covers the binary curves only for seeds: B-233/283/409/571 are five full 31-bit `lrand48` words per candidate from one sitting on 1998-04-17 (clock apparently halved); B-163's seed fits nothing they tried. Binary base points get one sentence ("the same goes for the NIST binary curves" — unexplained). K curves are not mentioned: they have no seed (a ∈ {0,1}, b = 1), so for a Koblitz curve the generator is the *entire* provenance question. Three work items, in priority order:

**(i) K-163's half-point value.** Covered in §2a. First rerun the corrected target, including standard fixed-width encodings. A hit would establish a recipe; the shortness alone does not. The absence of a cofactor step in the prime-field FreeLIP recipe is not evidence for different source code, since those curves have h = 1.

**(ii) The other nine binary generators under the same method.** The subgroup scans find no coordinate at least 32 bits short on them. The additional complete cofactor-preimage check finds no 128-bit-x value either. This excludes that particular bare-128-bit-input model in the tested polynomial basis, not every digest, encoding, or mapping. For future lookups include every rational preimage of G/h, G/(2h), and G/(4h), rather than only their subgroup representatives. Compare with X9.62-style hash expansion, candidate seeds, 31/32-bit RNG layouts, and both clock conventions, with an explicit time-window and trial-count budget.

**(iii) B-163's seed.** `85E25BFE5C86226CDB12016F7553F9D0E693A268`. Nothing in the two posts explains it. Checklist: every 1990s C-library PRNG (`lrand48`/`mrand48`/`drand48` bit layouts, `rand()` from BSD and System V, `random()`, Park–Miller, Knuth's subtractive generator, Numerical Recipes `ran0/1/2`), each at every byte offset and word size, with and without the halved clock; a FreeLIP `zrandom` stream (it was on the same machine in 1997); seed = hash (MD5, SHA-0, SHA-1) of a short string, including the other 13 seeds, curve names, dates; seed derived from another seed (XOR/addition of two published seeds, byte permutation of one); hand-typed or hex-edited (look at the ASCII of the bytes, repeated nibbles, keyboard-adjacent hex). The negative space is informative too: if B-163's seed is unlike every other one, B-163 may have been generated at a different time by a different process — B-163/K-163 are the WTLS/ANSI "sect163" curves and may predate the April 1998 session.

Deliverable for (ii) and (iii): a table of what was tried, in the same style as cm-hypothesis.md Part A, so the next person does not repeat it.

## 3. The displaced hypothesis

The Solinas lore does not explain the fourteen recovered curve seeds. Base points are one remaining place to test it; B-163's unrecovered seed is another. Do not infer that no one previously tested these hypotheses without a literature and archival search.

Concrete form: **G, or a small multiple of G, has an x-coordinate (or y) derived from a 1997-era hash of a human-readable string.**

What the data already say (this session, `mult.out`):

- For all ten published prime-field generators, the half-point G/2 (= (2⁻¹ mod n)·G) has a full-size x-coordinate.
- Over k = 2 … 2¹⁶ in both directions (k·G and G/k, 2¹⁷ points per curve, negations covered since ±P share x and y is reported as min(y, p−y)), no point has a coordinate shorter than the field size minus ~20 bits — exactly the minimum expected from 2¹⁷ random values. No 128- or 160-bit coordinate anywhere.
- So "hash output is x, then double/small-multiply" with a *bare* hash as x is excluded at this radius. Surviving forms: the hash is padded/expanded to field size (as the X9.62 seed-to-c procedure does), or the hash chooses x in some other way (e.g., hash gives a FreeLIP-style seed integer, or a counter is hashed), or the multiplier is outside the radius.

## 4. Plan for the new session

**Step 0 — fix the target set.** Four points: P-224, P-256, P-384, P-521 generators. Optionally also run every test on the six FreeLIP-explained points as a control: anything that "finds" a derivation for those is a false positive.

**Step 1 — precompute a lookup table per curve** (cheap, do once): x-coordinates of k·G and G/k for k up to some radius R (R = 2¹⁶ is minutes; 2²⁰ is an hour per curve in PARI, far less in C). Store as a hash set of x values. Also store the *low* and *high* 128/160-bit windows of each x, so a hash can be matched against a truncated or padded coordinate, and store min(y, p−y) likewise.

**Step 2 — candidate strings.** Solinas-flavoured sentences and their variants ("Jerry Solinas should make a million dollars a year" and the versions Solinas himself gave in 2015 — "Give Bob and Jerry a raise", "Bob and Jerry rule" — plus raises, salaries, Bob Reiter, Jerry Solinas, "rule", years, "NSA", curve names "P-256"/"P256"/"nistp256", dates in several formats, the srand48 timestamps themselves as decimal/hex/ctime strings, "Give Bob and Jerry a raise", "Bob and Jerry rule", punctuation and case variants, with and without trailing newline/NUL). Build it with an LLM; this is the part a model is good at. Keep the list in a file with provenance.

**Step 3 — hash and map.** For each string, each of MD5, SHA-1, SHA-0 (and RIPEMD-160, SHA-1 of SHA-1, counter-appended variants), produce candidate x values in each mapping:
  - bare digest as x (big- and little-endian);
  - digest expanded to field size by the X9.62 Appendix A seed-to-integer procedure (SHA-1 chain with counter) — this is the most "1997-NSA" mapping;
  - digest repeated/zero-padded to field size;
  - digest as a FreeLIP `zrstarts` seed, then the published FreeLIP recipe;
  - digest as an `srand48` seed, then lrand48 bytes as x.
  For each candidate x: test x on curve; if on curve, compute the point and look up both its x and the x of its small multiples in the Step 1 table. Also test "x = candidate, take first on-curve x ≥ candidate" (the FreeLIP/X9.62 style of incrementing).

**Step 4 — the "which coordinate" question** (undecided in the voice conversation): is the hash the x-coordinate, the y-coordinate, or a scalar that multiplies some canonical point (e.g. the point at the smallest x, which is x = 0 for P-256 and x = 3 for P-224)? The scalar form is cheap: hash → k, check k·P₀ = ±G for P₀ the smallest-x point. Include it.

**Step 5 — older standards.** X9.62-1998, SEC 1/SEC 2 v1 (2000), IEEE P1363 drafts, early FIPS 186-2 drafts, and the 1997–98 ANSI X9F1 working drafts may carry different or additional base points for the same curves, or the same points with provenance text. Check whether any draft ever printed a different G for P-224/256/384/521; a change in G between drafts would date the generation and might expose the method.

**Step 6 — controls and stopping rule.** Run everything on the six explained generators; expect zero hits. Count the total number of (string, hash, mapping, multiplier) trials and compute the expected number of chance hits (≈ trials × on-curve probability × |table| / p); stop when the search is clearly in the regime where a hit would be meaningful.

## 5. Files and tools

In `/home/claude/cm` (this sandbox; copy out before it expires):
- `cm-hypothesis.md` — the full skipped-seed investigation (negative result).
- `gen.py` — regenerates lrand48 candidates and both roots of b per X9.62 for any run.
- `*.cands`, `*.orders2` — every candidate's b and every verified order for P-256, P-224, prime192, prime239.
- `battery.py`, `analyze*.py`, `isog.gp`, `pts.gp` — the test battery.
- `binpts.gp`, `binpts.out`, `bincurves.json` — GF(2^m) scan of all ten binary generators; K-163 hit; verified parameters.
- `pts.out` — small-x points with y (root convention as in §1) for all 19 viable curves; no small-scalar relations among them or with G.
- `mult.out` — half-points and shortest coordinates among k·G, G/k, k ≤ 2¹⁶, all ten published generators.
- PARI/GP 2.10-dev built from a GitHub mirror at `/home/claude/src/pari` (no seadata; SEA early-abort mode has a trace-sign bug in this build — use full `ellcard` and verify with n·P = O).

Sources: Anthropic post https://www.anthropic.com/research/ecdsa-curve-origins ; Filippo Valsorda https://words.filippo.io/seeds-solved/ ; Koblitz & Menezes, ePrint 2015/1018; Bernstein, Lange et al., "How to manipulate curve standards" (2014/2015) for the sentence-lore background.
