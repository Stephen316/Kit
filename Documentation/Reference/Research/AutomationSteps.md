# Research automation implementation steps

## Status and ownership

This register belongs to the [neutral-first plan](AutomationPlan.md).
A01 is complete as a source-backed contract and capability audit.
**Current work: A02d capture evidence, A04c semantic qualification, A05 exact outcomes and A08b/A08c/A08e worker implementation.**
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

| Child ID | Deliverable                                                                          | Depends on                                           | Owner      | Status   | Exit criterion                                                                                                                                                                                                                                               |
| -------- | ------------------------------------------------------------------------------------ | ---------------------------------------------------- | ---------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| A08a     | Supervisor, private session directories, pools, controller interface and A03 adapter | A03 technical substeps                               | Stephen316 | complete | Six supervisor process scenarios passed at `c1c3fcce`, alongside fifteen controller scenarios covering counted resources and pool claims                                                                                                                     |
| A08b     | Headroom, adaptive limits, calibration and grouped small-file sessions               | A08a                                                 | jdharcourt | active   | Adaptive upward adjustment passed macOS at `e0d79125`; grouped/application transport passed at `3327f7fe`; all seventy-four macOS cases, including calibration, owner recovery and launch gating, passed at `2ff96767`. Current Linux reruns remain checking |
| A08c     | Isolated application authoring, trace and acceptance workers                         | A02b, A08a                                           | jdharcourt | active   | Durable output intake passed macOS/Windows at `e0d79125` and Linux at `95b3f2e4`; twelve application transport cases passed macOS at `3327f7fe`. Native dispatch, automatic restart, downstream bindings and unattended operation remain open                |
| A08d     | Installed CLI compatibility, delivered separately in PR #119                         | A03, A04a, A05a, A08a source interfaces              | jdharcourt | active   | PR #119 head `ffc86c97` passed Linux/Windows research compatibility against PR #94 `b86f30c7`, all 639 conversion/inspection cases and CI Agg. Later PR #94 heads remain outside that pinned evidence                                                        |
| A08e     | Windows host support for the supervisor and application workers                      | A08a                                                 | jdharcourt | active   | Windows passed all twenty-two cases at `7e6243b2`, including owner recovery, both parking cases and all four immutable-record cases. Native Windows dispatch remains open                                                                                    |
| A10a     | Optional Codex runner and private data boundary                                      | A08a, A07, A09; explicit model-command authorization | Unassigned | planned  | Candidate validation, isolated reads, bounded packets/patch paths and verified runner contracts                                                                                                                                                              |
| A10b     | Step validation, selector, failure log and start-step routing                        | A10a                                                 | Unassigned | planned  | Separate infrastructure/model failures, exact cache keys, stable packet prefixes, budgets, fallback after a first-step failure and two-failure start-step routing                                                                                            |
| A10c     | Use report for each model step and route key                                         | A10b, A09                                            | Unassigned | planned  | Recorded attempts, passes, model failures and tokens per pass for each step. The report never changes the selected models                                                                                                                                    |
| A10d     | Optional Claude API and Claude Code runners                                          | A08a, A07, A09; applicable authorization             | Unassigned | planned  | Provider validation, serving-model attribution, bounded errors and private-data/policy gates                                                                                                                                                                 |
| A14a     | Controller and corpus process gates                                                  | A03 technical substeps                               | jdharcourt | complete | Corpus and twelve controller scenarios passed at `eba0ab48`; extend the gate when interfaces change                                                                                                                                                          |
| A14b     | Reader, comparator and writer regression gates                                       | A04a, A05; A06 for paired gates                      | Unassigned | planned  | Pinned-input process checks plus independent semantic evidence reject unsupported/stale results                                                                                                                                                              |
| A14c     | Batched remote verification receipts                                                 | A03, A09, A14b                                       | Unassigned | planned  | Stage 11 research check, `waiting_ci` candidates, recorded batch artifacts, resumption and dependent invalidation after a failed batch                                                                                                                       |
| A15a     | Two-week deterministic operating pilot, with optional enabled model pools            | A07, A08b, A14; A10c/A10d only when enabled          | Unassigned | planned  | Measure elapsed and active agent time, throughput, recovery, blockers, verified capability gains, and any operator intervention. Track model spend when enabled                                                                                              |

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

A02d remains blocked: the implementation host refused connections to the documented Fusion bridge, and native UI initialization failed. A later read-only app inventory exposed neither Fusion nor SOLIDWORKS; no native run was attempted from that inventory.
The [fresh capture binding change](../../Changes/Research/FusionSketchBindingCapture.md) adds pinned observation-local constraint and dimension references.
Both preparation cases passed remotely at `480d9d3a`; all seven corpus/preparation cases passed again at `95b3f2e4`. No native run or new qualified pair is claimed.
P04 supporting-face identity and unsupported or unresolved bindings remain open.

