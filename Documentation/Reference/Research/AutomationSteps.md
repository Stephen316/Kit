# Research automation implementation steps

## Status and ownership

This register belongs to the [neutral-first plan](AutomationPlan.md).
A01 is complete as a source-backed contract and capability audit.
**Current step: A03 — durable evidence store and job controller.**
A03 is authorized and owned by jdharcourt on [PR #94](https://github.com/TryUniCAD/Kit/pull/94).
A02's corpus tooling and paired specifications are complete; independent capture qualification remains blocked.
A04–A16 remain planned and unassigned and require a subsequent request.
Read the [A01 decision and evidence](NeutralContractAudit.md) before claiming subsequent authorized work.

Keep identifiers stable when splitting work or revising estimates.
Use suffixes for new child steps and retain the parent identifier.
Each contributor claims a step through a PR comment before starting authorized work.
Record the owner, task branch, dependencies and current revision.
Check existing claims before claiming overlapping work.
Coordinate shared files explicitly and preserve other contributors' changes.

The document is the durable register.
PR comments provide the event history and evidence links.
Update the owner and status cells when an accepted documentation change records a new claim or disposition.
The controller's SQLite ledger is a separate runtime artifact.

Statuses are `planned`, `active`, `blocked`, `checking` and `complete`.
Use `complete` only after the row's exit criterion has matching evidence.
A local patch, model answer or posted review request does not establish completion.
If work pauses or changes owner, post a handoff with remaining tasks.

## Step register

| ID  | Deliverable                                            | Depends on                 | Owner      | Status   | Exit criterion                                                                                                                                                                                                                     |
| --- | ------------------------------------------------------ | -------------------------- | ---------- | -------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A01 | Neutral contract and capability audit                  | None                       | jdharcourt | complete | Existing fields, demonstrated gaps, version scope and independent acceptance requirements documented                                                                                                                               |
| A02 | Pinned corpus and paired authoring specifications      | A01                        | jdharcourt | blocked  | Hashed inputs, actual measurements, missing dependencies and independent holdout families recorded                                                                                                                                 |
| A03 | Durable evidence store and job controller              | A01                        | jdharcourt | active   | Transactional jobs, dependency invalidation, leases, bounded retries and interruption recovery verified remotely                                                                                                                   |
| A04 | SOLIDWORKS → neutral reader integration                | A01, A02                   | Unassigned | planned  | Initial sketches and feature variants preserve required semantics and report unresolved records accurately                                                                                                                         |
| A05 | Fusion → neutral reader integration                    | A01, A02                   | Unassigned | planned  | Equivalent initial designs serialize through the same contract with independently supported meaning                                                                                                                                |
| A06 | Semantic graph comparison                              | A04, A05                   | Unassigned | planned  | Equal, intentionally different and ambiguous paired cases report correctly without broad identity masking                                                                                                                          |
| A07 | Bounded deterministic inference and priority scheduler | A03, A06                   | Unassigned | planned  | Real shared gaps yield traceable hypotheses, counterexamples and affected-file rescans without models                                                                                                                              |
| A08 | Controlled sample and trace workers                    | A02, A03                   | Unassigned | planned  | Exact recipes and versioned receipts work with healthy controls; absent workers block only dependent jobs                                                                                                                          |
| A09 | Scoped field maps and typed codec candidates           | A07                        | Unassigned | planned  | Solved pad-then-pad family is reproduced without model calls, with independent proof and zero donor blocks                                                                                                                         |
| A10 | Optional model investigation packets                   | A07, A09                   | Unassigned | planned  | Models-off operation, bounded escalation, validated responses, cost limits and rejection of false proposals verified                                                                                                               |
| A11 | Portable neutral → Fusion writer                       | A01, A06, A09              | Unassigned | planned  | Qualified portable graphs generate native files without source replay, proprietary runtime or opaque replacements                                                                                                                  |
| A12 | Portable neutral → SOLIDWORKS writer                   | A01, A06, A09              | Unassigned | planned  | Qualified portable graphs generate native files from understood fields and reject unsupported required semantics                                                                                                                   |
| A13 | Bidirectional native acceptance                        | A04, A05, A08, A11, A12    | Unassigned | planned  | Both routes match body count, volume, center of mass and feature history, preserve all required constraints/dependencies, and pass independent driving-parameter edits, restoration, rebuild and save/reopen with healthy controls |
| A14 | Independent remote compatibility and regression gates  | A03, A06                   | Unassigned | planned  | Exact-revision checks reject stale receipts, shared-reader/writer mistakes and unsupported input through real boundaries                                                                                                           |
| A15 | Unattended operation, reports and forecast pilot       | A07, A14; A10 when enabled | Unassigned | planned  | Two-week operating evidence records recovery, no-progress parking, model spend, blockers and verified documents unlocked                                                                                                           |
| A16 | Broader features and additional CAD families           | A13, A15                   | Unassigned | planned  | Each scoped feature/version/route has independent native acceptance; FreeCAD and CATIA use the same contract                                                                                                                       |

A14 is developed alongside the steps it checks.
Any dependent step requiring verification must wait for its applicable gates.
A08 can wait for application access while saved-file research continues.
A10 remains optional and never blocks deterministic operation.
A13 requires actual application evidence and cannot pass in offline-only mode.
A16 is an expansion milestone, not a promise of universal support.

## A02 implementation and remaining evidence

Shared PR head: `Stephen316/Kit:docs/automation-plan` on PR #94.
A02 source checkpoint: `93bbf684c323e28176f7bb329ab04b092e097b37`, consolidated into this PR with its implementation history preserved.
The corpus pins main `74a0bc353421c25f7a6c539897baadf593a05766`.
All A01–A16 code, documentation and progress stay on PR #94; no separate step PRs are used.

| Child ID | Deliverable                                                 | Status   | Evidence or remaining requirement                                                                                                                     |
| -------- | ----------------------------------------------------------- | -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| A02a     | Hashed native inputs and historical evidence index          | complete | 778 native files, 232 JSON evidence files and two historical notes pinned; remote corpus verification passed at `0dd47cda`                            |
| A02b     | Five paired recipes and controlled-variation specifications | complete | Explicit parameters, frames, constraints, edits, analytic expectations, tolerances and reserved family splits; source review and digest checks passed |
| A02c     | Independently authored and measured native pairs            | blocked  | Capture slots are empty; require exact-source hashes, application builds, healthy controls and independent edit/rebuild/save/reopen observations      |
| A02d     | Independent qualification and holdout ancestry              | blocked  | Imported lineage reservations are provisional; audit authorship and descendants before evaluating generalization                                      |

Historical measurements retain their original values and failures.
Relative filenames do not establish capture-time hash bindings.
Analytic expectations are labelled separately from observed values.
Zero native pairs are currently qualified; no conversion capability is claimed.
No A03–A16 implementation is included.
The [remote workflow-quality job](https://github.com/TryUniCAD/Kit/actions/runs/43419522392/job/131865721189) passed pinned-object verification and all three process cases at `0dd47cdab9d51d24b87acae61ffb1f174ba44d81`.
That observation completes the A02a–A02b artifact criteria; it does not qualify the missing captures or prove product acceptance.

## A03 implementation and verification

Task branch: `feat/a03-durable-research-controller-20261113`; publication remains on this PR's shared `docs/automation-plan` head.
A03 depends on completed A01, so it can proceed while A02c–A02d wait for captures.
The [controller guide](ResearchController.md) records the implemented protocol and limits.

| Child ID | Deliverable                                             | Status   | Remaining evidence                                                                   |
| -------- | ------------------------------------------------------- | -------- | ------------------------------------------------------------------------------------ |
| A03a     | SQLite metadata and immutable hashed artifacts          | checking | Remote persistence, integrity and rollback-boundary checks                           |
| A03b     | Dependency fingerprints and transitive invalidation     | checking | Remote unchanged reuse, changed inputs/rules and stale-result fencing                |
| A03c     | Claims, leases, bounded retries and exclusive resources | checking | Remote competing claims, interruption recovery, waits, backoff and resource recovery |
| A03d     | Controller workflow and maintained usage information    | checking | Current-head CI and configured review                                                |

**A03 design decision:** adopt standard-library SQLite metadata and SHA-256 files in the existing `re/automation/` tree.
Use a local rollback journal, explicit write transactions and full synchronization; do not introduce a second case-variant research directory.
Worker result submission uses the controller protocol, not direct database writes.
No model, CAD worker launcher, decoder integration or neutral schema change is added by this step.

## Required PR progress comments

Post a top-level comment on [PR #94](https://github.com/TryUniCAD/Kit/pull/94) when claiming authorized work.
Post updates after a meaningful result, accepted push, failed verification, blocker, ownership change or handoff.
During sustained work, post at least one consolidated update per working day.
Do not post repetitive polling messages.
Implementation step IDs must appear in PR descriptions, relevant commits and progress comments.
All implementation stays on PR #94 and identifies the matching register rows.
Do not open separate PRs for A01–A16 unless the user changes this instruction.

Use a short, readable Markdown comment with these sections.
Replace every bracketed value and link evidence directly.

```markdown
### Current step: Axx — [step name]

**Status:** [active / blocked / checking / complete]
**Owner:** [github login]
**Revision:** [exact SHA or explicitly uncommitted]
**Work:** [branch and PR link]

**Completed**

- [Concrete result since the last update]

**Evidence**

- [Source/report link and exact-revision CI result]

**Remaining**

- [Unfinished exit criteria, or none for this step]

**Blockers:** [Missing prerequisite or none]
**Next:** [Specific next action or handoff]
```

For a claim, identify dependencies and the files the contributor owns.
For a blocker, state what change would make the job runnable.
For completion, link every required observation and identify the validated capability scope.
Do not use same-format success to close a cross-format conversion step.

## Documentation checkpoint

The current change aligns the plan, adds this register and records contributor instructions.
A01 now supplies the audited neutral-format decision and capability boundaries.
PR #94 now includes A02 corpus tooling, specifications and remote process coverage.
A03 now implements the durable metadata/lease protocol; remote verification is pending.
No codec integration, comparator, schema extension or application worker has been implemented through these steps.
Native capture qualification remains blocked separately.
A04–A16 have not started.
Formatting and source-link review do not replace the remote process checks.
Remote CI, configured review and merge-group acceptance remain separate publication evidence.
