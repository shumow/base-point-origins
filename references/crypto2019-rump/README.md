# The 2019–2020 investigation: what survives, and what it adds to this repository

*Added 2026-10-22 from two mailbox surveys Dan ran on 22 Oct 2026 (Microsoft work account and OneDrive; personal Gmail). Collaborators on the original work: Nadia Heninger, Travis Scholl; input from Dan Brown and Antonio Sanso. Every number quoted below was re-checked in this repository by `scripts/verify_crypto2019.py` (output in `results/verify-crypto2019.txt`).*

## Files

| File | What it is | Provenance |
|---|---|---|
| `microsoft-mailbox-survey.md` | Timeline (Mar 2019 – Jun 2020), hypotheses H1–H7 with status, list of recoverable artifacts, next steps | Survey of the Microsoft mailbox and OneDrive, 22 Oct 2026 |
| `gmail-survey.md` (+ the original `gmail-survey.rtf`) | Mostly negative search of the personal Gmail; the useful part is three message links with attachments nobody has opened yet (§Leads) | Survey of shumow@gmail.com, 22 Oct 2026; Markdown made with pandoc |
| `halve_generators.sage` | **Oct 2026 reconstruction**, not the 2019 code: halving on the four secp\*k1 curves, Dan Brown's counter test, the P-256 control, sect163k1, and Travis Scholl's CM derivation of the secp256k1 prime | Written during the Microsoft survey; "not yet run in Sage" per its header. Everything it asserts now passes in pure Python here |

**Not here, on purpose.** The rump-session slide deck (`secp256k1_rump_slides_Crypto2019.pdf`) as it came out of the Microsoft mailbox is a Microsoft IRM wrapper: one visible page saying "This PDF file is protected", the real deck encrypted inside as `MicrosoftIRMServices Protected PDF.pdf`, sensitivity label *Highly Confidential \ Microsoft FTE*. It cannot be opened outside the tenant and it does not belong in a public repository. SHA-256 of that wrapped file, for identification: `3ff95451cc40a59cb0340bfd7f57af939b0f2fb04cf43647f2f2fb702ff39b5e`. The clean copy is the `secp256k1.pdf` attached to Nadia's Gmail message of 20 Aug 2019, 00:35 Pacific, in the thread *allthekeys* (link in `gmail-survey.md`). Drop it in this folder as `secp256k1_rump_slides_Crypto2019.pdf`.

Also not mirrored: Travis Scholl's parameter gist (NIST.sage with the SHA-1 seed check, SEC.sage, Curve25519.sage), https://gist.github.com/tscholl2/412b6c8cc44c84debbe08c0cca98b42a — the sandbox could not fetch gist raw files.

## What the 2019 work established, against what this repository already had

| Claim | 2019–20 source | Status here |
|---|---|---|
| x(G/2) is short on secp192k1/224k1/256k1 and *identical* on 224k1 and 256k1; the r-curves are full-size | Travis Scholl → Nadia, 24 Mar 2019, after her AMS Hawaii talk; Nadia had the 256k1 case from Bitcoin | Reproduced independently, `notes/record.md` §7.2 |
| secp160k1 (SEC 2 v1.0 only) gives the bare 160-bit value `48ce563f…9c62`; that became the talk's title | Dan + Nadia at Crypto, 18 Aug 2019 | Reproduced, §7.2 |
| How it was noticed: 99% of *repeated* Bitcoin ECDSA nonces are (n−1)/2, because the short r makes the transaction cheaper (slides 2–3) | Rump talk, 20 Aug 2019 | **New to the repo.** This is the practical hook for any write-up and the reason the observation exists at all |
| SHA-1 preimage search with John the Ripper over the 256 variants of the 160-bit value with top and bottom nibble changed: **nothing** | Nadia, 19–20 Aug 2019 ("Hash candidates") | **New to the repo** as a logged negative. Wordlist unknown (ask Nadia). The repo's three pure-Python passes (~70 M evaluations, HANDOFF §3) and the hashcat V1 plan are its successor |
| Dan Brown's theory: a 160-bit value plus a small counter in the low bits, keep the first x that lifts to a point | Forwarded by Travis, 19–20 Aug 2019 | Ruled out in its naive form by the Oct 2026 survey (low 4 and 6 bits); `verify_crypto2019.py` §3 re-does it for 4, 6 and 8 bits, counting up and down, and for the *top* nibble. The repo's `nibble_rules.py` (~11,500 rules, record §7.3.3) is the broader version |
| The curves (not G) come from the CM method: j = 0, D = −3; p = 2²⁵⁶ − 2³² − 977 is the largest prime below 2²⁵⁶ − 2³² − 1 for which some y² = x³ + b has prime order, and that order is n | Antonio Sanso (18 Oct 2019), Dan Brown's history, Travis Scholl's Sage (27 Oct 2019) | **Verified here** (`verify_crypto2019.py` §6: five primes in the window, one with a prime-order twist). About the curve, not the base point; the write-up can say "the curve is explained, the generator is not" |
| sect163k1's half-generator has a 126-bit x; none of the other sect\*k1 do; a search for short x "close to" the other generators | Dan, 24 Jun 2020, pushed to `factorable/secp256k1` | Reproduced independently, record §7.1 (K-163 = 126 bits, nine other binary curves random-looking, all 28 cofactor preimages checked) |
| "Why publish 2H rather than H? Was G/2 a test vector?" (Dan Brown) | Oct 2019 thread | Open. One thing the repo's scan adds: on K-163, h = 2, so G = 2P is just G = h·P; on the secp\*k1 curves h = 1 and G = 2P anyway; on sect233k1 … 571k1 (h = 4) neither G/2 nor G/4 is short. So neither "always double" nor "multiply by the cofactor" explains all of Certicom's Koblitz generators at once |
| Not a backdoor; "an undocumented artifact of the generation procedure"; reuse across 224k1/256k1 argues against a trapdoor (Dan, Apr 2019) | Slides; Apr 2019 email | Same framing as `README.md` and HANDOFF §1 |
| People Dan Brown named at Certicom: Gallant, Lambert, Blake-Wilson, Qu; the r-curve SEEDs embed "Minghua Qu" | Oct 2019 | Already in `wordlists/certicom.txt` and `scripts/k163/strings_certicom.py` |

