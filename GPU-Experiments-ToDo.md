# Outstanding GPU experiments

Status: 20 October 2026. Scope: recovering the provenance of elliptic-curve
base points, not attacking keys or finding a weakness in the curves.

This is the remaining heavy-workload backlog after bringing up the local
Windows/WSL workflow. Unchecked items have **not** been completed. Recording
them here does not start or authorize a long-running search.

## Already completed; do not confuse these with the large searches

- [x] Native Windows hashcat 7.1.2 installed from a signature-verified archive;
  Intel Iris Xe detected through OpenCL.
- [x] Local WSL Docker sandbox built; effective isolation verified. After
  reconciling upstream CLI changes, all 53 tests pass, including the upstream
  SEC suite and independent PARI checks.
- [x] Actual GPU recovery of the bare and rule-generated positive controls
  under both SHA-1 and MD5.
- [x] Small Certicom dictionary pass with identity and append-`1` rules:
  13,880 candidate evaluations per algorithm, exhausted, no research hits.
  This is **not** a large rules, general-wordlist, mask, or phrase campaign.
- [x] SHA-1 target deduplication reproduced on the GPU; full-target verification
  and rejection of partial matches validated.

Local evidence: [reference run report](runs/20261020T164016Z-search-96e020e7/run.json).
That report and its inputs/logs are gitignored and are not part of a fresh clone.
Earlier CPU dictionary passes are recorded in [HANDOFF.md](HANDOFF.md) and the
[computational record](notes/record.md); they are not GPU coverage of an
arbitrarily expanded candidate space.

## Targets and execution constraints

- **secp*k1:** match bits 4..151, with bit 0 the least significant bit, against
  `ce563f89a0ed9414f5aa28ad0d96d6795f9c6`. The existing list enumerates the
  unknown top byte and last nibble in three readings: unchanged bytes, reversed
  bytes, and bytes reversed within each 32-bit word. This gives 12,288 targets,
  or 12,290 with the current two controls.
- **K-163:** corrected polynomial-basis coordinate
  `23e21d6019e1211f6bd47ec180256e97`. The existing MD5 list has four top-two-bit
  completions, or six targets with controls. It does not yet include reversed
  or word-swapped MD5 readings.
- On hashcat 7.1.2, SHA-1 mode 100 compares words 1..4, not all five words.
  The 12,290 input lines collapse to 290 comparison keys. Keep
  `--keep-guessing`, rehash returned plaintext bytes, and test the computed
  digest against the **full** target set. A representative's printed hash or
  a partial GPU match is not a 148-bit research hit.
- [The local runner](scripts/local.py) currently supports dictionary/rule
  passes for raw SHA-1 and MD5. It does **not** implement masks, combinator
  attacks, truncated-hash searches, or other hash families.
- Python preparation/tests run inside the restricted local WSL container.
  Hashcat uses the Windows GPU **outside** that container.

## Prioritized backlog

**Run order.** Before trusting any negative, run the leading-word probe
(`scripts/hashcat_probe.py`) and regenerate targets if it shows the top-byte
enumeration is unnecessary. Every pass carries the `Certicom`/`Certicom1`
controls and is void unless both crack in the same pass. Then work
cheapest-first: the Certicom dictionary with identity/append-`1` and `best64`
(GPU-02, startup-bound to seconds), larger wordlists with bounded rule
expansions (GPU-03, seconds to minutes), constrained date/counter and short
alphanumeric masks (GPU-04), and only after GPU-01's measured budget the
length-8 printable and length-10 alphanumeric masks. `scripts/local.py` runs the
dictionary/rule tiers end to end; masks are explicit hashcat commands that must
reproduce the same controls, full-target verification, and `run.json` logging.

### GPU-01: Measure representative sustained throughput

- [ ] Benchmark both algorithms against the actual research target lists and
  candidate-generation methods, rather than projecting from a single-hash
  benchmark or the tiny smoke run.
- [ ] Separate initialization/kernel compilation from sustained hashing.
  Measure dictionary/rules and masks separately, with the intended byte
  encodings and lengths.
- [ ] Start with workload profile 1 and short pilots. Record thermal behavior,
  responsiveness, actual GPU/backend, accepted/rejected candidates, and rates.
- [ ] Compare optimized kernels only in an explicitly length-bounded pass
  with positive controls; do not silently lose longer candidates.

