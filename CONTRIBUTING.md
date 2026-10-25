# Contributing: minding our Ps and Qs

The goal is reproducible historical research, with a small and understandable
engineering layer. These practices apply to human and AI-assisted contributions.
Always-on agent guidance is in [AGENTS.md](AGENTS.md); do not maintain a second,
competing copy for another assistant.

## Where information belongs

| Document | Owns |
|---|---|
| [README.md](README.md) | Public overview, navigation and local setup |
| [HANDOFF.md](HANDOFF.md) | Current research context and known facts |
| [notes/record.md](notes/record.md) | Computational results, commands, evidence and limitations |
| [notes/plan.md](notes/plan.md) | Research hypotheses and search strategy |
| [notes/experiment-shortlist.md](notes/experiment-shortlist.md) | Priorities, estimated effort and bounded completion status |
| [GPU-Experiments-ToDo.md](GPU-Experiments-ToDo.md) | Heavy GPU work, prerequisites, budgets and acceptance criteria |
| [notes/engineering-plan.md](notes/engineering-plan.md) | Engineering hygiene work and deferred tooling decisions |

Update the document that owns a fact, then update summaries or links only where
the change affects them. Preserve dated historical records; add a clearly
identified correction rather than silently rewriting what an older run covered.
Do not turn the handoff into an ever-growing task transcript.

## Before starting

1. Check the current branch, HEAD and worktree. Agree on scope; keep unrelated
   work intact and use a task branch for implementation.
2. Read the relevant existing code, controls and recorded evidence. Check for
   an existing helper or experiment before building another.
3. For a small fix, a short task description and regression test are enough.
   For a new experiment, use the plan below before running it. Extend an
   existing planning document rather than creating one file per conversation.
4. Obtain an explicit budget before heavy computation. Record hardware,
   backend/device, runtime or keyspace limits, and stop conditions. Estimates
   are not authorization.

### Experiment plan template

Use the relevant section of the research plan, shortlist or GPU backlog:

```text
Question/hypothesis:
Prior evidence and why this adds coverage:
Frozen inputs, encodings and target definitions:
Algorithms, suffixes, readings and expected evaluation counts:
Positive controls and how the real path recovers them:
Compute budget, prerequisites and stop conditions:
Reproduction command, environment and output location:
Acceptance criteria and limits of any negative result:
Status: proposed / ready / running / completed / time-limited / blocked
Result record and remaining work:
```

Do not label a run completed merely because a process exited successfully.
Check controls, actual counts, output integrity and intended scope first.
If inputs or implementation change, identify the new run and retain the
distinction from earlier coverage.

## The Ps and Qs review

- **Parameters:** Identify curve, field, basis/encoding, coordinate, group order
  and cofactor. Do not confuse field modulus p with subgroup order n (sometimes
  called q in source literature). Verify any conversion against known values.
  Distinguish the subgroup half from all rational cofactor preimages.
- **Provenance:** State where a parameter or claim came from: published source,
  independently checked arithmetic, reported historical account, or conjecture.
  Link evidence and identify what was actually inspected. Do not fetch private
  material merely because a link to it exists.
- **Precision:** Explain the exact bit ranges and transformations. Hex-character
  reversal is not byte reversal; a substring search is not reduction modulo p.
  A broad 148-bit match is not an exact 152-bit or full-coordinate match.
- **Positive controls:** Recover a planted/known answer through each newly
  claimed path, including suffixes, alternate readings or output entrypoints
  where relevant. Add regression coverage for bugs in accounting and manifests.
- **Quantities:** Separate input entries from unique byte strings, configured
  hash invocations from underlying compression calls, and hashes from
  reading/window comparisons. Check reported totals against the actual loop
  dimensions and explain duplicate variants.
- **Qualifications:** A bounded negative rules out only the recorded domain.
  Mark partial, skipped, failed and time-limited work explicitly. Separate
  throughput measurement from hypothetical rates and a structural observation
  from a recovered recipe.

## Validation

For focused standard-library tests, from the repository root in PowerShell:

```powershell
python -m unittest discover -s tests -p test_nothing_up_my_sleeve.py -v
```

Replace the pattern with the relevant test file. That example does not discover
`scripts/test_secg.py` and is not a substitute for the combined suite.

For the existing Windows/WSL setup:

```powershell
python scripts\local.py test
```

This checks sandbox isolation and discovers both `tests/` and
`scripts/test_secg.py`, including PARI validation when available. Follow
[README.md](README.md) for prerequisites. Build the container only when needed;
building requires network access, while normal test runs use the restricted
runtime. Report missing tools and test skips, including SageMath, explicitly.

- Run focused tests first and the combined suite when changing shared code,
  arithmetic, runner behavior or experiment entrypoints.
- For changed experiments, execute the bounded run and verify the produced
  manifest, counts, controls, hits and checksums, not just its exit code.
- For documentation-only changes, check links, commands and consistency with
  the implementation; no numerical sweep or GPU job is needed.
- Check the final diff for whitespace errors, accidental artifacts and unrelated
  changes. Use WSL Git if native Git is unavailable on this machine.

## Results and delivery

Record exact reproduction commands and environment, frozen input/source
checksums, actual coverage and byte-exact witnesses for hits. Specify whether
output is a committed research result in `results/` or an ignored local run in
`runs/`. Keep failed/incomplete runs identifiable rather than presenting them
as clean negatives. Never commit tools, secrets, private inputs or raw logs
without review.

The final handoff should say:

- What changed and why; which hypotheses remain open.
- What ran, what passed, and what was skipped or not run.
- Where the result and its scope are recorded.
- Branch and commit, worktree state, and whether anything was pushed.

Do not infer permission to publish private evidence or launch an expensive run
from permission to edit code. Do not push, open a PR or change shared Git
configuration without authorization.
