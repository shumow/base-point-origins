# AI engineering hygiene plan

Opened 24 October 2026 on `work/ai-engineering-hygiene`, from `main` at
`c5e91e6`. This is the engineering work plan, not a new research roadmap.

## Goal

Make it easy for a fresh human or agent to choose the right evidence, scope a
reproducible experiment, validate the actual outcome, and hand off work without
inflating research claims or duplicating planning documents.

## First pass

- [x] Inventory existing guidance, planning documents and validation entrypoints.
- [x] Add one concise root [AGENTS.md](../AGENTS.md), with research invariants,
  evidence rules and local execution boundaries.
- [x] Add [CONTRIBUTING.md](../CONTRIBUTING.md), including document ownership,
  the Ps and Qs review, an experiment plan template and validation guidance.
- [x] Link the guidance from the public entrypoint and check all new local links.
- [x] Verify commands and instructions against the existing implementation,
  review the diff and record validation below.

Acceptance: a contributor can find the current research state, choose where a
plan/result belongs, identify required controls and validation commands, and
understand the Windows/WSL/GPU boundary without reading a conversation history.
No numerical results, search coverage or runtime behavior should change.

## Deliberately deferred

- **CI and automated result-schema checks:** assess separately after identifying
  which controls can run portably, which need PARI/Sage, and whether recorded
  environment fields permit deterministic comparisons. Do not claim this
  first pass enforces the written guidance.
- **Prompt files, custom agents and skills:** add only for a demonstrated,
  repeated workflow that ordinary instructions cannot express. Avoid parallel
  tool-specific instruction trees.
- **Hooks, formatters and new dependencies:** require a concrete failure mode,
  compatibility assessment and a small tested implementation before adoption.
- **Broad historical-document cleanup:** do not rewrite older records as though
  they used current target definitions. Correct or annotate individual claims
  when evidence justifies it.
- **Heavy experiments:** remain in the [GPU backlog](../GPU-Experiments-ToDo.md);
  this branch neither authorizes nor launches them.

## Maintenance

Keep the always-on guidance short. When behavior or commands change, update
the owning document in the same change; keep plans linked to result records
instead of copying the results. Review these instructions when onboarding a
new agent exposes a specific ambiguity, not on an arbitrary recurring schedule.

## Validation record

First-pass documentation checks completed on 24 October 2026:

- All 37 checked local Markdown links resolve, including the three new README
  links; the three new documents are ASCII.
- Root `AGENTS.md` is the sole repository-wide instruction file; no
  `.github/copilot-instructions.md` was found.
- Static checks confirm the local runner's test action includes the sandbox
  probe and both test discovery locations. The focused command discovers
  14 structured-corpus tests without executing them.
- `git diff --check` passes; changes are limited to these three new documents
  and README navigation. No source code or recorded numerical results changed.

No tests, numerical sweeps or GPU campaigns were executed for this
documentation-only pass. No new enforcement tooling is included.