**Exit criterion:** measured rates and a wall-clock/thermal budget for each
proposed larger pass. No large exhaustive mask run before this step.

### GPU-02: Expand the Certicom dictionary with real rule sets

- [ ] Run a bounded `best64.rule` pass over the existing
  [Certicom dictionary](wordlists/certicom.txt), then consider larger rule sets
  only after estimating their candidate counts.
- [ ] Cover case changes, punctuation, spacing, numeric suffixes, dates,
  substitutions, and era-appropriate name/organization variants.
- [ ] Record the exact rule file and dictionary hashes. Separate exhausted
  passes from runtime-limited attempts; avoid repeatedly reporting the same
  candidate space as new coverage.

**Ready now:** dictionary/rule passes can use the existing local runner, which
adds its control word and identity/append-`1` rules.

### GPU-03: Larger dictionaries, names, and structured phrases

- [ ] Add public English-word and name lists, expanded historical Certicom/
  Waterloo/SECG material, and documented 1997-2000 terminology. Record sources,
  licenses, normalization, and deduplication.
- [ ] Run the larger lists through the validated SHA-1 and MD5 paths, with
  bounded rule expansions before broad combinatorial combinations.
- [ ] Test bounded two-to-five-word templates and the V2 idea of ranked,
  historically plausible phrases. Freeze each generated corpus before hashing
  so that a negative result has an exact, reproducible meaning.
- [ ] Treat phrase generation as candidate selection, not a cryptanalytic
  shortcut. Separate messages of at most 55 bytes from longer messages when
  testing the single-block hypothesis; do not silently discard the latter.

**Prerequisite:** combinator/hybrid generation needs explicit commands or
runner support plus controls through the actual generation path.

### GPU-04: Graduated mask and hybrid campaigns

- [ ] First test constrained numeric/date/counter masks and dictionary-plus-
  suffix/prefix hybrids. Prefer historically motivated structure to a blanket
  printable-character search.
- [ ] Widen short alphanumeric masks by length, with separately resumable,
  recorded shards.
- [ ] Consider all printable ASCII through length 8 and lowercase-plus-digits
  through length 10 only after GPU-01 and an explicit time-budget decision.
- [ ] Add mask-compatible planted controls for every charset/length family.
  The current `Certicom`/`Certicom1` controls do not fit arbitrary masks.
- [ ] Preserve full-target post-verification, partial-match handling,
  `--keep-guessing` for SHA-1, and per-run logs/checkpoints in the mask workflow.

**Not implemented by the current runner.** A raw hashcat mask invocation alone
does not provide the existing workflow's controls and verification.

These broad spaces are not automatically "hours on a laptop". The mask ladder
below, cheapest first, shows why GPU-01's measurement gates the large runs:

| Candidate space | Candidates, all stated lengths | at 1e9/s | at 1e10/s | at 5e10/s |
|---|---:|---:|---:|---:|
| 26 lowercase, lengths 1..8 | 217,180,147,158 | 3.6 min | 22 s | 4 s |
| 36 lowercase/digit, lengths 1..8 | 2,901,713,047,668 | 48 min | 4.8 min | 58 s |
| 95 printable ASCII, lengths 1..7 | 70,576,641,626,495 | 19.6 h | 2.0 h | 24 min |
| 95 printable ASCII, lengths 1..8 | 6,704,780,954,517,120 | 77.6 days | 7.8 days | 37 h |
| 36 lowercase/digit, lengths 1..10 | 3,760,620,109,779,060 | 43.5 days | 4.4 days | 21 h |

The three rates are hypothetical reference points, **not measurements of the
Iris Xe**: 1e9/s a conservative integrated-GPU guess, 1e10/s a strong discrete
GPU, 5e10/s an RTX 4090 class card. The §3 "hours" framing in
[`notes/hash-angle.md`](notes/hash-angle.md) assumed roughly a 1e12/s rig, which
this laptop is not. Each row is for one algorithm before extra encodings, hash
constructions, or input transforms. Replace these columns with GPU-01's measured
Iris Xe rate and schedule from `candidate_count / measured_rate`.

Dictionary and rule passes (GPU-02, GPU-03) are not in this table: at these
keyspaces they are startup-bound (kernel autotune and list load), seconds to a
few minutes, so they run first regardless of rate.

### GPU-05: Expand byte encodings, counters, and output readings

