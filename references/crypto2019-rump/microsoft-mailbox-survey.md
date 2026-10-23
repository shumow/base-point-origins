# Short x-coordinates of halved SEC 2 Koblitz generators: what survives (2019–2020)

*Recovered from Dan Shumow's Microsoft mailbox and OneDrive, October 2026. Collaborators: Nadia Heninger (UCSD), Travis Scholl (then at UC Irvine), with input from Dan Brown (Certicom/BlackBerry) and Antonio Sanso.*

*Evidence note: this is a mailbox-derived survey, not an original email export or the original 2019 program. Dates and reported searches retain that provenance. The readable slide replacement and selected arithmetic were checked separately; see [the synthesis](README.md) for page references, proof-enabled results and remaining limits.*

## TL;DR

- **The observation:** the four SEC 2 `secpXXXk1` half-generator x-coordinates share a 152-bit core; 224k1 and 256k1 share the same 166-bit value. The mailbox survey attributes the wider prime-curve observation to Travis in March 2019, following Nadia's secp256k1 observation through repeated Bitcoin nonces.
- **What got done:** Crypto 2019 rump-session talk (Aug 20, 2019), titled `48ce563f89a0ed9414f5aa28ad0d96d6795f9c62`. Then a John the Ripper search for a SHA-1 preimage (nothing found), a derivation of the secp256k1 field prime and curve via CM, a private GitHub repo with a paper planned, and in June 2020 an extension to the binary Koblitz curves (sect163k1 is also short).
- **Reproduced arithmetic:** the coordinate values in the table below are independently recomputed by the modern Python and Sage scripts. Those calculations do not authenticate the chronology or establish historical search coverage.
- **New result from today's re-check:** Dan Brown's "160-bit value plus a small counter, keep the first x that lifts" theory is **ruled out in its simplest form**. On every curve, smaller low-4-bit and low-6-bit values would already have given a valid point.
- **Sage code:** your original 2019/2020 Sage code is **not in your mail or OneDrive**. Per your June 2020 email, it was pushed to `github.com/factorable/secp256k1` (private) and discussed in a private channel on Nadia's Slack. Those two places are where to recover it. What did survive is Travis's Sage snippet for deriving the secp256k1 prime, his curve-parameter gist, Nadia's slide deck, and a reconstructed script (`halve_generators.sage`, included).

---

## 1. Timeline (from email)

