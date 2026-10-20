# MD4/MD5 meet-in-the-middle last-block preimage — design and task

*Filed 20 Oct 2026 from a voice conversation with Dan. This is the design for the next build; the solver does not exist
yet. **Test-first is mandatory** (§4): the plant-and-recover control is written and green before the solver is trusted,
and before any null result against the real K-163 value is reported.*

## 1. Why this, why MD-family, why K-163

The K-163 subgroup half-point x is a 126-bit value (`23e21d6019e1211f6bd47ec180256e97`, top two bits zero). A 128-bit
object from the 1997–2000 era is MD4/MD5-shaped. If it is `MD5(s)` or `MD4(s)` for a short string `s`, the known
Merkle–Damgård padding on a single block lets part of the computation run with no candidate at all, which is the handle
SHA-1 did not give us cleanly (SHA-1's message expansion spreads every unknown word across all 80 steps; see §2 of
`hash-angle.md`). MD4/MD5 have **no message expansion** — each 32-bit message word is used at a fixed, small set of
step positions — so the known padding words stay known wherever they appear, and the "run the digest backwards through
the known tail" idea reaches genuinely useful depth.

## 2. The construction (single block, known IV, known padding)

For `s` of length L ≤ 55 bytes the padded block is one 512-bit block of sixteen 32-bit words `W0..W15`:
`W0..W_{k}` hold the message bytes (little-endian for MD4/MD5), then `0x80` and zeros, `W14 = 8L` (low word of the bit
length), `W15 = 0`. For L = 8: `W0,W1` unknown; `W2 = 0x00000080`; `W3..W13 = 0`; `W14 = 64`; `W15 = 0`.

Davies–Meyer: `H_out = E_W(IV) + IV` word-wise, IV the fixed MD4/MD5 constant. For a single block **both ends are
known**: the input chaining value is the IV, and the final working state is `E_W(IV) = H_out − IV`.

Each MD4/MD5 step is a bijection given its message word (recover the fed-back register by rearranging the step
equation; MD5 step `Q_{t+1} = Q_t + ((Q_{t-3} + f + W + AC) <<< s)` inverts to `Q_{t-3} = ((Q_{t+1} − Q_t) >>> s) − f −
AC − W`). So:
- **Backward** from the final state `H_out − IV`, invert steps using only *known* (padding) words until the first
  unknown word is needed. That reconstructs several internal states for free.
- **Forward** from the IV, apply steps using the known low words; the unknown words `W0..W_{k}` enter at their first
  (round-1) positions.
- **Meet in the middle:** the two partial computations must agree on the full internal state at the split step. That
  constraint on the few unknown words is solved/enumerated, rather than hashing all `2^{32·(k+1)}` completions blind.

**Honest limit (state it in the write-up, do not oversell).** Because MD4/MD5 use every message word in round 1, the
strictly candidate-free backward tail is only a few steps for a short string — the leverage is the MITM constraint
cutting the forward enumeration plus a cheap per-candidate consistency filter, not a long free peel. MD4 (48 steps)
is friendlier than MD5 (64 steps). The exact free-tail depth per candidate length must be **tabulated from the real
message schedules** (deliverable 2), not asserted.

## 3. Deliverables

1. `scripts/md_steps.py` — MD4 and MD5 with forward *and* backward single-step functions, self-tested against published
   test vectors forward and against `hashlib` where available; backward(forward(state)) == state over random states.
   Model it on `scripts/sha1_steps.py`.
2. `scripts/md_schedule.py` (or a table in this note) — for each algorithm and each candidate length L = 1..20, the
   message-word-to-step map read backward from the last step, giving the number of leading steps that use only padding
   words (the free-tail depth) and which `W` indices are unknown. This tabulation is the thing that says how much the
   method buys per length; produce it before building the solver.
3. `scripts/md_mitm.py` — the solver: fix algorithm and L, split at the step the table identifies, enumerate the unknown
   words consistent with both partial computations, return any `s` with `MD*(s) == target` (reduced to the 126-bit K-163
   value with the top two bits free, and also the four full 128-bit completions).
4. Results + a short write-up here of what was searched and found, in the repo's usual register.

## 4. Test-first (write these before §3.3)

`tests/test_md_mitm.py`, stdlib `unittest`, plant-and-recover:
- Pick a known short string per length (e.g. `b"Jerry"`, `b"Bob"`, `b"Solinas!"`), compute its real MD4/MD5, hand the
  digest to the solver, assert it returns that string (or a string with the same digest). One case per length 3..12,
  both algorithms.
- Negative control: a digest with no short preimage (e.g. a random 16-byte value) returns nothing within the length
  bound.
- The step modules: forward against published vectors; backward∘forward == identity; and for the masked K-163 form,
  that a planted `MD5(s) & (2^126−1)` is recovered through the real top-two-bits-free matcher.
Only once these are green does a null result against the real K-163 value mean anything — same discipline as
`tests/test_recovery.py`.

## 5. Relation to the rest

This is the V1/V2 hash angle (`hash-angle.md`) specialised to the 128-bit K-163 value, where the MD-family no-expansion
property makes the forward/backward machinery (Stevens 2013 / Stevens–Shumow 2017, `references/`) actually bite. It does
not replace the GPU dictionary/mask run for the 160-bit secp core; it is the targeted analytic attack on the one
constant whose size points at MD4/MD5.
