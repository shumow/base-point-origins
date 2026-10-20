# hashcat run plan and time estimates (deliverable 3 of hash-angle.md §4)

*Written 2026-10-20. The mechanical half of V1 (`hash-angle.md` §3): a plain known-digest
dictionary-and-mask search for the short string whose hash is the secp\*k1 core (SHA-1 family)
or the K-163 value (MD5 family). Sentence-class inputs are V2 and are out of scope here.*

This plan is a schedule: which attack classes to run, in what order, and how long each takes.
It does not restate the cryptography (see §1–§3 of `hash-angle.md`) or the kernel/Metal setup
(see §5). It assumes `make_targets.py` has produced the target lists and that every run carries
`--plant` controls.

## 0. Measure the device first — do not trust the numbers below blind

Every time below is `keyspace / H`, where `H` is this machine's hashcat throughput. `H` varies by
two orders of magnitude across the hardware this project might touch, so **benchmark the actual
device before scheduling anything**:

    hashcat -b -m 100          # raw SHA-1, for the secp core list
    hashcat -b -m 0            # raw MD5, for the K-163 list

Take the `Speed.#*` line as `H_sha1` and `H_md5`. Substitute into the tables. Three reference
points are used below (all for raw SHA-1, mode 100, single device):

| Class | `H_sha1` | source |
|---|---|---|
| Metal laptop/phone (A18 Pro, the §5 machine) | **~1e9 /s** | *placeholder — not yet benchmarked, measure it* |
| Mid consumer discrete GPU | ~1e10 /s | `hash-angle.md` §3 |
| RTX 4090 class | ~5e10 /s | published hashcat benchmarks |

MD5 runs roughly 2–3× faster than SHA-1 on the same device, and the K-163 list has only 4 targets,
so the K-163 pass is never the bottleneck: whatever schedule the secp SHA-1 list can afford, run
the same candidate stream against the K-163 MD5 list too, for free in wall-clock terms.

The §3 claim that the length-8 printable mask (~2^52) is "feasible in hours on one GPU" assumes
roughly a 1e12 /s (1 TH/s) rig — a high-end multi-GPU box, not this laptop. On the A18 Pro
placeholder rate it is **months** (see §3 below). Treat the long masks as the part of the plan
that needs real hardware or a restricted charset; everything else runs on the laptop today.

## 1. Targets, modes, and the probe gate

`make_targets.py targets --plant Certicom Certicom1` writes:

- `targets/secp_core_sha1.txt` — up to 12,288 SHA-1 targets (256 top-byte × 16 last-nibble × 3
  byte-order readings), plus the planted controls. Mode `-m 100`.
- `targets/k163_md5.txt` — 4 MD5 targets (top two bits free), plus controls. Mode `-m 0`.

Target count does **not** multiply runtime: hashcat checks each candidate against the whole list
via its bitmap/hash-table at negligible per-candidate cost, and §5 confirmed the 12,288 secp
targets collapse to ~290 buckets internally. So every time estimate here uses the single-target
benchmark rate `H`.

**Run the probe before trusting any negative result** (`hashcat_probe.py`, `hash-angle.md` §5):

    python3 scripts/make_targets.py targets --plant Certicom Certicom1
    python3 scripts/hashcat_probe.py targets
    hashcat -m 100 -a 0 --potfile-path targets/probe.pot \
        targets/probe_leadingword.txt wordlists/certicom.txt

- **CRACKED** → hashcat ignores the leading digest word. Regenerate targets with the top-byte loop
  dropped (256× smaller list); the search is correctly blind to the unknown top byte.
- **EXHAUSTED** → hashcat confirms the full digest. Keep the 12,288-target list as is.

Either way, in every real run below the planted control (`Certicom`, and the rule-only
`Certicom1`) **must** appear in the potfile. A run that exhausts without cracking the plant is not
a valid negative — it means the dictionary, rules, mask, or kernel did not cover the plant, so fix
that and rerun before recording "no hit".

## 2. Cost model

For a dictionary attack: `candidates = words × rules`, `time = candidates / H`.
For a mask attack: `candidates = Σ charset^len`, dominated by the longest length.
Small keyspaces are **startup-bound**, not compute-bound: kernel autotune plus wordlist/rule load
is a floor of roughly 10–30 s per invocation regardless of how few candidates follow. Anything the
table marks "seconds" means "startup-bound, run it without thinking about cost".

Rule-set sizes used below: `best64.rule` ≈ 77 rules; a "large" rule set (`dive.rule`,
`OneRuleToRuleThemAll.rule`) ≈ 1e5 rules.

## 3. Attack classes, cheapest and most likely first

Times are for the secp SHA-1 list at the three reference rates (laptop 1e9 / consumer 1e10 /
4090 5e10). The K-163 MD5 pass is faster and runs alongside each.

### Tier A — the Certicom-era dictionary (run first, essentially free)

| # | attack | candidates | laptop | consumer | 4090 |
|---|---|---|---|---|---|
| A1 | `certicom.txt` straight (`-a 0`, no `-O`) | 6,939 | seconds | seconds | seconds |
| A2 | `certicom.txt` × `best64` | 5.3e5 | seconds | seconds | seconds |
| A3 | `certicom.txt` × large rule | 6.9e8 | ~1 s | seconds | seconds |
| A4 | `certicom.txt` + digit/date suffix (`-a 6`, `?d?d?d?d`) | 6.9e7 | seconds | seconds | seconds |

Drop `-O` for A1–A4 (the optimized kernel caps candidates at 31 bytes and rejected 148 wordlist
entries in §5; the pure kernel covers all lengths and was faster at this keyspace). This tier is
the highest-prior hypothesis and costs nothing — always run it, and rerun it whenever
`certicom.txt` grows.