| Date | What happened | Source |
|---|---|---|
| Jan 2019 | Nadia was already emailing Dan Brown about the secp256k1 base point (per her Aug 20 email; that thread isn't in your mailbox) | "Re: 256k1 and 224k1", Nadia, Aug 20 2019 |
| Mar 24, 2019 | Travis Scholl emails Nadia after her AMS Hawaii talk with x(((n−1)/2)G) for 192k1/192r1/224k1/224r1/256k1/256r1/384r1/521r1. Only the k1 curves are short, and 224k1 and 256k1 give **the same value** | "256k1 and 224k1" |
| Apr 2–3, 2019 | Nadia loops you in. You reply that one value reused across 224k1 and 256k1 argues *against* a trapdoor | "Re: 256k1 and 224k1" |
| ~Aug 18, 2019 (at Crypto) | You and Nadia find the 160-bit curve in **SEC 2 v1.0** (`secg.org/SEC2-Ver-1.0.pdf`). secp160k1 gives exactly the 160-bit core `48ce563f…9c62` | Nadia → Travis, Aug 18 2019 |
| Aug 19–20, 2019 | Nadia runs John the Ripper (`--format=Raw-SHA1`) on all 256 variants with the top and bottom nibbles changed. **No preimage found.** Travis forwards Dan Brown's theories | "Hash candidates"; "Re: 256k1 and 224k1" |
| Aug 20, 2019 | **Crypto 2019 rump session talk** (Heninger, Scholl, Shumow). You sent Travis photos of the title slide | slides attached to Nadia's Aug 20 email |
| Sep 20–21, 2019 | Brian LaMacchia encourages follow-up. Nadia: "We should definitely write this up." She creates a GitHub repo and adds you and Travis (`tscholl2`) | "Re: 256k1 and 224k1" |
| Oct 18–31, 2019 | Antonio Sanso suggests the curves came from the CM method. Dan Brown gives a long history (j=0, D=3, GLV, the ANSI X9.62 CM cookbook, a possible Crandall-prime workaround). Travis derives the secp256k1 prime in Sage | "48ce563f89a0ed9414f5aa28ad0d96d6795f9c62" thread |
| May 2020 | Listed in your cryptanalysis update to Brian: "Analyzing derivation of ECC generator points in SecP Curves (used by bitcoin.)" | "RE: One slide on cryptanalysis projects…" |
| Jun 24, 2020 | You push updates to `factorable/secp256k1`. You tell Travis you recreated the earlier calculations, then checked the **binary Koblitz `sectXXXk1`** curves: sect163k1 gives a **126-bit** x, none of the others do, and you were searching for short x-coordinates "close" to the other generators. Discussion moved to a private channel on Nadia's Slack | "RE: github updates" |
| after Jun 2020 | Nothing more in mail. No paper was found | — |

Adjacent but separate: Nadia's "Hidden number problem fourier Sage code" (Mar 2019), from the ECDSA Fourier-analysis work that found the WolfSSL bug.

---

## 2. The core data (re-verified Oct 2026)

x((1/2)G), computed as ((n+1)/2)·G and checked by doubling back to G:

| Curve | x((1/2)G) | Bits / field bits |
|---|---|---|
| secp160k1 | `48ce563f89a0ed9414f5aa28ad0d96d6795f9c62` | 159 / 160 |
| secp192k1 | `554123b78ce563f89a0ed9414f5aa28ad0d96d6795f9c66` | 187 / 192 |
| secp224k1 | `3b78ce563f89a0ed9414f5aa28ad0d96d6795f9c63` | 166 / 224 |
| secp256k1 | `3b78ce563f89a0ed9414f5aa28ad0d96d6795f9c63` | 166 / 256 |
| sect163k1 (binary) | `23e21d6019e1211f6bd47ec180256e97` | 126 / 163 |
| secp256r1 (control) | `2afa386b…f1f2da8db6` | 254 / 256 |

**Structure:** the 152-bit core `8ce563f89a0ed9414f5aa28ad0d96d6795f9c6` is shared, and the low 160-bit blocks differ in the top and bottom nibbles. 192k1 has an additional prefix whose origin is unknown. The sect163k1 value does **not** visibly share the core.

**Historical measurement:** PDF page 3 of the 2019 talk reports that 99% of repeated Bitcoin ECDSA nonces in that investigation were (n−1)/2; page 5 links the short value to lower transaction costs. The underlying dataset and methodology have not been revalidated here, and this is not a statement about today's blockchain.

---

## 3. Hypotheses and their status

| # | Hypothesis | Status |
|---|---|---|
| H1 | The 160-bit value is SHA-1 of some seed, with the top and bottom 4 bits tweaked. The SEC 2 random curves use SHA-1 seeds containing "MinghuaQu" | **Open.** The survey reports no match from JtR over 256 target variants (Aug 2019), but wordlists, rules, encodings, counts and completion status are unknown. The reported hashes.org attempt is likewise undocumented coverage. The reviewed mail does not establish whether later GPU searches occurred |
| H2 | The other k1 generators came from appending digits to the 160-bit core | Consistent with the data, but no mechanism is known. The slides call "why so many digits?" an unsolved mystery |
| H3 | (Dan Brown) 160-bit value plus a 6-bit counter, keeping the minimum value that decompresses | **Ruled out for the tested direct models.** With upper bits fixed, the actual low 6 bits are 34/38/35/35 versus first lifting 1/1/0/1. The modern Python check also rejects first-lifting searches over cleared low 4/8 bits and the top nibble, upward and downward with all other bits fixed. Counters before hashing or another transformation are **not tested** |
| H4 | It's a backdoor | **Not claimed.** The slides explicitly say it's "some kind of undocumented artifact from the generation procedure." Your Apr 2019 point: reusing one value across 224k1 and 256k1 is evidence against a trapdoor |
| H5 | The curves themselves (not G) came from the CM method | **Arithmetic reproduced, historical workflow not established.** For j=0, D=-3, the CM calculation reproduces secp256k1's p and n; the modern Sage reconstruction uses proof-enabled primality. This does not identify G or prove what code the designers used. The reported Crandall-patent explanation remains a rumor |
| H6 | Why publish 2·H instead of H? | **Open.** Dan Brown wondered whether (1/2)G was a test vector. Halve-and-add only makes sense for binary curves |
| H7 | Does the property help with discrete log? | Not believed to (slides). Dan Brown notes the base point doesn't matter for ECDH because of random self-reducibility, and probably only marginally for ECDSA |

People Dan Brown named as possibly involved at Certicom: Rob Gallant, Rob Lambert, Simon Blake-Wilson, Minghua Qu.

---

## 4. Code and artifacts: what's recoverable

| Artifact | Status | Where |
|---|---|---|
| **Your 2019/2020 Sage code** (halving, the sect search, the "nearby short x" search) | **Not in mail or OneDrive.** The OneDrive `.sage` files (ECWriter, EdwardsIsogeny, HuffIsogeny) date from 2013 and belong to other projects | Likely `github.com/factorable/secp256k1` (private; you were a collaborator and pushed in June 2020) and the private channel on Nadia's Slack |
| Rump-session slides (Beamer PDF, Aug 19 2019 draft) | Readable replacement reviewed locally on 22 Oct 2026; not redistributed here | Identity and page references in [the synthesis](README.md) |
| Travis's Sage derivation of the secp256k1 prime/order | **Recovered**, verbatim logic | Email Oct 27 2019. Folded into `halve_generators.sage` |
| Travis's curve-parameter gist (NIST, SEC, Curve25519, with the NIST seed-verification code) | **Live** | https://gist.github.com/tscholl2/412b6c8cc44c84debbe08c0cca98b42a |
| Reconstructed analysis script | **New, not recovered original code** | `halve_generators.sage`, now executed in Sage with explicit proof-enabled primality; selected arithmetic also reproduced in Python |
| Antonio Sanso's annotated slide screenshot; your photos of the talk | In mail | Oct 21 2019 forward; Aug 20 2019 reply |

**To recover the originals:** `gh repo clone factorable/secp256k1` (or ask Nadia, since `factorable` is her handle). If access lapsed, Nadia can re-add you. Also ask her to export the Slack channel.

---

## 5. Suggested next steps

1. Pull the GitHub repo and Slack export, then diff them against this survey.
2. Clarify how the proposed counter entered the procedure. Direct low-field and top-nibble first-lifting searches in both directions have been checked; counters before hashing or another transform remain open.
3. GPU SHA-1 preimage search over structured seeds (e.g., "MinghuaQu" + counter, mirroring the SEC 2 random-curve seeds). Hashcat makes this cheap now.
4. Do the same with sect233k1 / 283k1 / 409k1 / 571k1, and look at sect163k1's relationship (if any) to the 160-bit core.
5. Decide whether to write it up. Nadia's Sep 2019 "we should definitely write this up" never turned into a draft that we know of.
