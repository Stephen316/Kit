# Research automation implementation steps

## Status and ownership

This register belongs to the [neutral-first plan](AutomationPlan.md).
A01 is complete as a source-backed contract and capability audit.
**Current work: A02d capture evidence, A04c semantic qualification, A05 semantic qualification, A08b/A08c/A08e worker implementation and A14b regression evidence.**
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
| A14 | Independent remote compatibility and regression gates  | A03; A06 for reader and writer gates | jdharcourt | active   | Exact-revision checks reject stale receipts, shared-reader/writer mistakes and unsupported input through real boundaries                                                                                                           |
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

| Child ID | Deliverable                                                        | Depends on                              | Owner      | Status   | Exit criterion or remaining evidence                                                                           |
| -------- | ------------------------------------------------------------------ | --------------------------------------- | ---------- | -------- | -------------------------------------------------------------------------------------------------------------- |
| A05a     | Pinned F3D/F3Z reader, run summary and typed neutral serialization | A01, A02a                               | Stephen316 | complete | Five remote scenarios passed at `c1c3fcce`: 714 inputs, 12 strict, 685 partial and 17 rejected                 |
| A05b     | Exact per-file outcome gate                                        | A05a                                    | jdharcourt | complete | Full report pinned at `480d9d3a`; exact 714-file baseline passed all five reader scenarios again at `22a59e68` |
| A05c     | Initial profile and variant semantic qualification                 | A05a, A05b; independent source evidence | Stephen316 | blocked  | Independently establish required P01–P05 semantics, frames, termination, constraints and dependency bindings   |

The [reader guide](FusionResearchReader.md) defines the command, its run summary and its research-only receipts.
A05a uses the strict SDK reader first and accepts the partial legacy reader only with an explicit option.
A05a does not close A05b or A05c or qualify native conversion.
A05c needs independent source inventories and distinguishing evidence rather than agreement with the same reader.
See [the change entry](../../Changes/Research/PinnedFusionReader.md).

## Parallel-session child steps

