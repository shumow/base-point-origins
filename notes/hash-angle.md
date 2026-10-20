# The hash angle: what the Merkle–Damgård structure does and does not give us

*Written 2026-10-20 from Dan's voice notes, with the mathematics checked. This is the plan for treating the secp\*k1 constant (and the K-163 value) as hash outputs and recovering the input. References in `references/README.md`.*

## 1. The target, restated as a hash problem

Working hypothesis H1 from `plan.md`: the 160-bit block under the secp\*k1 half-generators is a digest — SHA-1 by era and size, SHA-0 or RIPEMD-160 as outside chances — of a short human-chosen string, and the per-curve top byte and last nibble are post-hoc adjustments. So the thing to invert is

    D = SHA-1(s),   with   D[4..151] = ce563f89a0ed9414f5aa28ad0d96d6795f9c6

and s short: a name, a phrase, a date. "Short" matters: any s of at most 55 bytes is a **single-block** message. After padding, the 16 message words are

    W0..Wk      the string bytes (big-endian words), then 0x80 and zero bytes
    W(k+1)..W13 zero
    W14         0
    W15         8·len(s)

For "Certicom" (8 bytes): W0 = 43657274, W1 = 69636f6d, W2 = 80000000, W3…W14 = 0, W15 = 0x40. So for a fixed candidate length, only ⌈len/4⌉ + 1 words are unknown and the rest of the block is fixed. That is the structure to exploit.

## 2. What is invertible, precisely

SHA-1's compression function is Davies–Meyer: with the block cipher E_M (80 steps keyed by the expanded message words W0…W79) acting on the 160-bit chaining value,

    H_out = E_M(H_in) + H_in        (word-wise addition mod 2^32: the "feed-forward")

Two different statements, one true and one false, need separating:

**True — the step function is a permutation given the message word.** One SHA-1 step maps (A, B, C, D, E) to (T, A, B≪30, C, D) with T = (A≪5) + f(B,C,D) + E + K + W_t. Given W_t, this is invertible: from the new state read off A, B, C, D (as the 2nd–5th words, un-rotating the third) and solve for E = T − (A≪5) − f(B,C,D) − K − W_t. Hence E_M is a permutation of the 160-bit state for every M, and *given M and any five consecutive working states you can reconstruct the entire 80-step computation in both directions*. This is exactly the fact counter-cryptanalysis uses (Stevens 2013; Stevens–Shumow 2017): from the known execution of a message, recompute an alternate message's working states forwards from a chosen step and backwards to step 0 to recover its alternate IHV_in, then forwards to the end to check for a collision. Information-theoretically: the cipher part loses nothing, as Dan says.

**False as stated — "given the message block and the output chaining value you can recover the input chaining value."** The map H_in ↦ E_M(H_in) + H_in is *not* a permutation; the feed-forward is precisely what makes the compression function one-way, and for a random M it behaves like a random function (collisions, non-surjectivity). The step inversion recovers H_in from the *final working state* E_M(H_in), not from H_out. To get the final working state from H_out you must already know H_in.

**For a single-block message this collapses into something useful but not magic.** H_in is the standard IV, so it *is* known, and the final working state is known too: E_M(IV) = D − IV. So we have a known plaintext/ciphertext pair (IV, D − IV) for the 80-step cipher E_M, and the unknown is the key M — a short string in known positions, with most of the 16 message words fixed by the padding. Running steps backwards from D − IV is possible for as long as the W_t involved are known; running forwards from IV likewise. Where the two meet, the unknown words must reconcile them. That is the shape of a meet-in-the-middle preimage attack, and on full 80-step SHA-1 it does not beat brute force — the message expansion spreads every unknown word across all 80 steps, and the best known preimage attacks on SHA-1 only reach ~60 steps at ~2^150+. Nothing in our setting (known padding, short string) changes that complexity picture, because the known words are the *high* ones (W5–W15) while the unknown ones (W0–W4) enter at steps 0–4 and then everywhere via expansion.

So the honest statement is: **the Merkle–Damgård structure gives us (a) a clean one-block model with ≤ 5 unknown words, (b) a fast consistency check per candidate (one compression), and (c) the forward/backward machinery to verify any candidate's internal states — but it does not give a shortcut past enumerating candidate strings.** The search is a dictionary/mask attack, and the question is purely how to generate good candidates and how fast to hash them.

