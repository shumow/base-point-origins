# Hand-off: everything known about the base-point problem, for a fresh agent

*Written 2026-10-20 at the end of the session that spun this repository out of [ECDSA-Origins-Revealed-Followup](https://github.com/shumow/ECDSA-Origins-Revealed-Followup). Read this first; then `notes/plan.md` (the search plan) and `notes/record.md` (the computational record). Everything below has been verified by direct computation in this session unless marked otherwise.*

## 0. The one-paragraph version

The seeds of the NIST/ANSI curves are solved (Anthropic, 16 Oct 2026: `lrand48()` seeded from the clock). The **base points** are not: of the twenty NIST/ANSI curves, only six generators are explained (P-192 and the five ANSI X9.62 example curves, from FreeLIP's `zrandom`); P-224/256/384/521, the five B curves and the five K curves are open, and so is every SEC 2 curve beyond those. What *is* visible in the unexplained generators is structure of a specific, non-malicious-looking kind: one constant reused across four Certicom Koblitz curves, a prefix shared between two secp160 curves, a short coordinate under K-163. The working thesis is "choose an x (probably a hash digest, possibly a reused test constant), solve for y, double" — Easter-egg-grade silly business, not a weakness — and the job is to find the recipe.

## 1. Framing (Dan's, verbatim in spirit)

This is a historical note. There is no attack here and it is hard to even sketch one that uses a shared *public* x-coordinate. The point is that the standard parameters carry fingerprints of ad hoc generation by a few people with ad hoc tools, and recovering the recipe replaces lore with fact, the way `lrand48` did for the seeds. Keep every write-up in that register: curious, concrete, no insinuation.

## 2. The facts

### 2.1 Subgroup half-generators x(G/2) = x(((n+1)/2)·G)

```
curve       x(G/2)                                                  bits / field
secp160k1   48ce563f89a0ed9414f5aa28ad0d96d6795f9c62                159 / 160
secp192k1   554123b78ce563f89a0ed9414f5aa28ad0d96d6795f9c66         187 / 192
secp224k1   3b78ce563f89a0ed9414f5aa28ad0d96d6795f9c63              166 / 224
secp256k1   3b78ce563f89a0ed9414f5aa28ad0d96d6795f9c63              166 / 256
K-163       23e21d6019e1211f6bd47ec180256e97                        126 / 163  (y is 161 bits)
```

What exactly is shared among the four secp\*k1 values — be precise, it constrains everything:
- bits 4–151 (148 bits): `ce563f89a0ed9414f5aa28ad0d96d6795f9c6` on all four;
- bits 152–159 (the top byte of the 160-bit block): `48` on secp160k1, `78` on the others — so "the low 160 bits are fixed" is **false**;
- above bit 160: `3b` on 224k1/256k1, `554123b` on 192k1, nothing on 160k1. The 192-bit curve has *more* prefix than the 224/256-bit ones, so this is not a long constant truncated to field size;
- last nibble: 2, 6, 3, 3;
- every value is far below its field prime, so no modular reduction is in play in the published values.

secp224k1 and secp256k1 are *identical* at G/2 — same 166-bit x on two different curves over two different fields (both with a = 0; b = 5 and b = 7). That alone proves the generators were constructed from a chosen x and doubled, with the x reused.

### 2.2 The secp160r pair
```
secp160r1   x(G)   = 4a96b5688ef573284664698968c38bb913cbfc82
secp160r2   x(G/2) = 4a96b5688ef573284664698e81e1510fae4e8422
```
First 92 bits shared (`4a96b5688ef573284664698`), remaining 68 differ wholesale — not an increment. Unexplained.

### 2.3 Everything else scanned looks random
- All ten NIST/ANSI prime-field generators (P-192/224/256/384/521, prime192v2/v3, prime239v1/v2/v3): k·G and G/k for k ≤ 2¹⁶, both y signs; shortest coordinates within two bits of the uniform-minimum expectation. (`results/mult.out`)
- Nine of ten NIST binary curves (all but K-163): k·G, k ≤ 2¹⁶; G/k, k ≤ 2¹²; plus all 28 rational cofactor preimages across the ten curves. (`results/binpts.out`)
- Six of ten SEC 2 prime curves (secp112r1/r2, 128r1/r2, 160r1, 160r2 apart from §2.2), including the cofactor preimages on the two h = 4 curves. (`results/secg-halfpoints.txt`)
- No shared hex substring of ≥ 32 bits between any two half-generators across the whole set except the ones above; the K-163 value shares nothing with the secp constant.

### 2.4 K-163 specifics
- sect163k1 / ansit163k1 / NIST K-163: y² + xy = x³ + x² + 1 over GF(2¹⁶³) with reduction polynomial x¹⁶³ + x⁷ + x⁶ + x³ + 1, h = 2, no seed. The generator is the curve's only chosen parameter.
- x(G/2) is 126 bits under a uniform heuristic: probability 2⁻³⁷ for a specified point; ~5 × 10⁻⁶ expected hits across the 696,300 binary points scanned; not a calibrated discovery probability because of exploratory choices.
- The other rational half, G/2 + (0,1), has a 162-bit x (`389ff55b1717d231e466c6a90bef265d7ad1ca9a4`). The 2-torsion point on K-163 is (0, 1).
- The value was initially published wrong (coefficient-bit-reversed, `3a5da90060df8af5be2121e601ae11f1`); corrected 19 Oct. The 32-bit words of the correct value have top bits 0,0,0,1, so it is not four consecutive 31-bit `lrand48` outputs in that reading.
- As a 128-bit object it is the natural MD5-sized sibling of the 160-bit secp constant; its top two bits being zero is either chance (¼) or a mask.

### 2.5 What Anthropic's post does and does not say (checked 20 Oct)
- Explained seeds: all ten NIST/ANSI prime-curve seeds; B-233/283/409/571 (five 31-bit `lrand48` words, one sitting on 17 Apr 1998, clock apparently halved). B-163's seed fits nothing they tried.
- Explained base points: P-192, prime192v2/v3, prime239v1/v2/v3 — FreeLIP `zrandom` (state × 3¹²¹ mod 2¹⁰⁷ − 1), small integer seeds 20000, 20512, 20517, 20420, 20507, 20509, seven outputs discarded, 26-bit limbs assembled into x, first on-curve x taken, May 1997.
- Unexplained base points: P-224, P-256, P-384, P-521, "the NIST binary curves". The K curves are not mentioned at all.
- Valsorda's write-up mentions neither base points nor K-163.

### 2.6 Prior art
- Heninger, Scholl, Shumow, Crypto 2019 rump session, 21:00, title `48ce563f89a0ed9414f5aa28ad0d96d6795f9c62` (= x(G/2) on secp160k1). Video: https://www.youtube.com/watch?v=NGLR2N4EK58. No slides on the IACR page. Dan was a co-author, so the secp\*k1 observation is his and Nadia's prior work; this repo reproduces it across all four curves and extends the scan.
- The SEC 2 v1.0 r-curve SEEDs embed ASCII: secp112r1 `…8E4D696E676875615175…` = "Minghua Qu"; likewise secp112r2, secp128r1/r2, secp160r1 (`…4D696E6768756151 7533…`). The same people were demonstrably putting names into constants. Treat this as a hint about *which strings* to hash.

## 3. What has been tried and failed

### 3.1 K-163 hash dictionary (29,577,717 evaluations, 0 hits)
`scripts/k163/search.py` against the corrected 126-bit target. Strings (`scripts/k163/strings.py`): Solinas-lore phrases ("Give Bob and Jerry a raise", "Jerry Solinas should make a million dollars a year", …), people (Solinas, Reiter, Koblitz, Miller, Menezes, Vanstone, Schroeppel, Johnson, Brown), orgs (NSA, NIST, ANSI, X9.62, IEEE P1363, SECG, Certicom, WAP, WTLS), curve names in many spellings, generic words, small integers, the B-163 seed and K-163 G coordinates as hex strings, every date 1997-01-01…1998-12-31 in 13 formats, the run timestamps as decimal/halved/doubled/hex/ctime; each in case variants, with trailing `.`, `!`, space, newline, CRLF, NUL, leading space; encoded ASCII, UTF-16-LE, UTF-16-BE. Hashes: MD5, MD4, SHA-0, SHA-1, RIPEMD-128, RIPEMD-160, SHA-1∘SHA-1 (`hashes.py` has pure-Python MD4/SHA-0/RIPEMD-128). Suffixes: none, and counter 0–3 as a byte / decimal char / 4-byte BE. Readings: as-is, byte-reversed, 32-bit-word-swapped, low/high 128 of a 160-bit digest, top-two-bits-masked, first-15-bytes. Result: `results/k163-search-rerun.txt`.

### 3.2 Core-matched dictionary for the secp constant (16,432,065 evaluations, 0 hits)
`scripts/secg_core_search.py`: same string set; SHA-1, SHA-0, RIPEMD-160, SHA-1∘SHA-1, SHA-1∘MD5; same suffixes; readings as-is / reversed / word-swapped; **matcher compares bits 4–151 only** against the core, so the varying top byte and last nibble cannot hide a hit; also checks the full 160-bit values with top byte 48 or 78. Result: `results/secg-core-search.txt`. Caveat: this string set was built for the NSA/NIST story. It does not contain Certicom-specific material (see §4.1).

### 3.3 Last-nibble acceptance rule (negative)
For base …9c60 + i, i = 0…15, on each secp\*k1 curve, which i give a point, and the parity / half-plane of y(P) (`notes/plan.md` step 2 has the table). The used P has even y above p/2 on all four — but "first x on the curve" picks 0, 0, 2, 1, and "first x whose even root is above p/2" picks 0 on secp192k1. So neither parity nor y < p/2 nor plain on-curve explains 2, 6, 3, 3. Open.

## 4. What to do next (priority order)

### 4.1 Certicom-era dictionary pass — the obvious next experiment
Extend `scripts/k163/strings.py` (or write `strings_certicom.py`) and rerun `secg_core_search.py` (and the K-163 search). Add: Certicom, Certicom Corp, Certicom Research, SECG, SEC 1, SEC 2, "Standards for Efficient Cryptography", Mississauga, Waterloo, Hayward; people: Scott Vanstone, Alfred Menezes, Minghua Qu, Dan Brown, Daniel R. L. Brown, Rob Gallant, Robert Gallant, Rob Lambert, Robert Lambert, Simon Blake-Wilson, Don Johnson, Ron Mullin, Ian Blake, Neal Koblitz; curve names: secp160k1 … secp256k1, sec160k1, ansip256k1, "Koblitz 256", "k256", "koblitz", "anomalous", "CM curve", "j=0"; the SEC 1/2 draft dates (1999–2000, and 1998 for the Certicom ECC Challenge); the ECC Challenge names (ECCp-131, ECC2K-163, …) — Certicom's challenge curves of 1997 are a plausible source of a reused constant; the r-curve SEEDs and their ASCII; and the obvious test strings ("test", "abc", "hello", "The quick brown fox…", "Certicom test vector"). Also try hashing the *other* curves' parameters: p, n, a, b of each secp\*k1 curve as decimal/hex strings — a program that seeded the generator search from the curve's own parameters would produce a value shared only if the input was shared, so this tests the hypothesis more than it finds the answer.

### 4.2 Explain the top byte and the 192k1 prefix
Test whether `48`/`78` and `3b`/`554123b` are (a) a counter, (b) top bytes of a second digest of the same string with a counter (X9.62 seed-expansion style: SHA-1(s‖i) chained), (c) the X9.62 expansion of a 160-bit input to field length — compute the expansion for each field and compare high bits, (d) an artefact of a 32-bit-word layout (the 166-bit value is 5×32 + 6 bits; the 187-bit one 5×32 + 27). Any hypothesis must produce `48` on the 160-bit curve and `78` on the others from the same source.

### 4.3 The secp160r pair
Find what fixes the top 92 bits of §2.2 and varies the bottom 68. Compute x(G/2) and small multiples for the SEC 2 *binary* curves (sect113/131/163/193/233/239/283/409/571, r and k variants) and the ANSI X9.62 binary examples (c2pnb163v1 … c2tnb431r1), and the WTLS curves, and look for shared prefixes/suffixes the way `secg_scan.py` does. The binary scan code is `scripts/binpts.py` (pure Python, slow but fine) and `binpts.gp` (PARI, needs `gp`).

### 4.4 K-163 as the MD5 sibling
Rerun the K-163 search with the 4.1 strings. Also test: the 126-bit value as the low/high 126 of a SHA-1 digest; MD5 with the top two bits masked; the value as *x of the point before cofactor clearing on another convention* (G = 2P vs P = G/2 are the same here, but check G + T for T the 2-torsion point as the starting point — done: 162 bits).

### 4.5 Archival
SEC 1 / SEC 2 drafts 1999–2000; Certicom ECC Challenge documents (1997); IEEE P1363 working-group archives; WTLS (WAP) spec and drafts; ANSI X9.62/X9.63 drafts; any Certicom test-vector or "ECC parameters" documents; the SECG mailing list archive. A draft with a *different* generator dates the constant; a draft with a *stated derivation* ends the search. Nobody has done this pass.

### 4.6 The NIST prime curves P-224/256/384/521
Nothing hash-sized at subgroup multiples ≤ 2¹⁶. Next: X9.62-style expansions of candidate strings compared against x(G), x(G/2), x(2G) …; `lrand48` and FreeLIP `zrandom` streams (both clock conventions Anthropic found) windowed against those coordinates; the P-192 FreeLIP recipe run with *every* small seed 1…100000 on each of the four curves (cheap, decisive if it hits).

## 5. Repository map

```
README.md                  framing + status
HANDOFF.md                 this file
notes/plan.md              hypotheses H1–H4 and the six-step plan, with steps 1–2 marked done
notes/record.md            full computational record (Part C of the original notes: §7, 7.1, 7.2)
notes/base-point-brief.md  older hand-off brief (superseded where it disagrees with plan.md)
scripts/secg_scan.py       SEC 2 prime-curve scan (pure Python, ~2 min for all ten)
scripts/secg_core_search.py core-matched dictionary search (reuses k163/strings.py and k163/hashes.py)
scripts/binpts.py, .gp     NIST binary-curve scan (Python / PARI)
scripts/k163/              hash dictionary harness: search.py, strings.py, hashes.py (MD4, SHA-0, RIPEMD-128)
data/bincurves.json        verified NIST binary-curve parameters
results/                   secg-halfpoints.{txt,json}, secg-core-search.txt, binpts.out, mult.out, k163-search-rerun.txt
```

## 6. Practical notes for the agent
- SEC 2 v2.0 (secg.org/sec2-v2.pdf) dropped the ≤160-bit curves; their parameters are in SEC 2 v1.0 (secg.org/SEC2-Ver-1.0.pdf). Both were fetched 20 Oct and the parameters in `secg_scan.py` were verified by n·G = O.
- Pure-Python EC arithmetic is fine for 2¹⁶ multiples on prime curves (seconds) and tolerable on binary curves (minutes to hours at 571 bits). PARI/GP is much faster but was not available in the sandbox used so far; if `gp` is on PATH, `binpts.gp` is the better tool.
- The dictionary searches run at ~40–50k hash evaluations/s in pure Python; 30 M evaluations ≈ 15 min. Keep the matcher core-based for the secp constant.
- The original seeds/skips investigation, including the full ~50-invariant battery and the statistical caveats, lives in the follow-up repository and is *not* this repo's concern.
- Dan's standing style preference for write-ups: say what was found and what you'd bet on; qualify once, not three times.
