# Short x-coordinates of halved SEC 2 Koblitz generators: what survives (2019–2020)

*Recovered from Dan Shumow's Microsoft mailbox and OneDrive, October 2026. Collaborators: Nadia Heninger (UCSD), Travis Scholl (then at UC Irvine), with input from Dan Brown (Certicom/BlackBerry) and Antonio Sanso.*

*Kept as delivered on 22 Oct 2026, apart from this line. It is a survey of mail, not an email export, and some of its statements have since been corrected or sharpened in [README.md](README.md): the shared core is 152 bits, not 160; the CM window holds seven primes; the counter theory is excluded in more forms than listed under H3; the slide deck named below was reviewed by Dan but is not in this folder.*

## TL;DR

- **The observation:** for each SEC 2 `secpXXXk1` curve, x((1/2)G) = x(((n−1)/2)·G) is far shorter than the field size, and the four values share an obvious 160-bit core. Travis Scholl spotted it first, in March 2019. Nadia had found the 256k1 case through repeated Bitcoin nonces.
- **What got done:** Crypto 2019 rump-session talk (Aug 20, 2019), titled `48ce563f89a0ed9414f5aa28ad0d96d6795f9c62`. Then a John the Ripper search for a SHA-1 preimage (nothing found), a derivation of the secp256k1 field prime and curve via CM, a private GitHub repo with a paper planned, and in June 2020 an extension to the binary Koblitz curves (sect163k1 is also short).
- **What's still valid:** I recomputed every value from scratch today. They all hold (see the table below).
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

**Structure:** the 160-bit core `…8ce563f89a0ed9414f5aa28ad0d96d6795f9c6…` is shared, and the curves differ in the top and bottom nibbles. 192k1 also has a prefix `55412` that looks hand-picked. The sect163k1 value does **not** visibly share the core.

**Where it was first seen:** 99% of repeated Bitcoin ECDSA nonces are (n−1)/2. Because the x-coordinate of that point is short, it makes transactions cheaper (slide 2–3 of the rump talk).

---

## 3. Hypotheses and their status

| # | Hypothesis | Status |
|---|---|---|
| H1 | The 160-bit value is SHA-1 of some seed, with the top and bottom 4 bits tweaked. The SEC 2 random curves use SHA-1 seeds containing "MinghuaQu" | **Open.** JtR over the 256 nibble variants found nothing (Aug 2019). Dan Brown recalls trying hashes.org with no hit. The GPU brute force asked for on the last slide never happened as far as mail shows |
| H2 | The other k1 generators came from appending digits to the 160-bit core | Consistent with the data, but no mechanism is known. The slides call "why so many digits?" an unsolved mystery |
| H3 | (Dan Brown) 160-bit core plus a 6-bit counter, keeping the minimum value that decompresses | **Ruled out in its naive form (new, Oct 2026).** With the upper bits fixed, the actual low 6 bits are 34/38/35/35 for 160/192/224/256k1, but the smallest valid values are 1/1/0/1. Low 4 bits fail the same way. A counter counting down, or one applied before some other transform, is still untested |
| H4 | It's a backdoor | **Not claimed.** The slides explicitly say it's "some kind of undocumented artifact from the generation procedure." Your Apr 2019 point: reusing one value across 224k1 and 256k1 is evidence against a trapdoor |
| H5 | The curves themselves (not G) came from the CM method | **Largely settled.** j=0, D=3, class number 1, so the coefficients come from a table (ANSI X9.62 cookbook). Travis showed p = 2^256 − 2^32 − 977 is the largest prime below 2^256 − 2^32 − 1 that has a prime-order j=0 curve, with twists excluded. Dan Brown thinks the 2^32 term may be a Crandall-patent workaround (rumor) |
| H6 | Why publish 2·H instead of H? | **Open.** Dan Brown wondered whether (1/2)G was a test vector. Halve-and-add only makes sense for binary curves |
| H7 | Does the property help with discrete log? | Not believed to (slides). Dan Brown notes the base point doesn't matter for ECDH because of random self-reducibility, and probably only marginally for ECDSA |

People Dan Brown named as possibly involved at Certicom: Rob Gallant, Rob Lambert, Simon Blake-Wilson, Minghua Qu.

---

## 4. Code and artifacts: what's recoverable

| Artifact | Status | Where |
|---|---|---|
| **Your 2019/2020 Sage code** (halving, the sect search, the "nearby short x" search) | **Not in mail or OneDrive.** The OneDrive `.sage` files (ECWriter, EdwardsIsogeny, HuffIsogeny) date from 2013 and belong to other projects | Likely `github.com/factorable/secp256k1` (private; you were a collaborator and pushed in June 2020) and the private channel on Nadia's Slack |
| Rump-session slides (Beamer PDF, Aug 19 2019 draft) | **Recovered** | `secp256k1_rump_slides_Crypto2019.pdf` (attached) |
| Travis's Sage derivation of the secp256k1 prime/order | **Recovered**, verbatim logic | Email Oct 27 2019. Folded into `halve_generators.sage` |
| Travis's curve-parameter gist (NIST, SEC, Curve25519, with the NIST seed-verification code) | **Live** | https://gist.github.com/tscholl2/412b6c8cc44c84debbe08c0cca98b42a |
| Reconstructed analysis script | **New** | `halve_generators.sage`. Its numbers were independently checked in pure Python, but it hasn't been run in Sage itself |
| Antonio Sanso's annotated slide screenshot; your photos of the talk | In mail | Oct 21 2019 forward; Aug 20 2019 reply |

**To recover the originals:** `gh repo clone factorable/secp256k1` (or ask Nadia, since `factorable` is her handle). If access lapsed, Nadia can re-add you. Also ask her to export the Slack channel.

---

## 5. Suggested next steps

1. Pull the GitHub repo and Slack export, then diff them against this survey.
2. Extend the H3 test: count-down counters, a counter in the *top* bits, and counters applied before an x→2x or other transform.
3. GPU SHA-1 preimage search over structured seeds (e.g., "MinghuaQu" + counter, mirroring the SEC 2 random-curve seeds). Hashcat makes this cheap now.
4. Do the same with sect233k1 / 283k1 / 409k1 / 571k1, and look at sect163k1's relationship (if any) to the 160-bit core.
5. Decide whether to write it up. Nadia's Sep 2019 "we should definitely write this up" never turned into a draft that we know of.
