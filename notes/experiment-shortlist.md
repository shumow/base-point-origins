# Experiment shortlist: next things to run on the base points

*Written 2026-10-21. A ranked shortlist of the experiments still worth running
against the base-point provenance problem, with time estimates and how much to
trust each estimate. Scope: recovering how the generators were made, not
attacking the curves. Background in [`plan.md`](plan.md),
[`hash-angle.md`](hash-angle.md), [`md-mitm.md`](md-mitm.md), and the GPU
backlog in [`../GPU-Experiments-ToDo.md`](../GPU-Experiments-ToDo.md).*

## How to read the estimates

Each experiment carries two separate times and a certainty rating:

- **Build effort** — focused, agent-assisted engineering to get it running and
  test-first-correct (plant-and-recover controls green before any null result
  is trusted). Expressed in working hours/days, not wall-clock calendar time.
- **Compute/run** — how long the thing takes to execute once built, on a
  capable Apple Silicon laptop (Metal GPU, unified memory).
- **Certainty** — High / Medium / Low, describing confidence in the *time
  estimate itself*, with the reason. It is **not** the chance of finding a hit.

A critical caveat repeated from the research notes: **time-to-run is not
probability-of-success.** Several of these can run to completion and find
nothing, and that is still a useful, publishable negative if the candidate
space was frozen and the controls passed. Where the odds of a hit are
especially low or especially worth it, that is flagged separately.

## Summary

| # | Experiment | Build effort | Compute/run | Estimate certainty |
|---|---|---|---|---|
| 1 | Nothing-up-my-sleeve / structured non-semantic corpus | 2–4 hours | seconds–minutes | **High** |
| 2 | Top-byte and expansion stories (analytic) | 0.5–1 day | instant | **High** (run), Medium (build) |
| 3 | Real Metal benchmark + graduated mask ladder | 1–2 hours to pilot | see note | **High** (pilot), Low (full masks) |
| 4 | On-device LLM candidate generation (V2) | 0.5–1 day | minutes–hours | **Medium** |
| 5 | K-163 MD4/MD5 meet-in-the-middle solver | 1–2 days | highly variable | **Low** |

Recommended order is the table order: the cheap, high-signal analytic and
curated runs first (1–2), the measurement that unlocks everything else (3),
then the two substantial builds (4–5).

## 1. Nothing-up-my-sleeve / structured non-semantic corpus

**Bounded pass completed (24 Oct 2026), negative.** Selectively integrated from
`claude/determined-ride-l5ppv0`, with corrected accounting and corpus labels.
[`nothing_up_my_sleeve.py`](../scripts/nothing_up_my_sleeve.py) freezes 20 direct
hex sources and 66 hash inputs: fractional digits of seven math constants,
hash IVs/round constants, selected curve parameters/seeds, targets themselves
and six markers. Standards values use raw bytes and lower/upper hex ASCII;
math constants use 40/64 hex characters and 20 raw bytes. No decimal-ASCII
encoding is included. The MD5 word-order IV and its little-endian-byte form
are distinct (the branch accidentally duplicated the latter).

Results: [`nothing-up-my-sleeve.json`](../results/nothing-up-my-sleeve.json)
and [text](../results/nothing-up-my-sleeve.txt). **4,290 secp evaluations**
(66 inputs × five algorithms × thirteen suffix variants), and **594 K-163
evaluations** (nine algorithms, **unsuffixed only**); no hits. One evaluation
means one configured hash-function invocation, not one candidate or reading.
The manifest retains algorithms, suffixes, readings, input/source checksums
and target definitions. The secp matcher deliberately uses the broader legacy
148-bit mask (bits 4–151); the actual common block is 152 bits (bits 4–155).
Direct coverage is hex-substring search, as-is or with **hex characters**
reversed, excluding the two as-is self-identities; it does not test modular
reduction or byte reversal. Controls and exact-count regressions are in
[`test_nothing_up_my_sleeve.py`](../tests/test_nothing_up_my_sleeve.py).
This is not all possible famous values or all encodings: the broader proposal
below remains a source of corpus extensions, not completed coverage.

**What.** Test whether the secp\*k1 core or the K-163 value is the hash, or a
simple function, of a *famous* value rather than a human sentence: digits of pi
and e, the SHA-1 and MD5 initialization vectors, other curves' parameters and
SEC SEEDs (including the r-curve SEEDs that embed the ASCII "Minghua Qu"), the
field primes, prior digests, X9.62/X9.63 worked-example values, and small
counters. Feed the curated list through the existing matchers
(`scripts/secg_core_search.py`, `scripts/wordlist_search.py`).

**Why interesting.** It covers the hypothesis class that neither dictionaries
nor masks reach, and the notes explicitly allow that the input may be
non-semantic. A hit here would essentially be the whole answer.

- **Build effort:** 2–4 hours. Only the corpus is new; the matchers exist.
- **Compute/run:** seconds to a few minutes. The corpus is small.
- **Certainty: High.** Both numbers are driven by a small, known candidate set
  running through code that already works and is already benchmarked.

## 2. Top-byte and expansion stories (analytic)

**Current coverage, not a universal exclusion.** Main already has the
152-bit structural analysis and the bounded counter/second-hash/two-stage
models; see [`record.md`](record.md) §7.3.7–7.3.10. The overlapping branch
`top_byte_analysis.py` and its results were not imported: they used the older
148-bit decomposition and overstated the exclusions. Its additional observed
coordinate reduction check is now in
[`high_bytes_analysis.py`](../scripts/high_bytes_analysis.py) §8, with planted
controls in [`test_high_bytes.py`](../tests/test_high_bytes.py).
Only the four observed full x values and their low-160 forms are reduced
modulo each other curve's prime: no nonzero-quotient match, only the known
224k1/256k1 identity. This does **not** exclude an arbitrary common
pre-reduction integer, other counter recipes or expansion schemes.