Net: the repository had independently re-derived everything computational from 2019–20. What the surveys add is the record itself (dates, who saw what first, who was consulted), one logged negative (JtR), the Bitcoin-nonce origin story, the CM derivation of the curve, and pointers to where the original code and slides are.

## Two corrections to the repository, found while checking

1. **The shared core is 152 bits, not 148.** The low 160 bits of the four values are `48ce563f…9c62`, `78ce563f…9c66`, `78ce563f…9c63`, `78ce563f…9c63`. HANDOFF §2.1 and record §7.2 call bits 4–151 (`ce563f…9c6`) the core and say the top *byte* (48 vs 78) varies; but the byte's low nibble is `8` on all four, so bits 4–155 (`8ce563f89a0ed9414f5aa28ad0d96d6795f9c6`) are shared and only the top nibble (4 vs 7) and the bottom nibble (2, 6, 3, 3) differ. The 2019 slides had it right ("top and bottom nibbles changed", 16 × 16 = 256 variants). Consequence for the hashcat side: `scripts/make_targets.py` enumerates the top byte and bottom nibble, 4,096 completions per reading, 12,288 in all. That is a superset of the 256 per reading actually needed, so no result is wrong, but the matcher in `secg_core_search.py` compares bits 4–151 and could compare 4–155. Not changed in this pass; noted in HANDOFF, record and `hash-angle.md`.
2. **Two exponent typos in record §7.3.2 / HANDOFF §4.2.** c − a = 0x3b3·2¹⁵⁶ + 1 (not 2¹⁵²) and b − c = 0x55412·2¹⁶⁸ + 3 (not 2¹⁷²), with a, b, c the 160k1, 192k1, 224/256k1 values. The 32-bit-word picture given there (`0000003b 78ce563f …` vs `0554123b 78ce563f …`) was already right; fixed in place.

## Leads only Dan can follow

1. **Original 2019–20 Sage code**: not in either mailbox or OneDrive. Per the 24 Jun 2020 email it is in `github.com/factorable/secp256k1` (private; Nadia's org, Dan and `tscholl2` were collaborators) and the discussion continued in a private channel on Nadia's Slack. Clone the repo, diff its results against `notes/record.md`, and ask Nadia for a Slack export.
2. **The slide deck**: get the Gmail copy (above) and add it here.
3. **Unopened attachments** (Gmail links in `gmail-survey.md`): `compute-all-the-keys.png` (Nadia, 19 Aug 2019 23:14, and Dan's reply 23:22); and a `paper.pdf` forwarded between the personal and Microsoft addresses in **June 2022**, surfaced by a search for secp256r1 and Nadia + curve — possibly the write-up Nadia proposed in Sep 2019, which the Microsoft survey says was never found.
4. **Ask Nadia** which wordlist the Aug 2019 John the Ripper run used, so the negative can be logged with a candidate space, like the repo's other negatives.
5. **Ask Dan Brown** what he tried on hashes.org and whether his "160-bit value + counter" theory meant something other than counting up in the low bits (counting down, top bits, and a counter before a transform are now also excluded or checked; see `verify_crypto2019.py` §3).
6. Antonio Sanso's annotated slide screenshot (forward of 21 Oct 2019) and Dan's photos of the talk (20 Aug 2019) are in the Microsoft mailbox if a write-up wants them.