These rows incorporate the [parallel-session design](ParallelSessions.md#delivery).
Their parent identifiers remain stable.
They are not implemented by documenting the rows.

| Child ID | Deliverable                                                                          | Depends on                                           | Owner      | Status   | Exit criterion                                                                                                                                                                                                                                                             |
| -------- | ------------------------------------------------------------------------------------ | ---------------------------------------------------- | ---------- | -------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A08a     | Supervisor, private session directories, pools, controller interface and A03 adapter | A03 technical substeps                               | Stephen316 | complete | Six supervisor process scenarios passed at `c1c3fcce`, alongside fifteen controller scenarios covering counted resources and pool claims                                                                                                                                   |
| A08b     | Headroom, adaptive limits, calibration and grouped small-file sessions               | A08a                                                 | jdharcourt | active   | At `22a59e68`, Linux passed 57 and macOS 74 process cases, including calibration, grouping, owner recovery and launch gating. Linux measured upward adjustment and numeric deadline backoff from 2 to 1; saturated calibration and independent OOM attribution remain open |
| A08c     | Isolated application authoring, trace and acceptance workers                         | A02b, A08a                                           | jdharcourt | active   | At `22a59e68`, five intake and twelve application transport cases passed Linux/macOS; Windows passed intake and parking cases. Native dispatch, automatic restart, downstream bindings and unattended operation remain open                                                |
| A08d     | Installed CLI compatibility, delivered separately in PR #119                         | A03, A04a, A05a, A08a source interfaces              | jdharcourt | active   | PR #119 head `ffc86c97` passed Linux/Windows research compatibility against PR #94 `b86f30c7`, all 639 conversion/inspection cases and CI Agg. Later PR #94 heads remain outside that pinned evidence                                                                      |
| A08e     | Windows host support for the supervisor and application workers                      | A08a                                                 | jdharcourt | active   | Windows passed all twenty-two cases at `22a59e68`, including owner recovery, intake, both parking cases and all four immutable-record cases. Native Windows dispatch remains open                                                                                          |
| A10a     | Optional Codex runner and private data boundary                                      | A08a, A07, A09; explicit model-command authorization | Unassigned | planned  | Candidate validation, isolated reads, bounded packets/patch paths and verified runner contracts                                                                                                                                                                            |
| A10b     | Step validation, selector, failure log and start-step routing                        | A10a                                                 | Unassigned | planned  | Separate infrastructure/model failures, exact cache keys, stable packet prefixes, budgets, fallback after a first-step failure and two-failure start-step routing                                                                                                          |
| A10c     | Use report for each model step and route key                                         | A10b, A09                                            | Unassigned | planned  | Recorded attempts, passes, model failures and tokens per pass for each step. The report never changes the selected models                                                                                                                                                  |
| A10d     | Optional Claude API and Claude Code runners                                          | A08a, A07, A09; applicable authorization             | Unassigned | planned  | Provider validation, serving-model attribution, bounded errors and private-data/policy gates                                                                                                                                                                               |
| A14a     | Controller and corpus process gates                                                  | A03 technical substeps                               | jdharcourt | complete | Seven corpus and fifteen controller scenarios passed at `22a59e68`; extend the gate when interfaces change                                                                                                                                                                 |
| A14b     | Reader, comparator and writer regression gates                                       | A04a, A05; A06 for paired gates                      | jdharcourt | active   | Pinned reader/outcome and native-field refusal gates passed at `22a59e68`; independent semantic, comparator and writer acceptance still require A06 and native evidence                                                                                                    |
| A14c     | Batched remote verification receipts                                                 | A03, A09, A14b                                       | Unassigned | planned  | Stage 11 research check, `waiting_ci` candidates, recorded batch artifacts, resumption and dependent invalidation after a failed batch                                                                                                                                     |
| A15a     | Two-week deterministic operating pilot, with optional enabled model pools            | A07, A08b, A14; A10c/A10d only when enabled          | Unassigned | planned  | Measure elapsed and active agent time, throughput, recovery, blockers, verified capability gains, and any operator intervention. Track model spend when enabled                                                                                                            |

The model pairs do not become runtime requirements for a models-off pilot.
The coordinating agent runs remote CI in batches. See [batched remote verification](AutomationPlan.md#batched-remote-verification).
A08c includes the [always-busy application loop](ParallelSessions.md#application-workers-that-stay-busy): continuous claims, work ahead of decoding, scheduled resets and batch controls.
A08e targets the controller, supervisor and both applications running on one Windows host; native application execution remains open.
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

The latest verified source checkpoint is PR head `22a59e68c839354f3e6672eec6f67aa647aa1dce` against main `d85e42479bccc79bea5e0c7eeca6a0411cc9e2a9`.
The Linux job tested GitHub merge revision `6267defee23cfaee79c68d79a5fffb46c1c00253` for those inputs.
Every PR CI report, including [CI Agg](https://github.com/TryUniCAD/Kit/actions/runs/43678423564/job/132703569338), passed at that checkpoint.
Subsequent documentation heads require their own CI; this records a verified source checkpoint rather than predicting their results.

| Gate                             | Actual result                                                              | Evidence                                                                                  |
| -------------------------------- | -------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| Linux CI contracts               | 136 passed, 19.26 seconds                                                  | [Linux job](https://github.com/TryUniCAD/Kit/actions/runs/43678423785/job/132703622509)   |
| Native/API/registry              | 327 passed, 159 existing unavailable-corpus/platform skips, 74.46 seconds  | Same Linux job                                                                            |
| Typed carrier boundaries         | 31 passed, 148.54 seconds                                                  | Same Linux job                                                                            |
| Corpus/preparation               | 7 passed, 12.14 seconds                                                    | Same Linux job                                                                            |
| SOLIDWORKS reader                | 3 passed, 44.24 seconds; 58 decoded, zero rejected                         | Same Linux job                                                                            |
| Output/application transport     | 17 passed, 35.38 seconds                                                   | Same Linux job                                                                            |
| Fusion reader                    | 5 passed, 50.64 seconds; exact 714-file baseline unchanged                 | Same Linux job                                                                            |
| Durable controller               | 15 passed, 67.21 seconds                                                   | Same Linux job                                                                            |
| Linux supervisor                 | 57 passed, 393.51 seconds                                                  | Same Linux job                                                                            |
| macOS worker processes           | 74 passed, 514.07 seconds                                                  | [macOS job](https://github.com/TryUniCAD/Kit/actions/runs/43678423785/job/132703622604)   |
| Windows worker processes         | 22 passed, 77.49 seconds                                                   | [Windows job](https://github.com/TryUniCAD/Kit/actions/runs/43678423785/job/132703622723) |
| Fusion archive/API compatibility | 2,960 passed, 3 existing unavailable drawing-example skips, 515.95 seconds | [Fusion job](https://github.com/TryUniCAD/Kit/actions/runs/43678423837/job/132703567976)  |

A05b compares every file against the original complete report pinned at `480d9d3a`.
The outcomes remain 12 strict, 685 partial and 17 rejected; aggregate agreement alone cannot pass that gate.
These results verify reader integration and outcome stability, not geometry, constraints, dependency semantics or native conversion.

A08b now has passing process evidence for [bounded logs and cleanup](../../Changes/Research/Supervisor/BoundedSessionLogs.md), [version-scoped memory estimates](../../Changes/Research/Supervisor/VersionedMemoryEstimates.md), [adaptive limits](../../Changes/Research/Supervisor/AdaptivePoolLimits.md), [grouped sessions](../../Changes/Research/Supervisor/GroupedSmallFileSessions.md), [owner-epoch fencing](../../Changes/Research/Workers/SupervisorOwnerEpoch.md), [POSIX launch gating](../../Changes/Research/Supervisor/PosixWorkerLaunchGate.md) and [offline calibration](../../Changes/Research/Supervisor/OfflineDecoderCalibration.md).
The Linux log explicitly records a measured healthy-minute increase to two sessions and deadline-pair backoff from two to one.
Both POSIX selections include all fourteen calibration cases; no saturated throughput recommendation is established.
Windows calibration and independently attributed OOM backoff remain open.
Legacy no-owner controller calls and custom adapters without the fence capability remain explicitly unfenced.

A08c's five [durable-output intake](../../Changes/Research/Workers/DurableWorkerOutputs.md) cases passed on all three platforms.
The twelve [application transport/publication](../../Changes/Research/Workers/LocalApplicationDispatch.md) cases passed Linux/macOS.
Windows passed both unsupported-application parking cases and all four [immutable-record](../../Changes/Research/Workers/WindowsImmutableRecords.md) cases.
The revised sharing case proves refusal through CRT and native APIs plus successful same-path operations after handle release; successful pytest capture did not retain individual numeric error values.
These fixtures did not call native CAD APIs.
Native execution, automatic application restart, automatic acceptance acknowledgement, downstream bindings, batch resets and unattended operation remain open.
Completed and abandoned application spools stay retained until owner verification of actual controller acceptance; the completed-spool bound is 32 files and 520 MiB, not an OS write quota.

A04c records [hashed principal support candidates](../../Changes/Research/PrincipalSupportEvidence.md) for 25 measured identifiers, including three YZ variants.
Native class ownership and the opaque tag domain remain unqualified; P04 sketch/face ownership, through-all termination and complete constraint bindings remain open.
The [native-field refusal](../../Changes/Research/Readers/NativeFieldWriteRefusal.md) and [writer qualification](../../Changes/Research/Readers/NativeSemanticWriteQualification.md) regressions passed, preserving required-semantic refusal and destinations through real public/direct boundaries.
The full Fusion run also verifies the corrected explicit/inferred writer-ordering cases.
None of those refusals supplies the missing positive native qualification.

A02d remains blocked by application access: the documented Fusion bridge refused connections, initial native UI initialization failed, and a later read-only app inventory exposed neither Fusion nor SOLIDWORKS.
[Fresh-process readback](../../Changes/Research/FusionFreshProcessEvidence.md) now pins every committed Fusion variant, and [observation-local bindings](../../Changes/Research/FusionSketchBindingCapture.md) are implemented; a native run is still required to close provenance, observation binding and load diagnostics.
P05 stays reserved for holdout. Zero native pairs are qualified.
A06 waits for qualified A02d/A04c/A05c evidence; A07/A09 and both native writers retain their declared dependencies.
A13 needs native editable acceptance. The two-week A15 pilot has not started.
No local tests, collection, decoder experiments, native application runs or optional model-runner calls executed during this continuation.

All forty-one reported review threads were resolved at this checkpoint, but both configured native review reports were failed, one reported that review did not finish, and there was no approval for this head.
Green PR CI therefore did not establish readiness.
GitHub independently reported `REVIEW_REQUIRED` and enforced one approving review, code-owner review, last-push approval and resolved threads.
The PR merge-queue report does not establish successful heavy acceptance on an actual merge-group candidate.
No queue enrollment or merge was requested or performed.

## A08d deterministic research CLI compatibility

Owner: jdharcourt. Delivery: [separate CLI PR #119](https://github.com/TryUniCAD/Kit/pull/119).
The user clarified that the installed CLI belongs in its own PR and must remain compatible with PR #94's tools.
The CLI implementation, CLI-only tests, packaging changes, and guides are removed from this PR without rewriting history.
The research readers, controller, supervisor, export safeguards, and native decoding repairs remain here.
Compatibility checks in the separate PR select a pinned PR #94 checkout and preserve its existing document/receipt and runtime contracts.
No automatic model runner, persistent session-artifact ingestion, or native conversion qualification is claimed.

At PR #119 head `10f19a046a75d0409631eeb447af85167369132d`, [Linux research compatibility](https://github.com/TryUniCAD/Kit/actions/runs/43666848649/job/132668016477) passed seventeen cases with one platform skip, and [Windows research compatibility](https://github.com/TryUniCAD/Kit/actions/runs/43666848649/job/132668016227) passed seventeen cases. Both jobs checked out PR #94 revision `b86f30c7e41abdc3812ada795a193377f6ddd220` explicitly.
The independently registered [CLI conversion/inspection gate](https://github.com/TryUniCAD/Kit/actions/runs/43666848335/job/132668015805) failed twelve kind-classification cases with 617 passes, so PR #119's CI aggregator failed. Research protocol passes do not make that separate PR ready, and they do not verify later PR #94 heads. That failed checkpoint is superseded by the results below; CLI changes remain in PR #119.

At PR #119 head `ffc86c978ebce37b855c9665b08780e311b94ff4`, [Linux research compatibility](https://github.com/TryUniCAD/Kit/actions/runs/43669001024/job/132674633472) passed seventeen cases with one platform skip in 67.10 seconds, and [Windows research compatibility](https://github.com/TryUniCAD/Kit/actions/runs/43669001024/job/132674633505) passed seventeen in 80.96 seconds. Both still pinned PR #94 `b86f30c7e41abdc3812ada795a193377f6ddd220`. The [conversion/inspection gate](https://github.com/TryUniCAD/Kit/actions/runs/43669001060/job/132674633067) passed all 639 cases in 381.82 seconds and the [CI aggregator](https://github.com/TryUniCAD/Kit/actions/runs/43668999659/job/132674630942) passed. This removes the earlier failed-gate blocker at that checkpoint. Compatibility with later PR #94 revisions still needs a pin refresh and rerun in PR #119; no CLI implementation is added here.