**What.** The `48` vs `78` disagreement on the 160-bit curve and the shared
`3b78` on the larger curves are the sharpest structural clues (`plan.md` items
3–4). For each model — a counter, a second digest, the X9.62 seed-to-field
expansion, or reduction modulo a different prime — check whether it reproduces
the observed high bits across all four k1 curves at once. Also compute the
half-generators of the other SEC and ANSI curves and hunt for more shared
prefixes like the 92-bit secp160r1/r2 overlap.

**Why interesting.** It is pure arithmetic with no search, and it decides how to
even *frame* the hash search. It can falsify the "assembled as prefix‖digest"
model cheaply, which changes what every other experiment should target.

- **Build effort:** 0.5–1 day. Several small, independent checks plus the
  other-curve half-generator computation (reuse the existing curve code).
- **Compute/run:** effectively instant — no enumeration.
- **Certainty: High on run** (it is arithmetic, not search), **Medium on
  build** — the number of model variants to code is a judgment call and could
  grow if early results are suggestive.

## 3. Real Metal benchmark + graduated mask ladder

**What.** Everything mask-related is gated on GPU-01, and the Apple GPU's
sustained SHA-1/MD5 rate is genuinely unknown (prior runs were an A18 Pro and an
Intel Iris Xe). Measure it with `hashcat -b`, separating kernel compilation from
sustained hashing, then walk the cheapest-first mask ladder in
`GPU-Experiments-ToDo.md`.

**Why interesting.** It converts the hypothetical time columns in the backlog
into a real schedule for this specific machine, and it is the prerequisite the
backlog names before any large exhaustive mask run.

- **Build effort:** 1–2 hours. Mostly adapting the hashcat invocation for macOS
  Metal (exclude OpenCL, per `hash-angle.md` §5); the target lists and controls
  already exist.
- **Compute/run:** the benchmark is seconds; a pilot dictionary pass is minutes.
  The large masks are the day-to-month figures already tabulated — length-8
  printable ASCII is ~37 h at an RTX-4090-class rate and far longer on a laptop
  GPU, so those stay gated on an explicit budget decision.
- **Certainty: High for the benchmark and pilot. Low for the full masks** — the
  big-mask wall-clock depends entirely on the measured rate this step produces,
  which is the unknown it exists to resolve.

## 4. On-device LLM candidate generation (V2)

**What.** Operationalize V2 from `hash-angle.md`: run a local model (MLX or
llama.cpp on Metal) to generate ranked, historically grounded candidates from
the 1997–2000 Waterloo/Certicom/SEC context — names, titles, in-jokes, draft
lines, test strings — freeze each corpus for reproducibility, then hash them
through the existing matchers.

**Why interesting.** V2 is still only an idea, and the MacBook is the natural
machine for it. The motivation is concrete: the SEC 2 r-curve SEEDs embed
"Minghua Qu", so these people demonstrably put names into constants.

- **Build effort:** 0.5–1 day. Set up the local model, write the generation
  prompts, and wire generate → freeze → match. The matching half already exists.
- **Compute/run:** minutes to a few hours, dominated by model inference. Hashing
  the generated set is fast. Generating 10^5–10^6 candidates is the variable.
- **Certainty: Medium.** The build is routine but model setup and prompt
  iteration are easy to under- or over-estimate, and run time scales with how
  many candidates you decide to generate. Success odds are a separate, lower
  bet: it only helps if the input was a phrase someone can plausibly reconstruct.

## 5. K-163 MD4/MD5 meet-in-the-middle solver

**What.** Build the solver designed in `md-mitm.md`: a single-block preimage
attack on the 126-bit K-163 value under MD4/MD5, using the known padding to run
the digest backward through the known tail and meet a forward pass in the
middle, solving the few unknown message words instead of hashing all
completions blind. Test-first is mandatory.

**Why interesting.** It is the only idea that exploits hash structure rather
than brute force, and it does not exist yet. MD4/MD5 have no message expansion,
so the known padding words stay known — the handle SHA-1 did not give cleanly.

- **Build effort:** 1–2 days. Step-level MD4/MD5 forward and backward functions,
  the meet-in-the-middle join, the plant-and-recover control, and tabulating the
  real free-tail depth per candidate length (a listed deliverable, not to be
  asserted).
- **Compute/run:** highly variable and length-dependent. For very short inputs
  (roughly ≤5 ASCII bytes, ≤40 unknown bits) it is tractable in minutes to
  hours. For length 8 the unknown words are ~64 bits and MD5's round-2-to-4 word
  reuse blocks a clean split, so a full meet-in-the-middle is not feasible on a
  laptop — there the value is the few-step free peel plus a per-candidate filter,
  as `md-mitm.md`'s "honest limit" states, best run *over a dictionary* rather
  than blind.
- **Certainty: Low.** The build estimate is itself uncertain because correctness
  demands (test vectors, the free-tail tabulation) can expand it, and the useful
  run coverage depends on facts about the real message schedules that the build
  is what tabulates. This is the highest-variance item on the list.

## One honest framing for all of these

The notes repeatedly warn against overselling, and it applies here. Items 1–3
are cheap enough to run regardless and could end the search outright or sharpen
it. Items 4–5 are real builds whose payoff is uncertain; do them because the
questions are worth answering, not because a hit is likely. Every run that
finds nothing is only meaningful if its candidate space was frozen first and its
planted controls passed — that discipline, not the raw speed, is what makes a
negative worth recording.