A04c now records [hashed principal support candidates](../../Changes/Research/PrincipalSupportEvidence.md).
The new gate requires 25 measured plane identifiers, including three YZ variants.
The records remain unqualified until native class ownership and the opaque tag domain are established.

A08b adds [bounded logs and restart cleanup](../../Changes/Research/Supervisor/BoundedSessionLogs.md), with eight supervisor scenarios passed at `480d9d3a`.
CPU/memory admission and sampled group-memory stops passed all eleven Linux supervisor scenarios at `b86f30c7`.
It does not close adaptive capacity, calibration, grouped jobs, application workers or Windows support.
A08b now also implements [version-scoped memory estimates](../../Changes/Research/Supervisor/VersionedMemoryEstimates.md).
The [macOS gate at `91d90628`](https://github.com/TryUniCAD/Kit/actions/runs/43667302609/job/132669499511) passed all fourteen process cases in 132.47 seconds, including five-observation learning, restart/new-version isolation, a 55-session rolling-window check and invalid-history refusal before claims. The [Linux workflow-quality gate at `91d90628`](https://github.com/TryUniCAD/Kit/actions/runs/43667302609/job/132669499653) also passed all fourteen supervisor cases in 115.51 seconds, fifteen controller cases, seven corpus/preparation cases, three SOLIDWORKS reader cases and five Fusion cases against the unchanged exact-outcome baseline. Its native/API/registry stage passed 203 cases with 159 unavailable-corpus/platform skips. The CI aggregator passed at that head; remaining review findings still block readiness. [Adaptive concurrency](../../Changes/Research/Supervisor/AdaptivePoolLimits.md) is implemented. The macOS gate at `e0d79125` passed its five additional cases, including an actual measured upward branch. Its minimum-capacity deadline case recorded a reduction request without a numeric decrease. Linux execution remains open. [Optional grouped sessions](../../Changes/Research/Supervisor/GroupedSmallFileSessions.md) now implement 2–20 logical jobs with independent leases, counted resources, output manifests and durable single-job retries in one physical process. Fourteen grouped process cases passed macOS at `3327f7fe`; Linux verification and Windows grouped qualification remain open. Source review also found that an orphaned in-flight controller can publish claims after restart recovery scans; the [owner-epoch fence](../../Changes/Research/Workers/SupervisorOwnerEpoch.md) now implements transaction-bound rotation before recovery scans, with all five cases passed on macOS and Windows at `95b3f2e4`; current Linux verification remains open. Legacy no-owner/controller and custom-adapter calls remain explicitly unfenced. The [POSIX launch gate](../../Changes/Research/Supervisor/PosixWorkerLaunchGate.md) now holds worker execution until process metadata is synced and fresh logical leases pass; all five real process cases passed macOS at `95b3f2e4`; current Linux verification remains open. The [standalone offline calibration slice](../../Changes/Research/Supervisor/OfflineDecoderCalibration.md) is implemented with explicit immutable workloads, isolated 1/2/4/8 trials, preserved reserves/resources and fourteen real process cases passed on macOS at `2ff96767`; current Linux verification remains open. No comparable saturated recommendation is established; Windows calibration and independent OOM attribution remain open.
A08e's [Windows gate at `30707236`](https://github.com/TryUniCAD/Kit/actions/runs/43666746526/job/132667719525) passed five cases; descendant completion retried after an exit status of 1 in 10.366 seconds. Source inspection identified an invalid launcher/interpreter PID equality in the fixture. The repair binds the observed parent chain and proves private Job Object membership.
The [Windows gate at `91d90628`](https://github.com/TryUniCAD/Kit/actions/runs/43667302609/job/132669500211) then passed all six process cases in 20.22 seconds, including descendant completion and crash recovery. Windows supervision is verified at that checkpoint; application-worker execution on Windows remains open under A08c/A08e.
The [macOS gate at `35080cec`](https://github.com/TryUniCAD/Kit/actions/runs/43666501725/job/132666944085) passed all eleven POSIX process cases in 75.81 seconds.
At `35080cec`, the affected native/API/registry stage passed 188 cases with 159 existing unavailable-corpus skips; seven corpus/preparation and three SOLIDWORKS reader cases also passed before the run was superseded. Those completed steps do not make its cancelled overall job green.
A08c owns the [durable declared-output intake](../../Changes/Research/Workers/DurableWorkerOutputs.md) prerequisite: session cleanup must not remove native outputs before a current-lease completion stores their verified artifacts. The [macOS gate at `e0d79125`](https://github.com/TryUniCAD/Kit/actions/runs/43669741073/job/132676916901) passed twenty-four cases in 235.59 seconds, including five output-intake and five adaptive-capacity scenarios. The [Windows gate at that head](https://github.com/TryUniCAD/Kit/actions/runs/43669741073/job/132676916918) passed all eleven cases in 49.13 seconds, verifying the corrected reparse flag owner and enabling adaptive configuration. The [Linux gate](https://github.com/TryUniCAD/Kit/actions/runs/43669741073/job/132676916864) passed 293 native/API/registry cases with 159 unavailable-corpus/platform skips, then passed 28 and failed three focused native caller cases; later research stages did not run. The path policy also rejected a gotcha filename containing digits. Source repairs rename that file, retain the filtered source's actual capabilities, and refuse FreeCAD extrusion profiles whose closed-profile/topology proof is absent. The repaired [native semantic write qualification](../../Changes/Research/Readers/NativeSemanticWriteQualification.md) cases passed in the later 327 native and 31 carrier selections recorded below. These partial successes do not establish a green current-head CI aggregator. At `6fb599a9`, Windows passed eleven existing cases and rejected two new parking fixtures for a resource-map/label-array mismatch; the fixture is repaired. Its installed-wheel gate also exposed a guard/Fusion-adapter import cycle, repaired by deferring the contract encoder import until evaluation. Current-head reruns remain required.
The [pinned local Fusion dispatcher](../../Changes/Research/Workers/LocalApplicationDispatch.md) now implements fresh main-thread control probes, fixed trusted capture entry points, private output staging, accepted phase-A dependency binding and explicit external-owner restart handoffs. Its twelve remote transport/publication cases passed macOS at `3327f7fe`; Linux output/application stages passed at `95b3f2e4`. Completed and abandoned application spools remain retained until owner verification of actual controller acceptance; one outstanding spool fences further admission. The completed-spool limit is 32 files and 520 MiB, not an OS write quota. Native execution, automatic restart, automatic acceptance acknowledgement, downstream binding publication, batch resets and the unattended pilot remain open. No captured native pair or Windows native counterpart is qualified by this source work.
At `6e2da255`, the [installed-wheel gate](https://github.com/TryUniCAD/Kit/actions/runs/43673027311/job/132687036363) passed and [Linux](https://github.com/TryUniCAD/Kit/actions/runs/43673027349/job/132687037643) passed 136 policy and 323 native cases with 159 existing skips before three new part-authoring fixtures failed during state construction. The unsupported native-tag contract exception is removed rather than broadening the state allowlist; a working cuboid positive and explicit part-state refusal retain the actual scope. The [macOS job](https://github.com/TryUniCAD/Kit/actions/runs/43673027349/job/132687037442) ran no process cases because a duplicate unpackaged pytest basename blocked collection; the new grouped file is renamed without removing either selection. [Windows](https://github.com/TryUniCAD/Kit/actions/runs/43673027349/job/132687037854) passed eleven existing cases but both parking jobs returned `rejected`; diagnostics now retain their exact controller reason for the next run. None of these failures is treated as completed verification.
The [macOS gate at `3327f7fe`](https://github.com/TryUniCAD/Kit/actions/runs/43673846094/job/132689552836) passed all fifty process cases in 382.80 seconds, including fourteen grouped cases and twelve application protocol/publication cases. This verifies the source checkpoint's bounded group handling, retained-spool recovery and atomic record transport through real processes. High host load blocked the adaptive upward branch at that run; the earlier measured `e0d79125` branch remains separate evidence. No native application call ran in those transport fixtures. Its Windows gate retained eleven passes and two parking failures, and a new CI gotcha exceeded the 32-file direct-directory limit; the gotcha is moved into `Ci/Collection`. The corrected local path policy passes all 506 changed destinations. That checkpoint predates the successful owner and launch-gate macOS run recorded below; current-head reruns remain required.
The completed [Linux stages at `3327f7fe`](https://github.com/TryUniCAD/Kit/actions/runs/43673846094/job/132689553051) passed 327 native/API/registry cases with 159 existing skips, 31 typed-carrier boundary cases, seven corpus/preparation cases, three SOLIDWORKS reader cases, seventeen output/application cases and five Fusion cases against the unchanged exact 714-file baseline. The job was cancelled during controller verification, so no current controller/supervisor or overall green result is inferred. The [Windows gate at `95b3f2e4`](https://github.com/TryUniCAD/Kit/actions/runs/43674626489/job/132692019085) passed sixteen and failed two in 71.74 seconds, with all five owner cases passing. Both parking errors were `application input changed while reading`. Pinned CPython source identifies different path/handle ctime meanings; the [protected Windows read repair](../../Changes/Research/Workers/WindowsImmutableRecords.md) retains handle ChangeTime checks, uses shared path identity fields and adds four real record cases. Current-head execution remains required.
The [macOS gate at `95b3f2e4`](https://github.com/TryUniCAD/Kit/actions/runs/43674626489/job/132692019027) passed all sixty cases in 419.41 seconds, including the five launch and five recovery-owner cases. [Linux at that head](https://github.com/TryUniCAD/Kit/actions/runs/43674626489/job/132692018859) completed all native, carrier, corpus, reader, output and fifteen controller cases, then passed forty-two supervisor cases and failed `CheckRestart`: metadata visibility now precedes worker entry, so its bootstrap could safely exit before recovery. The fixture repair waits for an actual PID-bound worker-entry marker and preserves every live-orphan/bystander assertion; hold-rebinding cases use the same phase distinction. The [broader Fusion run](https://github.com/TryUniCAD/Kit/actions/runs/43674626437/job/132691958526) passed 2,958 cases with three skips and failed one caller expecting writer lookup before required-semantic refusal. Separate actual-history refusal and typed missing-writer cases now retain both requirements. None of these repairs is treated as a green current-head gate before rerun.
At `2ff96767`, the [macOS gate](https://github.com/TryUniCAD/Kit/actions/runs/43676632437/job/132698100852) passed all seventy-four process cases in 501.85 seconds, including all fourteen standalone calibration scenarios. Host load prevented the adaptive upward branch at this checkpoint; the earlier `e0d79125` observation remains separate evidence. The calibration fixtures prove constrained-trial reporting, refusal and cleanup, not a saturated throughput recommendation. The [Windows gate](https://github.com/TryUniCAD/Kit/actions/runs/43676632437/job/132698100644) passed twenty-one and failed one in 70.20 seconds. Both previously failing application parking cases now passed, as did rewritten-record identity, metadata-only mutation refusal and unsafe-path refusal. The remaining sharing fixture had every mutation raise `OSError` but required native WinError codes even for the CRT file writer; its error-domain assertion is repaired with explicit native probes and post-release controls, pending remote execution. This is partial stage evidence, not an overall green Windows gate. The configured review did not finish at that checkpoint and supplied no matching approval.

At source checkpoint `7e6243b28ea5d84de2c8aea7577221c24b13ceb0`, the [Windows gate](https://github.com/TryUniCAD/Kit/actions/runs/43677583943/job/132701013861) passed all twenty-two cases in 64.92 seconds, including the revised sharing refusal and same-path post-release controls. Successful pytest capture did not retain individual error values; the assertions prove the required error domains. All forty-one reported review threads are resolved, but the configured native reports are failed, one reports that review did not finish, and there is no approval for that checkpoint. The [macOS gate](https://github.com/TryUniCAD/Kit/actions/runs/43677583943/job/132701013633) passed all seventy-four process cases in 500.72 seconds. The [Fusion archive gate](https://github.com/TryUniCAD/Kit/actions/runs/43677583852/job/132701052081) passed 2,959 cases with three existing skips and failed one incorrect inferred-writer expectation. The repair preserves explicit native-semantic refusal, inferred missing-writer refusal and an additional inferred JSON semantic refusal; no production guard is relaxed. This does not establish overall CI or merge-group acceptance.

A02d preparation now pins every committed Fusion variant for restarted-process readback; native execution remains blocked. A06 waits for qualified A02d/A04c/A05c evidence; A07/A09 and the native writers retain their declared dependencies. Offline transport or exact reader outcomes do not satisfy those semantic prerequisites.
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
The independently registered [CLI conversion/inspection gate](https://github.com/TryUniCAD/Kit/actions/runs/43666848335/job/132668015805) failed twelve kind-classification cases with 617 passes, so PR #119's CI aggregator failed. Research protocol passes do not make that separate PR ready, and they do not verify later PR #94 heads. That failed checkpoint is superseded by the results below; CLI changes remain in PR #119.

At PR #119 head `ffc86c978ebce37b855c9665b08780e311b94ff4`, [Linux research compatibility](https://github.com/TryUniCAD/Kit/actions/runs/43669001024/job/132674633472) passed seventeen cases with one platform skip in 67.10 seconds, and [Windows research compatibility](https://github.com/TryUniCAD/Kit/actions/runs/43669001024/job/132674633505) passed seventeen in 80.96 seconds. Both still pinned PR #94 `b86f30c7e41abdc3812ada795a193377f6ddd220`. The [conversion/inspection gate](https://github.com/TryUniCAD/Kit/actions/runs/43669001060/job/132674633067) passed all 639 cases in 381.82 seconds and the [CI aggregator](https://github.com/TryUniCAD/Kit/actions/runs/43668999659/job/132674630942) passed. This removes the earlier failed-gate blocker at that checkpoint. Compatibility with later PR #94 revisions still needs a pin refresh and rerun in PR #119; no CLI implementation is added here.