### Tier B — general wordlists

| # | attack | candidates | laptop | consumer | 4090 |
|---|---|---|---|---|---|
| B1 | English + name lists straight | ~1e7 | seconds | seconds | seconds |
| B2 | rockyou-class (1.4e7) × `best64` | 1.1e9 | ~1 s | seconds | seconds |
| B3 | rockyou-class × large rule | 1.4e12 | 24 min | 2.4 min | 29 s |
| B4 | large list (1e9) × `best64` | 7.7e10 | 77 s | 8 s | seconds |
| B5 | large list (1e9) × large rule | 1e14 | 28 h | 2.8 h | 33 min |

Wordlists to feed B1: standard English (SCOWL/aspell), first/last-name lists, plus the curve-param
and SEC-draft strings already in `certicom.txt`. B3 is the sweet spot on the laptop; B5 needs real
hardware or an overnight run.

### Tier C — masks (the long pole; needs a fast device or a restricted charset)

| # | mask | keyspace | laptop | consumer | 4090 |
|---|---|---|---|---|---|
| C1 | dates, all formats | ~3e5 | seconds | seconds | seconds |
| C2 | `?l` len ≤ 8 | 2.1e11 | 3.5 min | 21 s | ~4 s |
| C3 | `?l?d` len ≤ 8 | 2.8e12 | 47 min | 4.7 min | 56 s |
| C4 | `?a` len ≤ 7 | 7.0e13 | 19 h | 1.9 h | 23 min |
| C5 | `?a` len 8 (the §3 "~2^52" target) | 6.6e15 | 77 d | 7.7 d | 37 h |
| C6 | `?l?d` len ≤ 10 | 3.7e15 | 42 d | 4.2 d | 20 h |

Use `-O` for all of Tier C (every candidate is short by construction, so the 31-byte cap is
harmless and the optimized kernel is faster). On the laptop, run C1–C4 and stop; C5/C6 are a
discrete-GPU or multi-GPU job, or split the C5 keyspace with `-s`/`-l` across several machines /
sessions. Record exactly which length and charset was actually reached so a later negative is
honest about its bounds.

### Out of scope here

- **Sentence-class inputs (V2).** Masks over multi-word phrases blow up (26^30); covered by the
  language-model candidate generator in `hash-angle.md` §3 V2, not by this plan.
- **K-163 128-bit non-MD5 readings.** Truncated SHA-1 (128 of 160 bits), MD4, and RIPEMD-128 have
  no hashcat partial-match mode (§3), so they stay in the Python harness (`wordlist_search.py`),
  which already runs the same candidate strings through those matchers.

## 4. Recommended schedule

1. Probe gate (§1). Regenerate targets if CRACKED.
2. Tier A, both lists. Minutes total, including the plant check.
3. Tier B1–B3, both lists. Under an hour on the laptop.
4. Tier C1–C3 (and C4 if time allows), both lists. Under an hour on the laptop up to C3.
5. Queue B5 and C4 as an overnight laptop pass, or move the whole of Tier C to a discrete GPU.
6. C5/C6 only on 4090-class hardware, or `-s`/`-l` keyspace-split across sessions.

Every exhausted run that cracked its plant and found nothing narrows the hypothesis; log it (§5)
rather than discarding it.

## 5. Results log format

One JSONL record per hashcat invocation, appended to `results/hashcat/runs.jsonl`. Potfiles go in
`results/hashcat/<run_id>.pot`; keep them, they are the cracked-hash evidence.

Fields:

| field | meaning |
|---|---|
| `run_id` | `YYYYMMDD-NN`, unique per invocation |
| `date` | ISO 8601 timestamp |
| `device` | GPU/backend, e.g. `A18 Pro / Metal` |
| `H_measured` | hashes/s from `hashcat -b` for this mode on this device |
| `mode` | hashcat `-m` (100 = SHA-1, 0 = MD5) |
| `target_file` / `n_targets` | which list and how many digests |
| `attack` | `-a` value (0 dict, 1 combinator, 3 mask, 6/7 hybrid) |
| `wordlist` / `rules` / `mask` | whichever apply, by filename / mask string |
| `keyspace` | candidates actually enumerated |
| `runtime_s` | wall-clock seconds |
| `status` | `cracked` \| `exhausted` \| `aborted` |
| `plant_cracked` | bool — **false invalidates the run** |
| `cracks` | list of `digest:plaintext` for any non-plant hit |
| `cmdline` | exact command, for reproduction |
| `notes` | anything odd (kernel warnings, charset reached, split bounds) |

Example:

    {"run_id":"20261020-01","date":"2026-10-20T19:40:00Z","device":"A18 Pro / Metal",
     "H_measured":1.0e9,"mode":100,"target_file":"targets/secp_core_sha1.txt","n_targets":12290,
     "attack":0,"wordlist":"wordlists/certicom.txt","rules":"best64.rule","mask":null,
     "keyspace":534303,"runtime_s":22,"status":"exhausted","plant_cracked":true,
     "cracks":[],"cmdline":"hashcat -m 100 -a 0 -r rules/best64.rule --potfile-path results/hashcat/20261020-01.pot targets/secp_core_sha1.txt wordlists/certicom.txt",
     "notes":"tier A2; pure kernel (no -O); plant Certicom+Certicom1 both cracked"}

A hit (`cracks` non-empty on a real target) is not the end: hand the plaintext to
`scripts/sha1_steps.py` to reconstruct its full 80-step execution and confirm the top-byte /
last-nibble story (`hash-angle.md` §2a, §3 V1), and check it against the alternate readings before
claiming the base-point origin is recovered.
