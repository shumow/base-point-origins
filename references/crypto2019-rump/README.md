# The 2019–2020 investigation: what survives, and what it adds to this repository

*Added 2026-10-22 from two mailbox surveys Dan ran on 22 Oct 2026 (Microsoft work account and OneDrive; personal Gmail). Collaborators on the original work: Nadia Heninger, Travis Scholl; input from Dan Brown and Antonio Sanso. Every number quoted below was re-checked in this repository by `scripts/verify_crypto2019.py` and `halve_generators.sage`; the chronology and the 2019 search coverage are what the mailbox surveys report, no more — see "Evidence levels".*

## Files

| File | What it is | Provenance |
|---|---|---|
| `microsoft-mailbox-survey.md` | Timeline (Mar 2019 – Jun 2020), hypotheses H1–H7 with status, list of recoverable artifacts, next steps | Survey of the Microsoft mailbox and OneDrive, 22 Oct 2026, kept verbatim apart from a one-line header; where this README disagrees with it (152-bit core, seven primes, counter theory, slides), this README is the correction |
| `gmail-survey.md` (+ `gmail-survey.rtf`) | Mostly negative search of the personal Gmail; the useful part is three messages with attachments nobody has opened yet (§Leads), identified by date, subject and filename | Survey of shumow@gmail.com, 22 Oct 2026; Markdown made with pandoc. Both files were edited after the fact to remove the private Gmail links and add a header note, so the RTF is not byte-identical to the survey as delivered |
| `factorable-secp256k1/` | **The original 2019–20 Sage code**, recovered 23 Oct 2026: Dan downloaded the private `factorable/secp256k1` repo as a zip (flat directory; these five files are all of it). `seck_curves.sage` checks the four secp\*k1 and six sect\*k1 parameter sets and prints x(G/2) and the cofactor-coset preimages; `sectk_small_x_srch.sage` + `run_sectk_short_coord_srch.sage` is the June 2020 search over σᵏ(2⁻ʲ·G) + T (Frobenius powers × inverse powers of two × E[h]) with its output in `short_x_coordinate_search_sectXXXk1_curves.txt`; `sectk_endomorphism_srch.sage` tests G = P + σ(P) on sect233k1 (no recorded output). Replicated by `scripts/sectk_2020_checks.py` → `results/sectk-2020-checks.txt` | Verbatim from the zip; sect239k1's Gy string carries a stray space that Sage's parser ignores |
| `halve_generators.sage` | **Oct 2026 reconstruction**, not the 2019 code: halving on the four secp\*k1 curves, direct low-bit counter tests, the P-256 control, sect163k1, and the CM calculation | Executed in Sage with explicit proof-enabled primality; output in `../../results/verify-crypto2019-sage.txt` |

**Slides reviewed, not redistributed.** The original mailbox export was a rights-protected wrapper and was not added. Dan supplied a readable 13-page replacement on 22 Oct 2026, titled `48ce563f89a0ed9414f5aa28ad0d96d6795f9c62`, by Nadia Heninger, Travis Scholl and Dan Shumow, dated 19 Aug 2019. Its SHA-256 is `af0bab53380f6d4ea493ec8950a4b2ea4f8ba7f3bf352231fe3392c488ba9afc`. Page numbers below are PDF pages, including overlay pages. The attachment was reviewed locally, not copied into this repository; reading access is not treated as permission to redistribute it.

## Evidence levels

- **Directly checked in the slides:** page 7 lists the four half-generator coordinates; page 11 labels SHA-1 and top/bottom-nibble changes as hypotheses; page 12 explicitly does not claim a backdoor; page 13 asks former Certicom employees and GPU volunteers for help.
- **Historical measurement, not revalidated:** page 3 reports that 99% of repeated Bitcoin ECDSA nonces in the 2019 investigation were `(n-1)/2`; page 5 links the short value to cheaper transactions. The dataset and measurement method are not supplied here.
- **Mailbox-survey reports:** the timeline, John the Ripper run, June 2020 follow-up, and original code locations. This review did not inspect the original messages, private repository or Slack archive.
- **Computation:** the Python and Sage scripts check the arithmetic (coordinates, core, counter models, the CM window). Arithmetic says what is true of the published values, not which program produced them; that is the one caveat for everything below, stated here once.