- [ ] Apply the large candidate corpora to the CPU harness's ASCII,
  UTF-16-LE/BE, punctuation, terminator, and counter constructions. Include
  byte-exact NUL and binary counter cases, not just printable text lookalikes.
- [ ] Preserve the tested suffix definitions: no suffix, and counters 0..3
  as one byte, decimal text, and four-byte big-endian integers. Any wider
  counter range is a separately recorded hypothesis.
- [ ] Add reversed-byte and per-32-bit-word-byte-reversed K-163 MD5 target
  readings, with planted controls for each. The existing four MD5 targets
  only cover the unchanged reading and its top-bit variants.
- [ ] Cross-check generated bytes, byte order, masks, and representative
  recoveries against the existing CPU matchers before scaling.

**Prerequisite:** byte-exact input/target preparation and coverage metadata;
an ordinary ASCII dictionary run is not equivalent to the CPU variant sweep.

### GPU-06: K-163 truncated SHA-1 searches

- [ ] Define and test high/low 128-bit and high/low 126-bit hypotheses,
  including the precise bit masking and byte-order conventions.
- [ ] Investigate using mode 100's observed comparison of SHA-1 words 1..4
  as a low-128-bit prefilter, with a dedicated verifier and controls.
  The current full-target verifier intentionally does not implement this
  different acceptance condition.
- [ ] For high-128-bit and other masks, implement or select an exactly
  compatible GPU matcher; a custom OpenCL kernel may be required.
- [ ] Differentially test any new matcher against CPU results and planted
  hits, including wrong-bit and wrong-endianness near misses, before searching.

**Blocked on tooling.** Do not enumerate all `2^32` missing SHA-1 bits, or treat
mode 100's ignored first word as proof that every truncation is supported.

### GPU-07: Other historical hashes and composed constructions

- [ ] Port the expanded corpus to SHA-0 and RIPEMD-160 for the secp core, and
  MD4/RIPEMD-128 for K-163, after validating available kernels/modes.
- [ ] Cover the CPU harness's composed hashes, including SHA-1 of raw SHA-1
  or MD5 digest bytes, and MD5 of raw or hexadecimal MD5 output.
- [ ] Specify raw digest versus hex text, hex case, input encoding, output
  reading, and mask separately. A similarly named hashcat mode is not enough
  without known vectors and end-to-end planted recovery.

**Prerequisite:** compatible modes/kernels and acceptance checks. The current
local SHA-1/MD5 runner does not cover these constructions.

## Completion and reporting rules

For every heavy pass, save the exact command, hardware/driver/hashcat versions,
target/input/rule hashes, candidate-generation definition, shard or restore
position, runtime limit, actual progress, rejected candidates, control
recoveries, full-match verification, partial matches, and exit status.
`scripts/local.py` already records these in each run's `run.json` for
dictionary/rule passes; a manual mask or hybrid run must emit the same fields,
in its own `run.json` or equivalent, so its negative is reproducible.

- A pass is negative only for its precisely specified, exhausted space after
  its controls pass. Runtime limits, interruption, missing controls, or
  unsupported/rejected candidate lengths do not establish full coverage.
- Hashcat exit 4 means time-limited/incomplete. SHA-1 `--keep-guessing` can
  leave the terminal's recovered counter at zero even when recovery files
  contain hits; use verified plaintexts, not that counter, as evidence.
- Reserve GPU time deliberately on this shared-use laptop. Keep conservative
  workload settings until measured otherwise; do not use `--force`, silent
  CPU fallback, automatic large follow-on searches, or unbudgeted background
  runs. Stop or pause if thermal behavior or responsiveness is unacceptable.
- A matching digest is a provenance lead, not yet a complete generator recipe.
  Reconstruct the input bytes, output reading, high-prefix/tail adjustments,
  point lifting, and doubling against the published generators.

Archival research, expanded curve scans, large RNG-seed sweeps, and explaining
the secp160r shared prefix remain separate investigation items, not GPU jobs
already implemented or scheduled by this checklist. Reversible SHA-1 steps do
not currently provide a demonstrated shortcut around candidate enumeration.

Sources: [local execution instructions](README.md#running-locally-on-windows-with-wsl),
[V1/V2 hash-search plan](notes/hash-angle.md),
[research handoff](HANDOFF.md), and [broader provenance plan](notes/plan.md).
