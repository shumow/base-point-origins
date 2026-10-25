# Agent guidance

## Mission and scope

This repository investigates the historical provenance of standardized elliptic
curve base points. Structural observations are not attacks, evidence of a
weakness, or recovered generation recipes.

- Start with [README.md](README.md) for navigation and execution instructions.
  Read the relevant parts of [HANDOFF.md](HANDOFF.md) and
  [notes/record.md](notes/record.md) before changing research claims.
- Follow [CONTRIBUTING.md](CONTRIBUTING.md) for planning, evidence and validation.
  [notes/engineering-plan.md](notes/engineering-plan.md) tracks engineering
  hygiene, not the research hypothesis backlog.
- Do not read SNFS/GNFS witness/investigation documents for this project.
  Do not ingest private correspondence or publish private material without
  explicit authorization for the specific material.

## Work safely

- Check the branch and worktree first; this checkout may be shared with other
  sessions. Preserve unrelated edits. Never discard work or rewrite published
  history to make a task easier.
- Keep changes scoped. Reuse existing arithmetic, matchers and manifest helpers.
  Do not create parallel implementations or duplicate instruction files.
- Use standard-library Python and the existing test tools unless a dependency
  is justified. Keep `.tools/`, `runs/`, caches and downloaded binaries out of
  commits.
- State what was changed, verified, skipped, committed and pushed separately.
  A plan, tool invocation or successful smoke test is not a completed experiment.

## Evidence before conclusions

- A search needs planted or known positive controls through the actual search
  path before its negative result is trusted.
- Report the exact corpus, encodings, targets, algorithms, suffixes, readings
  and evaluation counts. Candidates, hash invocations and reading/window checks
  are different quantities. Time-limited is not exhausted.
- Label facts, reported history, heuristics and hypotheses separately. Bound
  every exclusion to what the code actually tests.
- The shared secp*k1 block is **152 bits, bits 4..155**. The existing
  `secg_core_search.py` deliberately tests a broader **148-bit** projection,
  bits 4..151; do not silently change that coverage or call it the entire block.
- Use K-163's corrected polynomial-basis x(G/2),
  `23e21d6019e1211f6bd47ec180256e97`. Subgroup division is not the full
  cofactor-preimage set.
- Regenerate affected recorded results from the changed code. Retain input and
  source checksums and byte-exact hit witnesses; never hand-edit a computed
  result to fit an expected conclusion.

## Execution boundaries

- On this Windows setup, use native Windows Python for `scripts\local.py`.
  CPU/PARI validation runs in restricted local WSL Docker; native Windows
  hashcat runs **outside** that sandbox.
- Prefer focused controls first, then `python scripts\local.py test` for
  cross-cutting or arithmetic changes. Report skips and missing prerequisites;
  do not substitute a narrower suite silently.
- Do not launch heavy GPU campaigns without explicit scope and compute budget.
  Follow [GPU-Experiments-ToDo.md](GPU-Experiments-ToDo.md).
- Preserve GPU full-digest post-verification, `--keep-guessing`, newline
  normalization and planted controls. Hashcat partial matches and recovery
  counters alone are not research hits.