## 2a. Dan's framing of the invertibility (voice, 20 Oct), and what the papers actually say

**Dan's reasoning, kept because it is the right way to see it.** In a Merkle–Damgård compression function the input block is treated like a block-cipher *key schedule*, and the chaining variable is the *plaintext* being encrypted under that key. A block cipher for a fixed key is a bijection — information-theoretically it has to be, or two chaining values would map to one and the function would be surjective-but-not-injective on the state, losing information inside the cipher. So for a known block the last block's computation can be run forwards *and* backwards; the only one-way element is the feed-forward addition at the end. For a one-block message the chaining input is the fixed IV, so nothing is unknown but the block itself, and "run it backwards from H_out − IV and see whether you land on the IV" is a cheap consistency check per candidate block — the same cost as a forward hash, but it is the mechanism counter-cryptanalysis is built on, and it parallelises. Decision from the same conversation: **V1 (the single-block, known-padding case) is the scenario to pursue first**; V2 (language-model-generated sentence candidates, or GPU burn over structured inputs) comes later, and the inputs may turn out non-semantic anyway.

**Ingestion of the three references (read 20 Oct through the fetch tool; PDFs not yet in `references/`, see its README).** The §2 statement holds exactly as written:
- *Stevens, Counter-cryptanalysis, CRYPTO 2013*, Alg. 2-1 "Last near-collision block detection", §2.2. Known: the message, its blocks, IHV_k and the stored working state WS_i at a chosen step i, and a list of triples (δB, i, δWS_i). For each triple: apply δB to the block and δWS_i to WS_i; run steps i−1 … 0 **backwards** to WS'_0; run steps i+1 … S **forwards** to WS'_S; derive IHV'_k from WS'_0 (the working state is initialised from the IHV, so this is a read-off plus un-rotation); apply the feed-forward to get IHV'_{k+1}; near-collision iff IHV'_{k+1} = IHV_{k+1}. The paper justifies the backward pass only with "the step functions of MD5 and SHA-1 are reversible." Cost: ≈ (C + 1)× one hash for C triples — each triple is one full recompression (the backward and forward halves together cover all steps); MD5 ≈ 2²⁴×, SHA-1 ≈ 15× with 14 disturbance vectors.
- *Stevens–Shumow, USENIX Security 2017*, Alg. 1 and §4.2: identical recompression — WS'_i = WS_i + δWS_i, steps i … 0 backwards to CV'_{j−1}, steps i+1 … I−1 forwards, feed-forward, compare — but gated per DV by *unavoidable bit conditions* (§3.2, §4.5–4.6), linear equations W_i[a] ⊕ W_j[b] = c on the *expanded message bits* that every attack in that DV's class must satisfy (Conjecture 3, steps 35–65). The UBC check uses only message words, so the recompression runs only when a DV survives it; a random block passes a DV's UBCs with probability 2^−|U_dv|. Overhead drops from 30–43× plain SHA-1 to 1.43–1.66× (1.60× on gcc x86-64); recompression cost per block from 32× to ≈ 0.05× SHA-1. The state ↔ chaining-value link is the initialisation (Q₀, Q₋₁, Q₋₂, Q₋₃, Q₋₄) = (a, b, RR(c,30), RR(d,30), RR(e,30)).
- *Stevens, PhD thesis (Leiden 2012)*: §1.4.5 (p. 15) states the step function is "efficiently and uniquely invertible given the output working state and the message piece," and — the sentence that settles the feed-forward point — that the addition at the end of the compression function is necessary, because without it inverting the whole function would reduce to R step pre-images and be as cheap as evaluating it. MD5 step and feed-forward: §2.2.2, Eq. 2.2–2.3 (pp. 20–21); recovering a message word from the working state: §2.7 (p. 25); SHA-0/SHA-1 description: §7.2 (p. 117); collision detection: Ch. 8 (§8.2 core principle p. 188, §8.3 MD5 p. 189, §8.4 SHA-1 p. 192). Merkle–Damgård and padding: §1.4.4 (pp. 11–12). The excerpt the fetch tool returned covered only Ch. 1–3 and the start of Ch. 6; Ch. 7–8 should be re-read from the PDF once it is in `references/`.