Private Gmail links were removed from both survey files (they remain in this branch's earlier history); dates, subjects and attachment names stay as retrieval cues. Clear permissions before publishing further correspondence or attachments.

Also not mirrored: Travis Scholl's parameter gist (NIST.sage with the SHA-1 seed check, SEC.sage, Curve25519.sage), https://gist.github.com/tscholl2/412b6c8cc44c84debbe08c0cca98b42a — the sandbox could not fetch gist raw files.

## What the 2019 work established, against what this repository already had

| Claim | 2019–20 source | Status here |
|---|---|---|
| x(G/2) is short on secp192k1/224k1/256k1 and *identical* on 224k1 and 256k1; the r-curves are full-size | Travis Scholl → Nadia, 24 Mar 2019, after her AMS Hawaii talk; Nadia had the 256k1 case from Bitcoin | Reproduced independently, `notes/record.md` §7.2 |
| secp160k1 (SEC 2 v1.0 only) gives the bare 160-bit value `48ce563f…9c62`; that became the talk's title | Dan + Nadia at Crypto, 18 Aug 2019 | Reproduced, §7.2 |
| How it was noticed: 99% of *repeated* Bitcoin ECDSA nonces in the 2019 investigation were (n−1)/2, and the short r makes the transaction cheaper | Rump slides, PDF pages 3 and 5 (checked by Dan, 22 Oct 2026) | **New to the repo.** The practical hook for any write-up and the reason the observation exists at all. The 2019 dataset is not re-measured here |
| SHA-1 preimage search with John the Ripper over the 256 variants of the 160-bit value with top and bottom nibble changed: **nothing** | Nadia, 19–20 Aug 2019 ("Hash candidates"), per the mailbox survey | **New to the repo** as a logged negative, with **unknown candidate coverage**: wordlist, rules, encodings and completion are not in mail, so it excludes no named corpus until Nadia says what ran. The repo's three pure-Python passes (~70 M evaluations, HANDOFF §3) and the hashcat V1 plan are its successor |
| Dan Brown's theory: a 160-bit value plus a small counter in the low bits, keep the first x that lifts to a point | Forwarded by Travis, 19–20 Aug 2019 | Excluded for a counter in the low 4, 6 or 8 bits counting up or down, and for the top nibble in either direction, with all other bits fixed (`verify_crypto2019.py` §3). A counter applied before a hash or other transform is not tested. The repo's `nibble_rules.py` (~11,500 rules, record §7.3.3) is the broader version |
| The curves (not G) come from the CM method: j = 0, D = −3; p = 2²⁵⁶ − 2³² − 977 is the largest prime below 2²⁵⁶ − 2³² − 1 for which some y² = x³ + b has prime order, and that order is n | Antonio Sanso (18 Oct 2019), Dan Brown's history, Travis Scholl's Sage (27 Oct 2019) | **Verified here**: the window holds seven primes, three of them 1 mod 3, and of their 18 twist orders exactly one is prime, secp256k1's n (`verify_crypto2019.py` §6, probable-prime; `halve_generators.sage`, proof-enabled). About the curve, not the base point; the write-up can say "the curve is explained, the generator is not" |
| sect163k1's half-generator has a 126-bit x; none of the other sect\*k1 do; a search for short x "close to" the other generators | Dan, 24 Jun 2020, pushed to `factorable/secp256k1` | Reproduced independently, record §7.1 (K-163 = 126 bits, nine other binary curves random-looking, all 28 cofactor preimages checked). The 2020 code (`factorable-secp256k1/`) shows what "close to" meant: the m²·h points σᵏ(2⁻ʲ·G) + T, 0 ≤ j, k < m, T ∈ E[h]. Its recorded minima (215/219/266/390/549 bits on 233/239/283/409/571) are each recomputed from their (k, j) in `sectk_2020_checks.py` and are within two bits of the uniform expectation for a grid that size; only sect163k1's G/2 stands out. A different scalar set from the repo's k ≤ 2¹⁶ scans, so an independent negative |
| G = P + σ(P) for a P with short x (the "endomorphism hypothesis", tested on sect233k1 in 2020 with no recorded result) | `sectk_endomorphism_srch.sage` | **Negative on all six sect\*k1 curves** (`sectk_2020_checks.py` §2): x of (1 + σ)⁻¹G + T is full-size for every T ∈ E[h]; same for (1 − σ)⁻¹G |
| "Why publish 2H rather than H? Was G/2 a test vector?" (Dan Brown) | Oct 2019 thread | Open. One thing the repo's scan adds: on K-163, h = 2, so G = 2P is just G = h·P; on the secp\*k1 curves h = 1 and G = 2P anyway; on sect233k1 … 571k1 (h = 4) neither G/2 nor G/4 is short. So neither "always double" nor "multiply by the cofactor" explains all of Certicom's Koblitz generators at once |
| Not a backdoor; "an undocumented artifact of the generation procedure"; reuse across 224k1/256k1 argues against a trapdoor (Dan, Apr 2019) | Slides; Apr 2019 email | Same framing as `README.md` and HANDOFF §1 |
| People Dan Brown named at Certicom: Gallant, Lambert, Blake-Wilson, Qu; the r-curve SEEDs embed "Minghua Qu" | Oct 2019 | Already in `wordlists/certicom.txt` and `scripts/k163/strings_certicom.py` |

Net: the repository had independently re-derived everything computational from 2019–20. What the surveys add is the record itself (dates, who saw what first, who was consulted), one logged negative of unknown coverage (JtR), the Bitcoin-nonce origin story, the CM derivation of the curve, and pointers to where the original code and slides are. A full comparison with the 2019–20 experiments still needs the original code (§Leads).

## Reproducing the arithmetic

Run from the repository root, in a shell with the named interpreter available:

```sh
python3 scripts/verify_crypto2019.py
sage references/crypto2019-rump/halve_generators.sage
python3 -m unittest discover -s tests -p 'test_crypto2019.py' -v
```

The standard-library Python run uses 32-round Miller-Rabin and explicitly reports probable-prime results. The independent Sage run enumerates every odd modulus in `[2^256 - 2^32 - 977, 2^256 - 2^32)` with `is_prime(proof=True)`, then checks all six CM candidate orders for each of the three split primes with the same proof-enabled setting. For the four other prime moduli, `p = 2 mod 3`, every j = 0 curve has even order `p+1`.

Recorded outputs: [`verify-crypto2019.txt`](../../results/verify-crypto2019.txt) and [`verify-crypto2019-sage.txt`](../../results/verify-crypto2019-sage.txt). The test compares a fresh Python run against the recorded output byte for byte, and runs the Sage script (preparsed in memory, so no `.sage.py` is left behind) only when Sage is installed.

## Runbook: re-running the full 2020 grid (unattended, CPU only)

The quick check above recomputes only the recorded minima. To confirm they are the *global* minima of the m²·h grid, run from the repository root with a stock Python 3 (standard library only, no Sage, no GPU):

```sh
python3 -m unittest tests.test_sectk2020          # planted controls, ~2 s; must pass first
python3 scripts/sectk_2020_checks.py --full       # all six curves, smallest first
```

- Appends one line per curve to `results/sectk-2020-full-grid.txt` the moment that curve finishes, so a killed run keeps what it had; prints progress with an ETA to stderr about every 5% of j. Exit 0 if every global minimum matches the 2020 record, 1 otherwise.
- Measured per-curve time on one sandbox CPU core: sect163k1 0.2 min, 233k1 0.9, 239k1 1.0, 283k1 1.9, 409k1 5.7, 571k1 15.1 — about 25 min in all. Name curves to run a subset or to resume: `--full sect409k1 sect571k1`.
- When it finishes: commit `results/sectk-2020-full-grid.txt` and replace "The full grid was not re-run here" in `notes/record.md` §7.3.6 with the outcome. If any curve **DIFFERS** from the 2020 record, do not edit `RECORDED_2020` in the script; report the new (bits, k, j, x) and leave both on record.

## Two corrections to the repository, found while checking

1. **The shared core is 152 bits, not 148.** The low 160 bits of the four values are `48ce563f…9c62`, `78ce563f…9c66`, `78ce563f…9c63`, `78ce563f…9c63`. HANDOFF §2.1 and record §7.2 call bits 4–151 (`ce563f…9c6`) the core and say the top *byte* (48 vs 78) varies; but the byte's low nibble is `8` on all four, so bits 4–155 (`8ce563f89a0ed9414f5aa28ad0d96d6795f9c6`) are shared and only the top nibble (4 vs 7) and the bottom nibble (2, 6, 3, 3) differ. The 2019 slides had it right ("top and bottom nibbles changed", 16 × 16 = 256 variants). Consequence for the hashcat side: `scripts/make_targets.py` enumerates the top byte and bottom nibble, 4,096 completions per reading, 12,288 in all. That is a superset of the 256 per reading actually needed, so no result is wrong, but the matcher in `secg_core_search.py` compares bits 4–151 and could compare 4–155. Not changed in this pass; noted in HANDOFF, record and `hash-angle.md`.
2. **Two exponent typos in record §7.3.2 / HANDOFF §4.2.** c − a = 0x3b3·2¹⁵⁶ + 1 (not 2¹⁵²) and b − c = 0x55412·2¹⁶⁸ + 3 (not 2¹⁷²), with a, b, c the 160k1, 192k1, 224/256k1 values. The 32-bit-word picture given there (`0000003b 78ce563f …` vs `0554123b 78ce563f …`) was already right; fixed in place.

## Leads only Dan can follow

1. **Original 2019–20 Sage code**: ~~not in either mailbox or OneDrive~~ **recovered 23 Oct 2026** from `github.com/factorable/secp256k1` (see `factorable-secp256k1/` above; the repo held only those five files, so Travis's and Nadia's 2019 code was never pushed there). Still outstanding: the private channel on Nadia's Slack, which the June 2020 email says carried the discussion.
2. **The slide deck**: the readable replacement has now been reviewed (see above). Confirm redistribution permissions before adding any copy to the repository.
3. **Unopened attachments** (retrieval cues in `gmail-survey.md`): `compute-all-the-keys.png` (Nadia, 19 Aug 2019 23:14, and Dan's reply 23:22); and a `paper.pdf` forwarded between the personal and Microsoft addresses in **June 2022**. Its subject matter remains unknown; search terms and a generic filename do not identify it as a draft of this work.
4. **Ask Nadia** which wordlist the Aug 2019 John the Ripper run used, so the negative can be logged with a candidate space, like the repo's other negatives.
5. **Ask Dan Brown** what he tried on hashes.org and precisely where a counter entered his proposed procedure. Only the direct fixed-other-bits searches described above have been checked; a counter before hashing or another transformation remains open.
6. Antonio Sanso's annotated slide screenshot (forward of 21 Oct 2019) and Dan's photos of the talk (20 Aug 2019) are in the Microsoft mailbox if a write-up wants them.
