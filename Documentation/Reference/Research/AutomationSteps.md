# Research automation implementation steps

## Status and ownership

This register belongs to the [neutral-first plan](AutomationPlan.md).
A01 is complete as a source-backed contract and capability audit.
**Current work: A02d capture evidence, A04c semantic qualification and A08b/A08e worker verification.**
A05a reader integration and A08a supervisor process gates passed at `c1c3fcce5b8b67373113ec44ad5d122a52bd7260`.
A05 semantic qualification remains blocked independently.
The current request authorizes remaining deterministic work in dependency order on [PR #94](https://github.com/TryUniCAD/Kit/pull/94).
A04a–A04b and A03e are verified at code checkpoint `eba0ab488a6a00e2a31fd5ed8ab0bee564b371db`.
Current continuation branch: `feat/pr94-status-20261115-0117`; publication stays on the shared PR head.
A02's corpus tooling and paired specifications are complete; independent capture qualification remains blocked.
Claim subsequent runnable child steps explicitly.
Model execution and policy exceptions retain the approvals described in the plan.
Read the [A01 decision and evidence](NeutralContractAudit.md) before claiming subsequent authorized work.

Keep identifiers stable when splitting work or revising estimates.
Use suffixes for new child steps and retain the parent identifier.
Each contributor claims a step through a PR comment before starting authorized work.
Record the owner, task branch, dependencies and current revision.
Check existing claims before claiming overlapping work.
Coordinate shared files explicitly and preserve other contributors' changes.

The document is the durable register.
It is the only maintained record of step status.
Other pages link here instead of repeating status.
PR comments provide the event history and evidence links.
Update the owner and status cells when an accepted documentation change records a new claim or disposition.
The controller's SQLite ledger is a separate runtime artifact.

Statuses are `planned`, `active`, `blocked`, `checking` and `complete`.
Use `complete` only after the row's exit criterion has matching evidence.
A local patch, model answer or posted review request does not establish completion.
If work pauses or changes owner, post a handoff with remaining tasks.

## Step register

| ID  | Deliverable                                            | Depends on                           | Owner      | Status   | Exit criterion                                                                                                                                                                                                                     |
| --- | ------------------------------------------------------ | ------------------------------------ | ---------- | -------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A01 | Neutral contract and capability audit                  | None                                 | jdharcourt | complete | Existing fields, demonstrated gaps, version scope and independent acceptance requirements documented                                                                                                                               |
| A02 | Pinned corpus and paired authoring specifications      | A01                                  | jdharcourt | blocked  | Hashed inputs, actual measurements, missing dependencies and independent holdout families recorded                                                                                                                                 |
| A03 | Durable evidence store and job controller              | A01                                  | jdharcourt | complete | Transactional jobs, dependency invalidation, leases, bounded retries and interruption recovery verified remotely                                                                                                                   |
| A04 | SOLIDWORKS → neutral reader integration                | A01, A02a                            | jdharcourt | blocked  | Initial sketches and feature variants preserve required semantics and report unresolved records accurately                                                                                                                         |
| A05 | Fusion → neutral reader integration                    | A01, A02a                            | Stephen316 | active   | Equivalent initial designs serialize through the same contract with independently supported meaning                                                                                                                                |
| A06 | Semantic graph comparison                              | A02c, A04, A05                       | Unassigned | planned  | Equal, intentionally different and ambiguous paired cases report correctly without broad identity masking                                                                                                                          |
| A07 | Bounded deterministic inference and priority scheduler | A03, A06                             | Unassigned | planned  | Real shared gaps yield traceable hypotheses, counterexamples and affected-file rescans without models                                                                                                                              |
| A08 | Controlled sample and trace workers                    | A02b, A03                            | jdharcourt | active   | Exact recipes and versioned receipts work with healthy controls; absent workers block only dependent jobs                                                                                                                          |
| A09 | Scoped field maps and typed codec candidates           | A07                                  | Unassigned | planned  | Solved pad-then-pad family is reproduced without model calls, with independent proof and zero donor blocks                                                                                                                         |
| A10 | Optional model investigation packets                   | A08a, A07, A09                       | Unassigned | planned  | Models-off operation, fixed two-step escalation, a failure log, repeat-failure start-step routing, validated responses, cost limits and false-proposal rejection verified                                                          |
| A11 | Portable neutral → Fusion writer                       | A01, A06, A09                        | Unassigned | planned  | Qualified portable graphs generate native files without source replay, proprietary runtime or opaque replacements                                                                                                                  |
| A12 | Portable neutral → SOLIDWORKS writer                   | A01, A06, A09                        | Unassigned | planned  | Qualified portable graphs generate native files from understood fields and reject unsupported required semantics                                                                                                                   |
| A13 | Bidirectional native acceptance                        | A04, A05, A08, A11, A12              | Unassigned | planned  | Both routes match body count, volume, center of mass and feature history, preserve all required constraints/dependencies, and pass independent driving-parameter edits, restoration, rebuild and save/reopen with healthy controls |
| A14 | Independent remote compatibility and regression gates  | A03; A06 for reader and writer gates | Unassigned | planned  | Exact-revision checks reject stale receipts, shared-reader/writer mistakes and unsupported input through real boundaries                                                                                                           |
| A15 | Unattended operation, reports and forecast pilot       | A07, A08b, A14; A10 when enabled     | Unassigned | planned  | Two-week operating evidence records recovery, no-progress parking, blockers and verified documents unlocked. Record model spend when enabled                                                                                       |
| A16 | Broader features and additional CAD families           | A13, A15                             | Unassigned | planned  | Each scoped feature/version/route has independent native acceptance; FreeCAD and CATIA use the same contract                                                                                                                       |

A04 and A05 start on the pinned corpus from A02a.
Paired captures from A02c gate paired comparison and native acceptance, not reader integration.
A08 needs the paired recipes from A02b, not the captures that it produces.
A14 starts its controller and corpus gates after A03; its reader and writer gates wait for A06.
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

| Child ID | Deliverable                                                 | Status   | Evidence or remaining requirement                                                                                                                                                                                                                                                                                                                                                          |
| -------- | ----------------------------------------------------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| A02a     | Hashed native inputs and historical evidence index          | complete | 778 native files, 232 JSON evidence files and two historical notes pinned; remote corpus verification passed at `0dd47cda`                                                                                                                                                                                                                                                                 |
| A02b     | Five paired recipes and controlled-variation specifications | complete | Explicit parameters, frames, constraints, edits, analytic expectations, tolerances and reserved family splits; source review and digest checks passed                                                                                                                                                                                                                                      |
| A02c     | Independently authored and measured native pairs            | complete | Fusion and SOLIDWORKS captures for P01–P05 recorded. The [SOLIDWORKS capture entry](../../Changes/Research/SolidWorksPairedCaptures.md) links the native files, application build, controls, and edit, rebuild, and reopen evidence                                                                                                                                                        |
| A02d     | Independent qualification and holdout ancestry              | blocked  | [Audit verifies 74 native files and ten receipts](../../Changes/Research/PairedCaptureLineageAudit.md). [Corpus intake](../../Changes/Research/PairedCaptureIntake.md) records the split and blockers. [Fusion fresh-process evidence](../../Changes/Research/FusionFreshProcessEvidence.md) still needs a native run, and observation binding gaps remain. P05 stays reserved for holdout |

Historical measurements retain their original values and failures.
Relative filenames do not establish capture-time hash bindings.
Analytic expectations are labelled separately from observed values.
Zero native pairs are currently qualified; no conversion capability is claimed.
A02 evidence does not establish completion of later steps.
The [remote workflow-quality job](https://github.com/TryUniCAD/Kit/actions/runs/43419522392/job/131865721189) passed pinned-object verification and all three process cases at `0dd47cdab9d51d24b87acae61ffb1f174ba44d81`.
That observation completes the A02a–A02b artifact criteria. The A02d audit verified the committed capture bytes and found no exact-byte aliases in the audited tree or the pinned historical corpus.

## A03 implementation and verification

Task branch: `feat/a03-durable-research-controller-20261113`; publication remains on this PR's shared `docs/automation-plan` head.
A03 depends on completed A01, so it can proceed while A02c–A02d wait for captures.
The [controller guide](ResearchController.md) records the implemented protocol and limits.

| Child ID | Deliverable                                             | Status   | Remaining evidence                                                                                            |
| -------- | ------------------------------------------------------- | -------- | ------------------------------------------------------------------------------------------------------------- |
| A03a     | SQLite metadata and immutable hashed artifacts          | complete | Remote persistence, integrity, rollback and schema-upgrade checks passed at `6a846c7d`                        |
| A03b     | Dependency fingerprints and transitive invalidation     | complete | Remote reuse, changed inputs/rules, cycle checks and incremental large-queue execution passed                 |
| A03c     | Claims, leases, bounded retries and exclusive resources | complete | Remote concurrency, interruption recovery, waits, backoff, fencing and resource recovery passed               |
| A03d     | Controller workflow and maintained usage information    | complete | Process workflow and configured approval passed at `eba0ab48`; current PR readiness remains separate          |
| A03e     | Metadata-only lease renewal                             | complete | Twelve controller process scenarios passed at `eba0ab48`, including a 64 MiB payload and corruption rejection |

A03e is the review repair owned by jdharcourt on PR #94.
It removes artifact-content reads from heartbeat renewal while retaining token, deadline and prerequisite checks.
Claims, result submission, status and artifact access retain integrity checks.
The 64 MiB process scenario passed remotely without a schema change.
See [the change entry](../../Changes/Research/MetadataOnlyLeaseRenewal.md).

**A03 design decision:** adopt standard-library SQLite metadata and SHA-256 files in the existing `re/automation/` tree.
Use a local rollback journal, explicit write transactions and full synchronization; do not introduce a second case-variant research directory.
Worker result submission uses the controller protocol, not direct database writes.
No model, CAD worker launcher, decoder integration or neutral schema change is added by this step.
The [remote controller verification job](https://github.com/TryUniCAD/Kit/actions/runs/43427628978/job/131892879264) passed all eleven process scenarios on Python 3.14 at `6a846c7d1a6e144cf04a7c30e32261c7be84ea68`.
Coverage includes 250 completed steps in a 10,000-job chain, 300 individual submissions and schema upgrades, as well as the lifecycle/integrity scenarios.
All verified review findings on that code revision are addressed and its threads are resolved.
The earlier approval was dismissed.
At `eba0ab48`, all 26 displayed checks passed and configured review `5894929093` was `APPROVED` for that exact head.
The [updated workflow-quality job](https://github.com/TryUniCAD/Kit/actions/runs/43467308910/job/132029763989) passed twelve controller scenarios in 71.61 seconds.
All configured findings were resolved.
GitHub separately reported `REVIEW_REQUIRED` under its enforced review rules despite that configured approval.
Current-head PR readiness and deferred merge-group acceptance remain separate from the completed artifact scope recorded here.

## A04 integration and semantic qualification

| Child ID | Deliverable                                          | Depends on                              | Owner      | Status   | Exit criterion or remaining evidence                                                                                                                                                                                                                                                            |
| -------- | ---------------------------------------------------- | --------------------------------------- | ---------- | -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A04a     | Pinned SLDPRT reader and typed neutral serialization | A01, A02a                               | jdharcourt | complete | All 58 pinned parts decoded/reconstructed; strict per-asset success, overwrite and tamper checks passed at `eba0ab48`                                                                                                                                                                           |
| A04b     | Separate field-path evidence and unresolved census   | A04a                                    | jdharcourt | complete | Remote receipts at `eba0ab48` retain native-only content, bytes, codes, diagnostics and unqualified direction/frame mappings                                                                                                                                                                    |
| A04c     | Initial profile and variant semantic qualification   | A04a, A04b; independent source evidence | jdharcourt | active   | [Discovery census](../../Changes/Research/SolidWorksDiscoveryCensus.md) decodes 25 committed files. CI verifies P01 rectangle edges, P03 boss reversal and P04 equation references. YZ support, P04 sketch and face ownership, through-all termination and full constraint bindings remain open |

The [reader guide](SolidworksResearchReader.md) defines the command and its research-only receipt.
A04a–A04b do not close A04c or qualify native conversion.
The reader does not infer missing constraints, repair the SDK mappings, launch applications or execute models.
A04c needs independent source inventories and distinguishing evidence rather than agreement with the same reader.
Its blocked status does not prevent A05 integration or A08a implementation.
The updated workflow-quality job passed all three reader scenarios in 60.15 seconds with 58 decoded and zero rejected.
The earlier sequential process harness took 172.97 seconds on `7f8a7425`; these are CI observations, not a universal speed guarantee.
A05 is claimed separately below.
A08a process gates passed at `c1c3fcce`; see the [supervisor guide](ResearchSupervisor.md).
A08b bounded logging, restart cleanup and resource controls passed eleven Linux process scenarios at `b86f30c7`.

## A05 integration and semantic qualification

| Child ID | Deliverable                                                        | Depends on                              | Owner      | Status   | Exit criterion or remaining evidence                                                                         |
| -------- | ------------------------------------------------------------------ | --------------------------------------- | ---------- | -------- | ------------------------------------------------------------------------------------------------------------ |
| A05a     | Pinned F3D/F3Z reader, run summary and typed neutral serialization | A01, A02a                               | Stephen316 | complete | Five remote scenarios passed at `c1c3fcce`: 714 inputs, 12 strict, 685 partial and 17 rejected               |
| A05b     | Exact per-file outcome gate                                        | A05a                                    | jdharcourt | complete | Full report pinned at `480d9d3a`; exact baseline enforcement passed all five reader scenarios at `b86f30c7`  |
| A05c     | Initial profile and variant semantic qualification                 | A05a, A05b; independent source evidence | Stephen316 | blocked  | Independently establish required P01–P05 semantics, frames, termination, constraints and dependency bindings |

The [reader guide](FusionResearchReader.md) defines the command, its run summary and its research-only receipts.
A05a uses the strict SDK reader first and accepts the partial legacy reader only with an explicit option.
A05a does not close A05b or A05c or qualify native conversion.
A05c needs independent source inventories and distinguishing evidence rather than agreement with the same reader.
See [the change entry](../../Changes/Research/PinnedFusionReader.md).

## Parallel-session child steps

These rows incorporate the [parallel-session design](ParallelSessions.md#delivery).
Their parent identifiers remain stable.
They are not implemented by documenting the rows.

| Child ID | Deliverable                                                                          | Depends on                                           | Owner      | Status   | Exit criterion                                                                                                                                                                                                                   |
| -------- | ------------------------------------------------------------------------------------ | ---------------------------------------------------- | ---------- | -------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A08a     | Supervisor, private session directories, pools, controller interface and A03 adapter | A03 technical substeps                               | Stephen316 | complete | Six supervisor process scenarios passed at `c1c3fcce`, alongside fifteen controller scenarios covering counted resources and pool claims                                                                                         |
| A08b     | Headroom, adaptive limits, calibration and grouped small-file sessions               | A08a                                                 | jdharcourt | active   | Eleven Linux process scenarios passed at `b86f30c7`, covering bounded logs, restart cleanup, CPU/memory admission and memory stops. Adaptive calibration and grouping remain open                                                |
| A08c     | Isolated application authoring, trace and acceptance workers                         | A02b, A08a                                           | jdharcourt | active   | Durable output intake passed five macOS process cases at `ef431a17`; Windows flag-owner repair and Linux verification are checking. Application dispatch, recipe hashes, fresh-process readback and healthy controls remain open |
| A08d     | Installed CLI compatibility, delivered separately in PR #119                         | A03, A04a, A05a, A08a source interfaces              | jdharcourt | blocked  | At PR #119 head `10f19a04`, research CLI checks passed on Linux and Windows against PR #94 `b86f30c7`; its separate conversion/inspection gate failed                                                                            |
| A08e     | Windows host support for the supervisor and application workers                      | A08a                                                 | jdharcourt | active   | Six Windows process cases passed at `91d90628`; native application-worker dispatch remains open. Fourteen macOS and fourteen Linux process cases passed at the same head; native application-worker execution remains open       |
| A10a     | Optional Codex runner and private data boundary                                      | A08a, A07, A09; explicit model-command authorization | Unassigned | planned  | Candidate validation, isolated reads, bounded packets/patch paths and verified runner contracts                                                                                                                                  |
| A10b     | Step validation, selector, failure log and start-step routing                        | A10a                                                 | Unassigned | planned  | Separate infrastructure/model failures, exact cache keys, stable packet prefixes, budgets, fallback after a first-step failure and two-failure start-step routing                                                                |
| A10c     | Use report for each model step and route key                                         | A10b, A09                                            | Unassigned | planned  | Recorded attempts, passes, model failures and tokens per pass for each step. The report never changes the selected models                                                                                                        |
| A10d     | Optional Claude API and Claude Code runners                                          | A08a, A07, A09; applicable authorization             | Unassigned | planned  | Provider validation, serving-model attribution, bounded errors and private-data/policy gates                                                                                                                                     |
| A14a     | Controller and corpus process gates                                                  | A03 technical substeps                               | jdharcourt | complete | Corpus and twelve controller scenarios passed at `eba0ab48`; extend the gate when interfaces change                                                                                                                              |
| A14b     | Reader, comparator and writer regression gates                                       | A04a, A05; A06 for paired gates                      | Unassigned | planned  | Pinned-input process checks plus independent semantic evidence reject unsupported/stale results                                                                                                                                  |
| A14c     | Batched remote verification receipts                                                 | A03, A09, A14b                                       | Unassigned | planned  | Stage 11 research check, `waiting_ci` candidates, recorded batch artifacts, resumption and dependent invalidation after a failed batch                                                                                           |
| A15a     | Two-week deterministic operating pilot, with optional enabled model pools            | A07, A08b, A14; A10c/A10d only when enabled          | Unassigned | planned  | Measure elapsed and active agent time, throughput, recovery, blockers, verified capability gains, and any operator intervention. Track model spend when enabled                                                                  |

The model pairs do not become runtime requirements for a models-off pilot.
The coordinating agent runs remote CI in batches. See [batched remote verification](AutomationPlan.md#batched-remote-verification).
A08c includes the [always-busy application loop](ParallelSessions.md#application-workers-that-stay-busy): continuous claims, work ahead of decoding, scheduled resets and batch controls.
A08e lets the controller, supervisor and both applications run on one Windows host.
The local-check proposal is not in force: all test execution remains remote.
A10 must not silently approve model-run shell commands or transmit private designs.

## Required PR progress comments

Post a top-level comment on [PR #94](https://github.com/TryUniCAD/Kit/pull/94) when claiming authorized work.
Post whenever any change or stage starts, progresses meaningfully, completes, becomes blocked or is handed off.
Post after every accepted push and failed verification.
A chat update or PR-body edit does not replace a top-level comment.
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
A03 and its heartbeat repair passed remote process verification at the recorded code checkpoints; PR readiness remains separate.
A04 adds a research reader boundary and evidence receipt around the existing codec.
No comparator, schema extension or application worker is established by that integration.
Native capture qualification remains blocked separately.
A04a–A04b passed remote verification. A04c has independent SOLIDWORKS measurements for bounded discovery comparisons.
At PR head `1bdb6743`, the remote discovery checks decoded all 25 parts. They verified six P01 edge counts and five XY endpoint comparisons, eight P03 boss direction cases, both P03 Front Plane directional Z bounds, both P04 equation bindings in eleven captures, and the resolved inch-length checks. The two expected Z intervals came from the independently measured boss centroids and depths. P01 and P03 YZ variants still fall back to the Front plane. [Discovery checks](https://github.com/TryUniCAD/Kit/actions/runs/43652490420/job/132623817084)
The [P04 configuration-stream investigation](../../../re/solidworks/records/P04SketchResidence.md) locates both sketches' marker groups. The resolved feature owners still need a direct native reference.
Later deterministic child steps remain available when their prerequisites pass.

### Reconciled remote evidence and current limits

[Workflow quality at `c1c3fcce`](https://github.com/TryUniCAD/Kit/actions/runs/43656612973/job/132636421153) passed five Fusion reader, fifteen controller and six supervisor process scenarios.
The Fusion corpus contained 714 inputs: 12 strict decodes, 685 partial decodes and 17 rejections.
These results close A05a and A08a's recorded process gates, not semantic qualification.
A05b now pins the first complete remote report from `480d9d3a` unchanged.
That cross-revision comparison passed at `b86f30c7` against the unchanged 714-file baseline.

A02d remains blocked: the implementation host refused connections to the documented Fusion bridge, and native UI initialization failed.
The [fresh capture binding change](../../Changes/Research/FusionSketchBindingCapture.md) adds pinned observation-local constraint and dimension references.
Both preparation cases passed remotely at `480d9d3a`. No native run or new qualified pair is claimed.
P04 supporting-face identity and unsupported or unresolved bindings remain open.

A04c now records [hashed principal support candidates](../../Changes/Research/PrincipalSupportEvidence.md).
The new gate requires 25 measured plane identifiers, including three YZ variants.
The records remain unqualified until native class ownership and the opaque tag domain are established.

A08b adds [bounded logs and restart cleanup](../../Changes/Research/Supervisor/BoundedSessionLogs.md), with eight supervisor scenarios passed at `480d9d3a`.
CPU/memory admission and sampled group-memory stops passed all eleven Linux supervisor scenarios at `b86f30c7`.
It does not close adaptive capacity, calibration, grouped jobs, application workers or Windows support.
A08b now also implements [version-scoped memory estimates](../../Changes/Research/Supervisor/VersionedMemoryEstimates.md).
The [macOS gate at `91d90628`](https://github.com/TryUniCAD/Kit/actions/runs/43667302609/job/132669499511) passed all fourteen process cases in 132.47 seconds, including five-observation learning, restart/new-version isolation, a 55-session rolling-window check and invalid-history refusal before claims. The [Linux workflow-quality gate at `91d90628`](https://github.com/TryUniCAD/Kit/actions/runs/43667302609/job/132669499653) also passed all fourteen supervisor cases in 115.51 seconds, fifteen controller cases, seven corpus/preparation cases, three SOLIDWORKS reader cases and five Fusion cases against the unchanged exact-outcome baseline. Its native/API/registry stage passed 203 cases with 159 unavailable-corpus/platform skips. The CI aggregator passed at that head; remaining review findings still block readiness. [Adaptive concurrency](../../Changes/Research/Supervisor/AdaptivePoolLimits.md) is now implemented and checking through real minute, deadline, memory-stop and configuration boundaries. Calibration batches, grouped jobs and independent OOM attribution remain open.
A08e's [Windows gate at `30707236`](https://github.com/TryUniCAD/Kit/actions/runs/43666746526/job/132667719525) passed five cases; descendant completion retried after an exit status of 1 in 10.366 seconds. Source inspection identified an invalid launcher/interpreter PID equality in the fixture. The repair binds the observed parent chain and proves private Job Object membership.
The [Windows gate at `91d90628`](https://github.com/TryUniCAD/Kit/actions/runs/43667302609/job/132669500211) then passed all six process cases in 20.22 seconds, including descendant completion and crash recovery. Windows supervision is verified at that checkpoint; application-worker execution on Windows remains open under A08c/A08e.
The [macOS gate at `35080cec`](https://github.com/TryUniCAD/Kit/actions/runs/43666501725/job/132666944085) passed all eleven POSIX process cases in 75.81 seconds.
At `35080cec`, the affected native/API/registry stage passed 188 cases with 159 existing unavailable-corpus skips; seven corpus/preparation and three SOLIDWORKS reader cases also passed before the run was superseded. Those completed steps do not make its cancelled overall job green.
A08c now owns the durable declared-output intake prerequisite: session cleanup must not remove native outputs before a current-lease completion stores their verified artifacts. The optional output manifest and its Linux/macOS/Windows process gate are implemented. The [macOS gate at `ef431a17`](https://github.com/TryUniCAD/Kit/actions/runs/43668887044/job/132674283950) passed all nineteen cases, including the five intake scenarios. Windows passed eight and failed three because its reparse flag was imported from the wrong pywin32 module; the exact-source flag-owner repair is checking. Linux intake was not reached after native fixture failures. No application dispatch or native result is qualified by that implementation work.
A02d preparation now pins every committed Fusion variant for restarted-process readback; native execution remains blocked.
The two-week A15 pilot has not started and cannot be replaced by a short CI run.

Formatting and source-link review do not replace the remote process checks.
Remote CI, configured review and merge-group acceptance remain separate publication evidence.

## A08d deterministic research CLI compatibility

Owner: jdharcourt. Delivery: [separate CLI PR #119](https://github.com/TryUniCAD/Kit/pull/119).
The user clarified that the installed CLI belongs in its own PR and must remain compatible with PR #94's tools.
The CLI implementation, CLI-only tests, packaging changes, and guides are removed from this PR without rewriting history.
The research readers, controller, supervisor, export safeguards, and native decoding repairs remain here.
Compatibility checks in the separate PR select a pinned PR #94 checkout and preserve its existing document/receipt and runtime contracts.
No automatic model runner, persistent session-artifact ingestion, or native conversion qualification is claimed.

At PR #119 head `10f19a046a75d0409631eeb447af85167369132d`, [Linux research compatibility](https://github.com/TryUniCAD/Kit/actions/runs/43666848649/job/132668016477) passed seventeen cases with one platform skip, and [Windows research compatibility](https://github.com/TryUniCAD/Kit/actions/runs/43666848649/job/132668016227) passed seventeen cases. Both jobs checked out PR #94 revision `b86f30c7e41abdc3812ada795a193377f6ddd220` explicitly.
The independently registered [CLI conversion/inspection gate](https://github.com/TryUniCAD/Kit/actions/runs/43666848335/job/132668015805) failed twelve kind-classification cases with 617 passes, so PR #119's CI aggregator failed. Research protocol passes do not make that separate PR ready, and they do not verify later PR #94 heads. CLI repairs remain in PR #119.