**Consequence for us, stated once.** Counter-cryptanalysis needs a *middle* working state with a known difference, which it gets from the collision attack's structure; we have no such handle, only the two ends (IV and H_out − IV) and an unknown block. So the machinery gives a per-candidate check and full internal-state reconstruction of any hit, not a preimage shortcut. The one genuinely new idea the 2017 paper suggests is *filtering on message-word conditions before hashing*: for our problem the analogue is structural, not differential — fixed padding words, ASCII byte ranges, word boundaries — and it is exactly what a hashcat mask encodes. `scripts/sha1_steps.py` is the step-level implementation (forward, backward, self-tested against hashlib) for confirming a hit's execution and for teaching this section.

## 3. The two plans

### V1 — single-block dictionary and mask attack, done properly on a GPU

Everything so far ran in pure Python at ~45 k SHA-1/s. A single consumer GPU does ~10^10 SHA-1/s with hashcat (mode 100, raw SHA-1) — six orders of magnitude. Two things make hashcat usable here:

1. **Partial matching via a multi-target hashlist.** We don't know the top byte (8 bits) or last nibble (4 bits) of the digest. Enumerate all 2^12 = 4096 completions of the 148-bit core into full 160-bit digests and load them as 4096 targets; hashcat checks every candidate against all of them at negligible extra cost. Do the same for the byte-reversed and word-swapped readings (3 × 4096 targets). (`scripts/make_targets.py`, to write.)
2. **Candidate generation.** (i) Dictionaries: the Certicom-era list from `HANDOFF.md` §4.1 and `plan.md` §4.1, English wordlists, name lists, plus hashcat's rule sets (case, punctuation, suffix digits, l33t); (ii) masks: all printable ASCII to length 8 (~2^52, feasible in hours on one GPU), lowercase+digits to length 10, dates in every format; (iii) the "sentence" class: two to five dictionary words with spaces, which is where the Solinas-lore-style inputs live and where a mask blows up — this is what V2 is for.

Also run the same against the K-163 value under MD5 (mode 0) with 4 targets (the two masked top bits) and under truncated SHA-1 (hashcat has no partial-match mode for 128-of-160 bits; generate the 2^32 completions is too many, so for "high/low 128 of SHA-1" readings stay in Python or write a custom OpenCL kernel).

Nothing above needs the forward/backward machinery; it is a plain known-digest search. Where the machinery *does* pay: once a candidate matches on 148 bits, reconstruct its full execution and confirm the top byte/last nibble story (does the real digest have `78` or `48` on top?), and check the alternate readings cheaply.

### V2 — semantically plausible candidates from a language model

If the input was a sentence ("Give Bob and Jerry a raise"-class), masks are hopeless (26^30) and dictionaries miss it unless someone guessed the sentence. The alternative is to generate candidates that a 1997–2000 Certicom cryptographer might have typed: an LLM prompted with the context (who, where, when, what the constant is for) produces ranked lists of phrases — names and titles, in-jokes, test strings, lines from the SEC drafts, Waterloo references — and a cheap hasher checks each with its variants. Open questions, in Dan's words: whether to spend effort on a generative model producing plausible inputs or on GPU brute force over structured inputs, or both; and the inputs might turn out to be non-semantic (a random value, a prior digest, a counter), in which case neither helps and only the archival route does.

A reasonable split: V1 covers everything mechanical (short strings, dates, names, parameter strings); V2 covers sentences; the archival pass (plan §4.5) covers the non-semantic case.

## 4. Deliverables for the next text session

1. `scripts/make_targets.py` — emit the 3 × 4096 SHA-1 target list for the secp core and the 4-target MD5 list for K-163, in hashcat format.
2. `wordlists/certicom.txt` — the Certicom-era base dictionary (names, orgs, curve names in all spellings, draft dates 1998–2000, ECC Challenge names, the r-curve SEED ASCII, the curves' own parameters as strings).
3. A hashcat run plan with estimated times per attack class, and a results log format.
4. (Optional) `scripts/sha1_steps.py` — a small step-level SHA-1 with forward and backward step functions, for confirming any hit's internal states and for teaching the point in §2 to the next reader.
