# Where did the base points come from?

*A historical investigation of the generators of the standard elliptic curves — NIST FIPS 186, ANSI X9.62, SEC 2. Spun out of [ECDSA-Origins-Revealed-Followup](https://github.com/shumow/ECDSA-Origins-Revealed-Followup) on 20 October 2026, which stays focused on the skipped-seed question.*

## The framing

Nothing here is an attack, and nothing here suggests one. Anthropic's October 2026 result settled the curve *seeds*: `lrand48()` from the Unix clock, candidates drawn in order, no hash of anybody's sentence. The *base points* are the piece that is still unexplained for fourteen of the twenty NIST/ANSI curves — P-224, P-256, P-384, P-521, the five B curves and the five K curves — and for every SEC 2 curve beyond those. And the structure we can see in them is of a specific kind:

- secp224k1 and secp256k1 have the **identical** 166-bit *x*-coordinate at *G*/2: `3b78ce563f89a0ed9414f5aa28ad0d96d6795f9c63`.
- secp160k1 and secp192k1 carry the same 148-bit core with different top bits and last nibbles (`48ce563f…9c62`, `554123b78ce563f…9c66`).
- *x*(*G*/2) on secp160r2 shares its first 92 bits with *x*(*G*) on secp160r1.
- The half of the K-163 generator has a 126-bit *x*: `23e21d6019e1211f6bd47ec180256e97`.

These are not the fingerprints of a designer hiding a weakness; it is hard to even sketch an attack that would use a shared public *x*-coordinate. They look like what programmers and mathematicians leave behind when nobody is watching: a convenience constant reused across fields, a test value never replaced, an Easter egg. That is the historical observation, and it is reason enough to keep digging. The seeds went from lore to fact in a day once someone found the recipe. The generators are the last large piece of the standard parameter set with no account of their origin, and they now carry structure that says there is an account to be found.

The secp\*k1 observation was first made in the Heninger–Scholl–Shumow Crypto 2019 rump-session talk, whose title is *x*(*G*/2) on secp160k1.

## What is here

| | |
|---|---|
| [`HANDOFF.md`](HANDOFF.md) | **start here** — everything known, everything tried, what to do next |
| [`notes/plan.md`](notes/plan.md) | the hypotheses and the six-step search plan, with the steps already run marked |
| [`notes/record.md`](notes/record.md) | the full record of what has been computed so far (small-multiple scans, K-163, the SEC 2 curves) |
| [`notes/base-point-brief.md`](notes/base-point-brief.md) | the earlier hand-off brief |
| [`scripts/`](scripts/) | `secg_scan.py` (SEC 2 prime curves), `binpts.py`/`.gp` (NIST binary curves), `k163/` (hash-preimage harness), `secg_core_search.py` (core-matched search) |
| [`results/`](results/) | every number behind the statements above |
| [`tests/`](tests/) | positive controls: every search here must recover a planted or known answer (`python3 -m unittest discover -s tests`) |
| [`wordlists/`](wordlists/), `scripts/make_targets.py` | the hashcat side of the search: Certicom-era dictionary and the 12,288-target list |
| [`GPU-Experiments-ToDo.md`](GPU-Experiments-ToDo.md) | outstanding heavy GPU experiments, tooling prerequisites, budgets, and completion criteria |

## Status (20 October 2026)

Everything run so far is negative, and each negative is now backed by a positive control in `tests/`:

- No acceptance rule among ~11,500 tried selects the per-curve last nibbles 2, 6, 3, 3.
- The 148-bit core is not the SHA-1 / SHA-0 / RIPEMD-160 (or doubled-hash) digest of any of ~290,000 NIST-era and Certicom-era strings in their case / punctuation / encoding / counter variants — three independent passes, ~70 million evaluations in all. The K-163 value is not the MD5 / MD4 / RIPEMD-128 (or truncated SHA-1) digest of any of them either.
- The FreeLIP `zrandom` recipe that produced P-192's base point does not produce P-224/256/384/521's or secp160k1's for any seed below 100,000.
- The 192k1 value is the 224/256k1 value with `55412` written in above bit 172 and the last nibble raised by 3; the X9.62 seed-to-field expansion is excluded.

The next step is **V1** of [`notes/hash-angle.md`](notes/hash-angle.md): the same search as a GPU dictionary-and-mask attack with hashcat against the 12,288-target list, which reaches candidate spaces (all printable ASCII to length 8, rule-expanded dictionaries) that pure-Python passes cannot. We are experimenting on laptop-class GPUs. **If you have GPU time and would like to run this, we'd be happy to talk** — open an issue or get in touch.

## Running locally on Windows with WSL

[`scripts/local.py`](scripts/local.py) uses **native Windows hashcat for the GPU**
and **Docker inside local WSL for Python/PARI**. It does not use a remote runner.
Windows GPU access avoids requiring a separate Intel OpenCL runtime inside WSL.
Hashcat itself runs on the Windows host, **not inside the container sandbox**.

Prerequisites:

- Native Windows Python 3.10 or newer (`python --version`).
- WSL 2, an Ubuntu distribution, and a working Docker daemon in that distribution.
- A Windows GPU compute driver and the official portable
  [hashcat release](https://hashcat.net/hashcat/). Extract the complete archive to
  `.tools\hashcat-7.1.2`, or pass `--hashcat C:\path\to\hashcat.exe`.
  Verify the detached signature against the signing-key fingerprint published on
  the hashcat download page before running downloaded binaries.

From the repository root in PowerShell:

```powershell
python scripts\local.py build
python scripts\local.py test
python scripts\local.py gpu-info
python scripts\local.py smoke
```

`build` uses the local WSL host network to download the Python image and PARI/GP
over HTTPS, with bounded package-manager retries. Later container runs have no
external network, a read-only root and source checkout, no Linux capabilities,
no privilege escalation, a non-root user, two CPUs, 2 GiB RAM with no additional
swap, and 512 MiB temporary storage. Only the specific run's output directory
is mounted writable. The Docker socket, Windows home directory, and GPU are
not mounted into the container. `test` checks the effective isolation before
running the existing and local-runner tests.
The test command also includes the upstream SEC validation suite and its
independent PARI checks; planted core-search controls validate the CLI's JSON
manifest rather than its older console format.

`gpu-info` must report a GPU backend. If its device ID is not 1, use, for example,
`python scripts\local.py --device 2 smoke`. GPU commands require GPU devices
(`-D 2`); they do not silently fall back to the CPU or use `--force`.

`smoke` runs a tiny dictionary through the actual 12,288 SHA-1 and four MD5
research targets, plus two planted controls for each algorithm. One control
needs the append-`1` rule. Both must be recovered in the same pass and their
digests are independently checked in Python; controls are never discoveries.

**SHA-1 comparison detail:** hashcat mode 100 compares only four of the five
SHA-1 words. On hashcat 7.1.2 the 12,290 input lines therefore collapse to 290
GPU comparison keys, and the reported hash can have a representative's first
word rather than the candidate's actual first word. The runner rehashes each
recovered candidate and checks membership in the **full target list**, preserving
the required 148-bit match. Partial GPU matches are recorded and rejected, and
`--keep-guessing` prevents one from suppressing a later full match.

To run a bounded dictionary search after the smoke test:

```powershell
python scripts\local.py search --seconds 60
python scripts\local.py search --seconds 300 --wordlist C:\data\words.txt --rules C:\tools\hashcat\rules\best64.rule
```

The default dictionary is `wordlists\certicom.txt`. Identity and append-`1`
rules and a bare control word are added to every search, including custom
rule sets. Each algorithm has its own time budget; initialization and kernel
compilation are additional, and workload profile 1 keeps the machine more
responsive. This runner handles dictionary/rule passes; large mask searches
remain explicit hashcat commands, not an automatic next step.

Every GPU run gets a new ignored `runs\...` directory containing target lists,
the exact dictionary/rules, logs, potfiles, restore state when hashcat writes
it, and `run.json` with input hashes, container image ID, commands, timings,
verified controls, and real hits. Hashcat exit 1 means the configured pass was
exhausted, not a tool failure. Exit 4 is preserved as a time-limited,
**incomplete** search, never a negative result; other errors or missing controls
fail explicitly. `prepare` generates the same inputs without starting the GPU.
`--distro` selects another local WSL distribution. Downloads in `.tools` and
outputs in `runs` are not committed.

## Who

Dan Shumow. Computation and drafting with Claude (Anthropic). Thanks to Nadia Heninger and Travis Scholl.

Code CC0 1.0; text CC BY 4.0.
