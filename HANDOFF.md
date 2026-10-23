# Hand-off: everything known about the base-point problem, for a fresh agent

*Written 2026-10-20 at the end of the session that spun this repository out of [ECDSA-Origins-Revealed-Followup](https://github.com/shumow/ECDSA-Origins-Revealed-Followup). Read this first; then `notes/plan.md` (the search plan) and `notes/record.md` (the computational record). Everything below has been verified by direct computation in this session unless marked otherwise; the 2019–20 history in §2.6 and §3.0 is reported from mailbox surveys, with its evidence levels set out in `references/crypto2019-rump/README.md`.*

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
- bits 4–155 (152 bits): `8ce563f89a0ed9414f5aa28ad0d96d6795f9c6` on all four (*corrected 22 Oct: earlier text said 148 bits, bits 4–151, and a varying top byte; the byte is `48` vs `78`, so its low nibble is shared too — see `references/crypto2019-rump/README.md`*);
- bits 156–159 (the top nibble of the 160-bit block): `4` on secp160k1, `7` on the others — so "the low 160 bits are fixed" is **false**, but only one nibble at the top varies, as the 2019 slides said;
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
- Two more negatives on the sect\*k1 curves from Dan's June 2020 code, replicated 23 Oct (`scripts/sectk_2020_checks.py`, `results/sectk-2020-checks.txt`): over the m²·h points σᵏ(2⁻ʲ·G) + T (Frobenius powers × inverse powers of two × E[h]) the shortest x on sect233/239/283/409/571k1 is 215/219/266/390/549 bits, within two bits of uniform for that many samples; and G = P + σ(P) with P short is false on all six curves (x of (1 ± σ)⁻¹G + T full-size).

### 2.5 What Anthropic's post does and does not say (checked 20 Oct)
- Explained seeds: all ten NIST/ANSI prime-curve seeds; B-233/283/409/571 (five 31-bit `lrand48` words, one sitting on 17 Apr 1998, clock apparently halved). B-163's seed fits nothing they tried.
- Explained base points: P-192, prime192v2/v3, prime239v1/v2/v3 — FreeLIP `zrandom` (state × 3¹²¹ mod 2¹⁰⁷ − 1), small integer seeds 20000, 20512, 20517, 20420, 20507, 20509, seven outputs discarded, 26-bit limbs assembled into x, first on-curve x taken, May 1997.
- Unexplained base points: P-224, P-256, P-384, P-521, "the NIST binary curves". The K curves are not mentioned at all.
- Valsorda's write-up mentions neither base points nor K-163.

### 2.6 Prior art
- Heninger, Scholl, Shumow, Crypto 2019 rump session, 21:00, title `48ce563f89a0ed9414f5aa28ad0d96d6795f9c62` (= x(G/2) on secp160k1). Video: https://www.youtube.com/watch?v=NGLR2N4EK58. No slides on the IACR page. Dan was a co-author, so the secp\*k1 observation is his and Nadia's prior work; this repo reproduces it across all four curves and extends the scan.
- **The 2019–20 record, recovered 22 Oct 2026 from Dan's mailboxes:** `references/crypto2019-rump/` (README there is the synthesis, with an "Evidence levels" section saying what was checked in the slides, what is reported from mail, and what the scripts prove). Per the surveys: Travis Scholl saw the short halves first (24 Mar 2019); Nadia had the 256k1 case because, as the slides report, 99% of repeated Bitcoin nonces in that investigation were (n−1)/2; the 160-bit curve was found at Crypto on 18 Aug 2019; Nadia ran John the Ripper over the 256 top/bottom-nibble variants (nothing, coverage unknown, §3.0); Dan Brown and Antonio Sanso supplied the CM history and the counter theory; Travis derived the secp256k1 prime by CM (27 Oct 2019); Dan extended to the sect\*k1 curves in June 2020 (only sect163k1 is short — matches §2.4). Dan's 2020 Sage code was recovered from the private `factorable/secp256k1` repo on 23 Oct (`references/crypto2019-rump/factorable-secp256k1/`, replicated by `scripts/sectk_2020_checks.py`; §2.4); the 2019 discussion on Nadia's Slack is still unrecovered. Dan checked the readable slide deck locally on 22 Oct 2026 (page references in the folder README); it is not redistributed. `scripts/verify_crypto2019.py` (Python, probable-prime tests) and `halve_generators.sage` (Sage, proof-enabled primality) re-check every number from that record.
- The SEC 2 v1.0 r-curve SEEDs embed ASCII: secp112r1 `…8E4D696E676875615175…` = "Minghua Qu"; likewise secp112r2, secp128r1/r2, secp160r1 (`…4D696E6768756151 7533…`). The same people were demonstrably putting names into constants. Treat this as a hint about *which strings* to hash.

## 3. What has been tried and failed

### 3.0 2019: reported John the Ripper negative; candidate coverage unknown
The mailbox survey reports that Nadia Heninger ran `--format=Raw-SHA1` on 19–20 Aug 2019 against all 16 × 16 top/bottom-nibble variants of the secp160k1 value, with no match. Those are target variants, not a definition of the candidate strings searched. Wordlists, rules, encodings, counts and completion status are not established here; infer neither defaults nor exhaustion of any named corpus. Keep this as historical context, not measured coverage in the new public hunt. Dan Brown's reported hashes.org attempt likewise has undocumented coverage. Source: `references/crypto2019-rump/microsoft-mailbox-survey.md`, timeline rows for Aug 19–20 2019.

### 3.1 K-163 hash dictionary (29,577,717 evaluations, 0 hits)
`scripts/k163/search.py` against the corrected 126-bit target. Strings (`scripts/k163/strings.py`): Solinas-lore phrases ("Give Bob and Jerry a raise", "Jerry Solinas should make a million dollars a year", …), people (Solinas, Reiter, Koblitz, Miller, Menezes, Vanstone, Schroeppel, Johnson, Brown), orgs (NSA, NIST, ANSI, X9.62, IEEE P1363, SECG, Certicom, WAP, WTLS), curve names in many spellings, generic words, small integers, the B-163 seed and K-163 G coordinates as hex strings, every date 1997-01-01…1998-12-31 in 13 formats, the run timestamps as decimal/halved/doubled/hex/ctime; each in case variants, with trailing `.`, `!`, space, newline, CRLF, NUL, leading space; encoded ASCII, UTF-16-LE, UTF-16-BE. Hashes: MD5, MD4, SHA-0, SHA-1, RIPEMD-128, RIPEMD-160, SHA-1∘SHA-1 (`hashes.py` has pure-Python MD4/SHA-0/RIPEMD-128). Suffixes: none, and counter 0–3 as a byte / decimal char / 4-byte BE. Readings: as-is, byte-reversed, 32-bit-word-swapped, low/high 128 of a 160-bit digest, top-two-bits-masked, first-15-bytes. Result: `results/k163-search-rerun.txt`.

### 3.2 Core-matched dictionary for the secp constant (16,432,065 evaluations, 0 hits)
*Re-certified 20 Oct* with the repaired script (strict hash initialization, coverage manifest): same 16,432,065 evaluations, 0 hits, all five algorithms confirmed present; manifest in `results/secg-core-search.json` (algorithms, suffixes, readings, input-sequence hash, source hashes, Python/OpenSSL versions).
`scripts/secg_core_search.py`: same string set; SHA-1, SHA-0, RIPEMD-160, SHA-1∘SHA-1, SHA-1∘MD5; same suffixes; readings as-is / reversed / word-swapped; **matcher compares bits 4–151 only** against the core, so the varying top byte and last nibble cannot hide a hit; also checks the full 160-bit values with top byte 48 or 78. Result: `results/secg-core-search.txt`. Caveat: this string set was built for the NSA/NIST story. It does not contain Certicom-specific material (see §4.1).

### 3.3 Certicom-era dictionary pass (§4.1, done 20 Oct, second session; 0 hits)
`scripts/k163/strings_certicom.py` (271,395 byte strings: Certicom/SECG/SEC/WTLS/P1363 names and places, the Certicom people, every spelling of the six secp curves and the Koblitz/CM/j=0 vocabulary, the 1997 ECC Challenge names, the r-curve SEEDs and "Minghua Qu", hash test strings, 1999–2000 dates, and every curve parameter as decimal/hex/raw bytes). Both harnesses take `STRINGS=strings_certicom`. secp core: 17,640,675 evaluations, 0 hits (`results/secg-core-search-certicom.txt`). K-163: 31,753,215 evaluations, 0 hits (`results/k163-search-certicom.txt`). Both dictionaries (NIST-centred and Certicom-centred) are now exhausted under every 1990s hash; a bare hash of a short human string is unlikely for either constant.

### 3.4 Last-nibble acceptance rule (negative, now brute-forced)
For base …9c60 + i, i = 0…15, on each secp\*k1 curve, which i give a point, and the parity / half-plane of y(P) (`notes/plan.md` step 2 has the table). The used P has even y above p/2 on all four — but "first x on the curve" picks 0, 0, 2, 1, and "first x whose even root is above p/2" picks 0 on secp192k1. So neither parity nor y < p/2 nor plain on-curve explains 2, 6, 3, 3. `scripts/nibble_rules.py` then tried ~11,500 rules (every start nibble in −16…15, both directions, 1st/2nd/3rd hit, ~60 point properties and all pairs): 13 fit, which is the chance rate. Most code-like survivor: "second on-curve x at or after …9c61". Treat as open; record §7.3.3.

## 4. What to do next (priority order)

### 4.1 Certicom-era dictionary pass — run twice on 20 Oct by two independent sessions, no hit either time
*Result A:* `wordlists/certicom.txt` (6,939 base strings) through `scripts/wordlist_search.py` — every variant, three encodings, 13 suffixes, SHA-1/SHA-0/RIPEMD-160/SHA-1∘SHA-1/SHA-1∘MD5 against the core and MD5/MD4/RIPEMD-128 against K-163: **no hit** (`results/certicom-wordlist-search.txt`, 19.4 M evaluations).
*Result B:* `scripts/k163/strings_certicom.py` (271,395 byte strings incl. the curve parameters as decimal/hex/raw bytes) through the original harnesses with `STRINGS=strings_certicom`: core 17.6 M evaluations, K-163 31.8 M, **no hit** (§3.3; `results/*-certicom.txt`). The list below is what went in; widen it (full English wordlists, name lists, hashcat rules) on a GPU per `notes/hash-angle.md` V1.
Extend `scripts/k163/strings.py` (or write `strings_certicom.py`) and rerun `secg_core_search.py` (and the K-163 search). Add: Certicom, Certicom Corp, Certicom Research, SECG, SEC 1, SEC 2, "Standards for Efficient Cryptography", Mississauga, Waterloo, Hayward; people: Scott Vanstone, Alfred Menezes, Minghua Qu, Dan Brown, Daniel R. L. Brown, Rob Gallant, Robert Gallant, Rob Lambert, Robert Lambert, Simon Blake-Wilson, Don Johnson, Ron Mullin, Ian Blake, Neal Koblitz; curve names: secp160k1 … secp256k1, sec160k1, ansip256k1, "Koblitz 256", "k256", "koblitz", "anomalous", "CM curve", "j=0"; the SEC 1/2 draft dates (1999–2000, and 1998 for the Certicom ECC Challenge); the ECC Challenge names (ECCp-131, ECC2K-163, …) — Certicom's challenge curves of 1997 are a plausible source of a reused constant; the r-curve SEEDs and their ASCII; and the obvious test strings ("test", "abc", "hello", "The quick brown fox…", "Certicom test vector"). Also try hashing the *other* curves' parameters: p, n, a, b of each secp\*k1 curve as decimal/hex strings — a program that seeded the generator search from the curve's own parameters would produce a value shared only if the input was shared, so this tests the hypothesis more than it finds the answer.

### 4.2 Explain the top byte and the 192k1 prefix — hypotheses tested 23 Oct, record §7.3.7
`scripts/high_bytes_analysis.py` (controls `tests/test_high_bytes.py`) ran the four listed hypotheses and more. Structure, confirmed invertibly: one 160-bit block `V = 78ce563f…9c6?` (middle 152 bits fixed, top/bottom nibbles soft) underlies all four; secp224k1 and secp256k1 are byte-identical at x(G/2); the high material is 0x3b on 192/224/256 (0x55412 extra on 192k1) and absent on 160k1, which has 0x30 cleared from V's top byte. **Excluded:** (c) FIPS/X9.62 expansion — it matches the shared low-160 bits but a single seed can't give both `0554123b` and `0000003b` as rightmost-32 of SHA-1(SEED), and the high field would be full-weight, not a 6-bit `3b`; truncation-to-field-size — 192k1 has *more* prefix than 224/256 over a *smaller* field; (a)/(d) a per-curve counter or uninitialised limb — 224=256 and 192 shares the 0x3b, so it is assigned, not leftover; a parameter function — 0x3b/0x55412/0x554123b match no Mersenne offset, low word of p/n, trace, or b, and V isn't a hash of p or n. The 0x30 top-byte clear on 160k1 is not field-forced (value < p, same bit length, both top bytes lift). **Bet:** the high bytes are small hand-assigned tags in the top 32-bit limb of a fixed-width buffer holding V. Hypothesis (b), a counter folded into the hash *input*, is modelled in record §7.3.8 (`scripts/counter_before_hash.py`): **excluded as the source of the top byte** — the shared 152-bit core forces one hashed input, which cannot also give a different top nibble, so the split is a post-hash edit; a 21.3M-evaluation input-counter probe over the Certicom list adds 0 core hits. Its one open branch, a counter before a *second* hash/transform of the digest (V = H1(seed) counter-free in the low bits, `high = g(H2(V,counter))`), is modelled in record §7.3.9 (`scripts/counter_second_hash.py`): 25.5M window checks find no transform, no re-hash window, and no small-counter second hash of V reproducing the 32-bit high limbs 0x0000003b / 0x0554123b, and no single recipe giving both — so it too is unsupported in the digest-input, small-counter regime. The last form, stage 2 hashing the *seed*, is modelled in record §7.3.10 (`scripts/seed_two_stage.py`) over candidate seeds (Certicom wordlist + curve params, 13,910 seed-encodings): a seed must clear BOTH stages, and stage 1 (→V), stage 2 (→32-bit high limb), a unified single-wide-hash-window model, and the joint test are all 0 hits (688M checks). So the counter-before-hash family is now closed over every testable seed/digest input; only a seed *outside* this corpus (a long or machine input) remains, which stage 1 already argues against for short human strings. Still open: what 0x3b (=59=';'), 0x55412 and the 0x30 clear *mean*.

### 4.3 The secp160r pair
Find what fixes the top 92 bits of §2.2 and varies the bottom 68. Compute x(G/2) and small multiples for the SEC 2 *binary* curves (sect113/131/163/193/233/239/283/409/571, r and k variants) and the ANSI X9.62 binary examples (c2pnb163v1 … c2tnb431r1), and the WTLS curves, and look for shared prefixes/suffixes the way `secg_scan.py` does. The binary scan code is `scripts/binpts.py` (pure Python, slow but fine) and `binpts.gp` (PARI, needs `gp`).

### 4.4 K-163 as the MD5 sibling
Rerun the K-163 search with the 4.1 strings. Also test: the 126-bit value as the low/high 126 of a SHA-1 digest; MD5 with the top two bits masked; the value as *x of the point before cofactor clearing on another convention* (G = 2P vs P = G/2 are the same here, but check G + T for T the 2-torsion point as the starting point — done: 162 bits).

### 4.5 Archival — pass STARTED 23 Oct 2026, catalog in `notes/archival.md`
SEC 1 / SEC 2 drafts 1999–2000; Certicom ECC Challenge documents (1997); IEEE P1363 working-group archives; WTLS (WAP) spec and drafts; ANSI X9.62/X9.63 drafts; any Certicom test-vector or "ECC parameters" documents; the SECG mailing list archive. A draft with a *different* generator dates the constant; a draft with a *stated derivation* ends the search. **Started:** `notes/archival.md` holds the decision rule, the standards timeline, the prioritized target catalog with URLs/reachability, and the search-level findings — chiefly that no public standard states a base-point derivation for the Koblitz curves (SEC 2 v1.0 gives only the curve-selection method; SEC 1 defers generation to X9.62:1998), and that **GEC 2: Test Vectors for SEC 1 (Certicom, reported v0.3, Sept 1999)** predates SEC 2 v1.0 by a year and is the top pre-SEC-2 target. The retrieval step is blocked in this sandbox: WebFetch reaches only GitHub and package registries (secg.org, web.archive.org, safecurves, rfc.nop.hu, ieee.org all fail DNS), so the PDFs are a hand-drop or networked-session job per the fetch list in `notes/archival.md` — drop them under `references/archival/`. v1.0 (2000-09-20) and v2.0 (2010) params are already verified in-repo (§6), so the open question is strictly pre-2000-09-20.
Closer to home (22 Oct): the mailbox surveys point to the private `factorable/secp256k1` repository and Nadia's Slack for original code. The readable rump slides have now been reviewed locally but not redistributed. Remaining attachment leads include `compute-all-the-keys.png` (Aug 2019) and an unidentified `paper.pdf` forwarded June 2022; its subject matter is unknown. Private mail links are redacted; dates, subjects and filenames remain in `references/crypto2019-rump/`. Confirm permission before publishing further correspondence or attachments.

### 4.5b Re-run the full 2020 sect\*k1 grid — DONE 23 Oct 2026, every curve matches
`python3 scripts/sectk_2020_checks.py --full` was run (exit 0, ~22 min on this 4-core sandbox; `tests.test_sectk2020` passed first). The recorded 2020 minimum is the **global** minimum of the m²·h grid on all six sect\*k1 curves, each at the recorded (k, j): 126/215/219/266/390/549 bits on sect163/233/239/283/409/571k1. So the 2020 search missed no shorter coordinate and K-163 stays the only short one. Full output in `results/sectk-2020-full-grid.txt`; record §7.3.6 updated. Nothing left to run here.

### 4.6 The NIST prime curves P-224/256/384/521
Nothing hash-sized at subgroup multiples ≤ 2¹⁶. FreeLIP recipe with every seed 1…100000, discards 0…12: `scripts/freelip_sweep.py`, 0 hits on all four curves and on secp160k1 (`results/freelip-sweep-{a,b}.txt`, record §7.3.4). Remaining: X9.62-style expansions of candidate strings compared against x(G), x(G/2), x(2G) …; `lrand48` and FreeLIP `zrandom` streams (both clock conventions Anthropic found) windowed against those coordinates; larger FreeLIP seeds or an `lrand48` stream in place of `zrandom`.

## 4b. The hash angle (added later on 20 Oct; §2a of the note holds the paper ingestion and Dan's framing, and `scripts/sha1_steps.py` the forward/backward implementation; V1 is the agreed first scenario)
`notes/hash-angle.md` is the plan for treating the constants as hash digests: what the Merkle–Damgård / Davies–Meyer structure gives (single-block model with ≤ 5 unknown message words, step inversion for reconstructing executions) and what it does not (no shortcut past enumerating candidates — the feed-forward is one-way; the step inversion recovers the input IHV from the final *working state*, not from the digest). Two plans: **V1** GPU dictionary/mask attacks with hashcat using a 12,288-target list that covers every completion of the 148-bit core in three readings (`scripts/make_targets.py`), seeded with `wordlists/certicom.txt`; **V2** language-model-generated candidate sentences for the Solinas-lore class of input. `references/README.md` lists the Stevens / Stevens–Shumow papers to read for the forward/backward technique and says what to check them against.

## 4c. Tests
`tests/test_recovery.py` (stdlib `unittest`, ~10 s): plants a known answer through each real search entry point — the core matcher and its main loop (as-is, byte-reversed, counter-suffixed SHA-0, top-byte/last-nibble-insensitive), the K-163 matcher (MD5, low-128-of-SHA-1, masked top bits), `wordlist_search` (a punctuation variant), `make_targets` (every completion of the core in all three readings is a target), `freelip_sweep` (reproduces P-192 from seed 20000; finds a point planted on P-256 with a non-standard discard), `nibble_rules` (finds a planted first-on-curve rule and confirms the real nibbles are not one), the EC arithmetic (recomputes all four half-generator constants from the published G), and `sha1_steps`. Run it before trusting any new negative result, and add a planted case for any new search.

## 4d. Next analytic task: MD4/MD5 meet-in-the-middle on K-163
`notes/md-mitm.md` — Dan's design (voice, 20 Oct) for a last-block MITM preimage on the 126-bit K-163 value, exploiting that MD4/MD5 have no message expansion so known-padding words stay known. Test-first: plant-and-recover control (`tests/test_md_mitm.py`) before the solver is trusted. Honest limit recorded there: the candidate-free back-tail is only a few steps for a short string; the win is the MITM constraint plus the cheap filter. Not yet built.

## 5. Repository map

```
README.md                  framing + status
HANDOFF.md                 this file
notes/plan.md              hypotheses H1–H4 and the six-step plan, with steps 1–2 marked done
notes/record.md            full computational record (§7, 7.1, 7.2; §7.3 = the 20 Oct second-session experiments)
notes/base-point-brief.md  older hand-off brief (superseded where it disagrees with plan.md)
notes/archival.md          §4.5 archival pass: decision rule, standards timeline, target catalog with URLs/reachability, and the fetch list (retrieval blocked in-sandbox)
scripts/secg_scan.py       SEC 2 prime-curve scan (pure Python, ~2 min for all ten)
scripts/secg_core_search.py core-matched dictionary search (STRINGS=strings|strings_certicom selects the set)
scripts/nibble_rules.py    brute-force of last-nibble acceptance rules
scripts/high_bytes_analysis.py  §4.2: structure of the four secp*k1 x(G/2) and the top-byte/192k1-prefix exclusions (→ results/high-bytes-analysis.txt; tests/test_high_bytes.py)
scripts/counter_before_hash.py  §4.2(b): models a counter in the hash input; excludes it as the source of the top byte (→ results/counter-before-hash.txt, results/counter-before-hash-probe.json; tests/test_counter_before_hash.py)
scripts/counter_second_hash.py  §4.2(b): models the two-stage counter-before-second-hash variant on the digest; unsupported (→ results/counter-second-hash.txt; tests/test_counter_second_hash.py)
scripts/seed_two_stage.py       §4.2(b): joint seed search — stage 1 (→V) and stage 2 (→high limb) over candidate seeds; all negative (→ results/seed-two-stage.txt; tests/test_seed_two_stage.py)
scripts/freelip_sweep.py   FreeLIP zrandom recipe x every small seed on P-224/256/384/521, secp160k1
tests/test_recovery.py     positive controls for every search (§4c)
scripts/hashcat_probe.py   decides whether hashcat confirms the leading digest word (hash-angle §5)
notes/md-mitm.md           MD4/MD5 meet-in-the-middle design for K-163 (§4d; not yet built)
scripts/sha1_steps.py      step-level SHA-1, forward + backward, self-tested (hash-angle §2a)
scripts/test_secg.py       regression tests for the SEC 2 scan and core search
scripts/make_targets.py    hashcat target lists (12,288 SHA-1 for the secp core; 4 MD5 for K-163)
wordlists/certicom.txt     Certicom-era base dictionary for the next search pass
notes/hash-angle.md        the Merkle–Damgård analysis and the V1/V2 search plans
references/README.md       Stevens / Stevens–Shumow papers to add and what to extract from them
scripts/binpts.py, .gp     NIST binary-curve scan (Python / PARI)
scripts/verify_crypto2019.py  re-checks the 2019–20 record: half-generators, 152-bit core, counter theory, P-256 control, K-163, CM derivation of secp256k1's p with probable-prime tests (→ results/verify-crypto2019.txt)
references/crypto2019-rump/halve_generators.sage  the same in Sage with proof-enabled primality (→ results/verify-crypto2019-sage.txt; tests/test_crypto2019.py runs both)
references/crypto2019-rump/  the 2019–20 investigation as recovered from mail (surveys, reconstructed Sage, synthesis README with leads); factorable-secp256k1/ holds Dan's original 2020 Sage code
scripts/sectk_2020_checks.py  replicates the 2020 sect*k1 searches: recorded grid minima recomputed, G = P + σ(P) hypothesis on all six curves (→ results/sectk-2020-checks.txt; tests/test_sectk2020.py)
scripts/k163/              hash dictionary harness: search.py, strings.py, strings_certicom.py, hashes.py (MD4, SHA-0, RIPEMD-128)
data/bincurves.json        verified NIST binary-curve parameters
results/                   secg-halfpoints.{txt,json}, secg-core-search{,-certicom}.txt, binpts.out, mult.out, k163-search-{rerun,certicom}.txt, nibble-rules.txt, freelip-sweep-{a,b}.txt, high-bytes-analysis.txt, sectk-2020-full-grid.txt, counter-before-hash.txt, counter-before-hash-probe.json, counter-second-hash.txt, seed-two-stage.txt
```

## 5b. Review ported 20 Oct
A Copilot review of the follow-up repo's copies (`review/base-points-corrections` there) was reviewed and its worthwhile parts ported here rather than merged there: `secg_scan.py` now enumerates and validates the full cofactor kernel E[h] and preimage coset or fails explicitly (no silent partial lists), records scan bounds and preimage witnesses in the JSON, and has `--output-dir`/bound flags; `secg_core_search.py` refuses to run if any configured hash is unavailable and writes a JSON manifest; `scripts/test_secg.py` (18 tests; one needs PARI) checks generator/half relations, the shared core and prefix, kernel-failure modes, cached witnesses and output paths. Run: `python -X utf8 -m unittest discover -s scripts -p test_secg.py -v`. The review's extra hedging ("does not establish the construction direction", "does not rule out untested hidden properties") was not adopted: two curves over different fields with the identical x at G/2 can only come from a shared x input, and the rest is boilerplate.

## 6. Practical notes for the agent
- SEC 2 v2.0 (secg.org/sec2-v2.pdf) dropped the ≤160-bit curves; their parameters are in SEC 2 v1.0 (secg.org/SEC2-Ver-1.0.pdf). Both were fetched 20 Oct and the parameters in `secg_scan.py` were verified by n·G = O.
- Pure-Python EC arithmetic is fine for 2¹⁶ multiples on prime curves (seconds) and tolerable on binary curves (minutes to hours at 571 bits). PARI/GP is much faster but was not available in the sandbox used so far; if `gp` is on PATH, `binpts.gp` is the better tool.
- The dictionary searches run at ~40–50k hash evaluations/s in pure Python; 30 M evaluations ≈ 15 min. Keep the matcher core-based for the secp constant.
- The original seeds/skips investigation, including the full ~50-invariant battery and the statistical caveats, lives in the follow-up repository and is *not* this repo's concern.
- Dan's standing style preference for write-ups: say what was found and what you'd bet on; qualify once, not three times.
