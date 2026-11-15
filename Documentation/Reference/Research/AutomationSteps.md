# Research automation implementation steps

## Status and ownership

This register belongs to the [neutral-first plan](AutomationPlan.md).
A01 is complete as a source-backed contract and capability audit.
**Current work: A02d capture evidence, A04c semantic qualification, A05 semantic qualification, A08b/A08c/A08e worker implementation and A14b regression evidence.**
A05a reader integration and A08a supervisor process gates passed at `c1c3fcce5b8b67373113ec44ad5d122a52bd7260`.
A05 semantic qualification continues on saved archives. Fresh native measurement and editable acceptance remain open.
The current request authorizes remaining deterministic work in dependency order on [PR #94](https://github.com/TryUniCAD/Kit/pull/94).
A04a–A04b and A03e are verified at code checkpoint `eba0ab488a6a00e2a31fd5ed8ab0bee564b371db`.
The work is published on the shared PR head.
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
| A04 | SOLIDWORKS → neutral reader integration                | A01, A02a                            | jdharcourt | active   | Initial sketches and feature variants preserve required semantics and report unresolved records accurately                                                                                                                         |
| A05 | Fusion → neutral reader integration                    | A01, A02a                            | Stephen316 | active   | Equivalent initial designs serialize through the same contract with independently supported meaning                                                                                                                                |
| A06 | Semantic graph comparison                              | A02c, A04, A05                       | Unassigned | planned  | Equal, intentionally different and ambiguous paired cases report correctly without broad identity masking                                                                                                                          |
| A07 | Bounded deterministic inference and priority scheduler | A03, A06                             | Codex A07  | blocked  | Real shared gaps yield traceable hypotheses, counterexamples and affected-file rescans without models                                                                                                                              |
| A08 | Controlled sample and trace workers                    | A02b, A03                            | jdharcourt | active   | Exact recipes and versioned receipts work with healthy controls; absent workers block only dependent jobs                                                                                                                          |
| A09 | Scoped field maps and typed codec candidates           | A07                                  | Unassigned | planned  | Solved pad-then-pad family is reproduced without model calls, with independent proof and zero donor blocks                                                                                                                         |
| A10 | Optional model investigation packets                   | A08a, A07, A09                       | Unassigned | planned  | Models-off operation, fixed two-step escalation, a failure log, repeat-failure start-step routing, validated responses, cost limits and false-proposal rejection verified                                                          |
| A11 | Portable neutral → Fusion writer                       | A01, A06, A09                        | Unassigned | planned  | Qualified portable graphs generate native files without source replay, proprietary runtime or opaque replacements                                                                                                                  |
| A12 | Portable neutral → SOLIDWORKS writer                   | A01, A06, A09                        | Codex      | blocked  | Qualified portable graphs generate native files from understood fields and reject unsupported required semantics                                                                                                                   |
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

A07's [deterministic inference and queue implementation](../../Changes/Research/Controller/DeterministicInference.md)
passed [hosted process verification](https://github.com/TryUniCAD/Kit/actions/runs/43763760551/job/132964230460)
on saved discovery archives at `ebe6130c`. Qualified A06 paired evidence
remains required for full acceptance.

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
| A02d     | Independent qualification and holdout ancestry              | blocked  | [Audit verifies 74 native files and ten receipts](../../Changes/Research/PairedCaptureLineageAudit.md). [Fresh SOLIDWORKS readback](../../Changes/Research/Workers/SolidWorksQueuedReadback.md) observed all P01, P03 and P04 discovery files. [Fusion fresh-process evidence](../../Changes/Research/FusionReadback/FusionFreshProcessEvidence.md) still needs a native run. P05 stays reserved for holdout |

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
| A04c     | Initial profile and variant semantic qualification   | A04a, A04b; independent source evidence | jdharcourt | active   | The [P04 sketch reader](../../Changes/Research/Readers/SolidWorksSketchGeometry.md) matches 66 dimensions, 88 axis bindings and eleven coincidences. The [P04 list replay](../../Changes/Research/Readers/SolidWorksResolvedEntry.md) verifies the cap, termination and depth. The [P01/P03 replay](../../Changes/Research/Readers/SolidWorksRectangularPlaneEvidence.md) verifies both YZ supports, signed boss geometry and the ordered operands of 28 dimensions, 56 line-axis relations and fourteen coincidences. The [public reader](../../Changes/Research/Readers/SolidWorksPublicSketchSupport.md) resolves ordinary P01/P03 placement from the saved typed support. The P03 boss reader retains the exact profile, direction and depth source, including the 10 mm depth on the inch-display capture. The public rectangle reader retains [saved axis relations and origin coincidence](../../Changes/Research/Readers/SolidWorksPublicSketchGeometry.md). The ordinary P04 reader follows the [saved centering dependency slots](../../Changes/Research/Readers/SolidWorksCutCentering.md) to both resolved sketch owners. The [P04 outer rectangle and Boss](../../Changes/Research/Readers/SolidWorks/SolidWorksOuterRectangle.md) retain the two source streams and the authored dimensions. The [public cut record](../../Changes/Research/Readers/SolidWorks/SolidWorksCutOperation.md) preserves the resolved target and termination. The [cut perimeter and saved face](../../Changes/Research/Readers/SolidWorks/SolidWorksCutFacePlacement.md) now enter the normal neutral document. The [CutSketch constraints](../../Changes/Research/Readers/SolidWorks/SolidWorksCutDimensionRoles.md) retain their ordered operands and distinguish driving sizes from equation-owned offsets. The [active partition](../../Changes/Research/Readers/SolidWorks/SolidWorksActivePartition.md) supplies the saved SOLIDWORKS body and its topology. Independent editable acceptance remains open |

The [reader guide](SolidworksResearchReader.md) defines the command and its research-only receipt.
A04a–A04b do not close A04c or qualify native conversion.
The reader does not infer missing constraints, repair the SDK mappings, launch applications or execute models.
A04c needs independent source inventories and distinguishing evidence rather than agreement with the same reader.
The [configuration replay](../../Changes/Research/Readers/SolidWorksConfigPresentation.md) derives length units, views, dimension styles, table and label settings, geometric tolerance frames, environment, views, managers and inline regions through the final part fields. The [packaged configuration map](../../Changes/Research/Readers/SolidWorksOrdinaryConfigMap.md) opens the ordinary resolved list through its saved counter. The [packaged plane reader](../../Changes/Research/Readers/SolidWorksArchivePlaneRefs.md) reads typed local components, placements and principal datums on the shared archive cursor. All fourteen P01/P03 sources reached the profile boundary and preserved their saved datum IDs and axes. Hosted API coverage checks the neutral support and its raw four-byte provenance. The [sketch presentation replay](../../Changes/Research/Readers/SolidWorksSketchRegionRecords.md) follows all 36 sketch bodies through counted displays and the region return.
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
| A05c     | Initial profile and variant semantic qualification                 | A05a, A05b; independent source evidence | Stephen316 | active   | The [P01 rectangle replay](../../Changes/Research/Readers/FusionRectangleSketchEvidence.md) verifies six plane and operand sets. The [P03 boss replay](../../Changes/Research/Readers/FusionBossProfileEvidence.md) binds eight bosses to measured loops and [signed directions](../../Changes/Research/Readers/FusionBossDirectionEvidence.md). P04 replay verifies [selected contours](../../Changes/Research/Readers/FusionCutSketch/FusionCutProfileEvidence.md), [boss-edge projections](../../Changes/Research/Readers/FusionCutProjectionEvidence.md), [center expression bindings](../../Changes/Research/Readers/FusionCutSketch/FusionCutCenterEvidence.md) and ownership of [110 relations and 66 dimensions](../../Changes/Research/Readers/FusionCutSketch/FusionCutRelationEvidence.md). The partial reader carries [44 saved cap-edge projections](../../Changes/Fusion/Adapter/FusionSavedCapRim.md) and the [saved Cut result topology](../../Changes/Fusion/Adapter/FusionSavedCutBody.md) over eleven variants. Fresh native readback and editable acceptance remain open |

The [reader guide](FusionResearchReader.md) defines the command, its run summary and its research-only receipts.
A05a uses the strict SDK reader first and accepts the partial legacy reader only with an explicit option.
A05a does not close A05b or A05c or qualify native conversion.
A05c needs independent source inventories and distinguishing evidence rather than agreement with the same reader.
The public Fusion partial reader now carries the [saved principal-plane identity](../../Changes/Fusion/Adapter/FusionPrincipalSketchSupport.md) and [signed axis-dimension operand order](../../Changes/Fusion/Adapter/FusionAxisDimensionOrder.md) into the neutral document. The hosted archive step passed all 25 checks at `fa7e92d8`. The partial reader also preserves the [saved point coincidence arguments](../../Changes/Fusion/Adapter/FusionPointCoincidence.md). Its three public-reader cases passed at `011ddb8b`. The latest reader also checks the [saved selected-profile proxy and descriptor](../../Changes/Fusion/Adapter/FusionOwnedProfileSelection.md) for the witnessed P03 and P04 extrusion layouts and projects the [historical P04 cut target body](../../Changes/Fusion/Adapter/FusionCutTargetSelection.md). Those cases passed on `b6ce2ec9`. The [P04 sketch's saved face recipe](../../Changes/Fusion/Adapter/FusionSketchFaceProvenance.md) passed its hosted checks at `f15b9cea`. The partial reader now joins that recipe to the [exact saved face occurrence](../../Changes/Fusion/Adapter/FusionSavedFaceOccurrence.md) on the verified prior body. It reads the [saved blind and through-all cut ends](../../Changes/Fusion/Adapter/FusionSavedCutEnds.md) and retains the [projected origin and center expression operands](../../Changes/Fusion/Adapter/FusionSavedCutCenter.md). All eleven saved P04 controls corroborate these reads. Hosted public checks, fresh licensed readback and editable acceptance remain open. [Hosted archive checks](https://github.com/TryUniCAD/Kit/actions/runs/43728415623/job/132855298357)
See [the change entry](../../Changes/Research/PinnedFusionReader.md).

## A12 SOLIDWORKS writer research

The [generation-19000 writer research](../../Changes/Research/Writers/SolidWorksWriterResearch.md) records evidence for the P03 rectangular blind boss, including the configuration-to-feature join, model header, and Definition notebook boundary.
The saved controls support offline format research while A06 graph qualification and A09 codec evidence remain open.
A12 still needs complete native generation from a qualified portable graph, refusal at the writer boundary, and controlled application evidence.

## Parallel-session child steps

These rows incorporate the [parallel-session design](ParallelSessions.md#delivery).
Their parent identifiers remain stable.
They are not implemented by documenting the rows.

| Child ID | Deliverable                                                                          | Depends on                                           | Owner      | Status   | Exit criterion                                                                                                                                                                                                                                                             |
| -------- | ------------------------------------------------------------------------------------ | ---------------------------------------------------- | ---------- | -------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A08a     | Supervisor, private session directories, pools, controller interface and A03 adapter | A03 technical substeps                               | Stephen316 | complete | Six supervisor process scenarios passed at `c1c3fcce`, alongside fifteen controller scenarios covering counted resources and pool claims                                                                                                                                   |
| A08b     | Headroom, adaptive limits, calibration and grouped small-file sessions               | A08a                                                 | jdharcourt | active   | The [matched Windows sweep](../../Changes/Research/Supervisor/SixteenWorkerCalibration.md#windows-sweep-with-the-warm-claim-helper) completed 320 decodes and held sixteen decoders for 5.681 seconds. The [Linux witness](../../Changes/Research/Supervisor/HostedSupervisorOom.md) verified kernel OOM backoff. Windows passed all 55 cases at [`44217316`](https://github.com/TryUniCAD/Kit/actions/runs/43719771306/job/132829070874). Its [`a5f4b51a` calibration trial](https://github.com/TryUniCAD/Kit/actions/runs/43723299668/job/132839798055) stopped after 3 of 8 serial jobs with `child_did_not_complete`. The fixture now reports bounded terminal worker evidence on failure |
| A08c     | Isolated application authoring, trace and acceptance workers                         | A02b, A08a                                           | jdharcourt | active   | The supervisor recovered acknowledgement of a [licensed P04 readback](../../Changes/Research/Workers/SolidWorksQueuedReadback.md#licensed-job-evidence). The [Fusion queue](../../Changes/Research/Workers/FusionPhaseQueue.md) bounds the restart wait and retains timeout request custody. The [owner archive command](../../Changes/Research/Workers/FusionPhaseAudit.md) preserves a proven unclaimed Phase A probe and releases that probe's quarantine, with archive and refusal cases verified on macOS at `f15b9cea`. The phase audit verified its archived receipt at `32ccaf06`. The owner command can queue one exact archived retry after validating the manifest, parked attempt, retry budget and resource ownership. The [macOS run](https://github.com/TryUniCAD/Kit/actions/runs/43723299668/job/132839798075) verified the Phase A parking repair and both Phase B restart cases. Licensed Fusion dispatch, automatic CAD restart and the unattended pilot remain open |
| A08d     | Installed CLI compatibility, delivered separately in PR #119                         | A03, A04a, A05a, A08a source interfaces              | jdharcourt | active   | PR #119 merged as `249cf7dc`. Its Linux and Windows research compatibility checks pin PR #94 `b86f30c7`. Compatibility with subsequent PR #94 revisions still needs an exact candidate run |
| A08e     | Windows host support for the supervisor and application workers                      | A08a                                                 | jdharcourt | active   | The [licensed Windows queue](../../Changes/Research/Workers/SolidWorksQueuedReadback.md) accepted 25 fresh SOLIDWORKS observations across P01, P03 and P04. Licensed [timeout rearm](../../Changes/Research/Workers/SolidWorks/TimeoutRearm.md#licensed-two-attempt-witness) and [restart replay](../../Changes/Research/Workers/SolidWorks/TimeoutRearmReplay.md#licensed-restart-witness) verified archival, a second native dispatch and the configured attempt limit for P04. Native Fusion execution remains open |
| A10a     | Optional Codex runner and private data boundary                                      | A08a, A07, A09; explicit model-command authorization | Unassigned | planned  | Candidate validation, isolated reads, bounded packets/patch paths and verified runner contracts                                                                                                                                                                            |
| A10b     | Step validation, selector, failure log and start-step routing                        | A10a                                                 | Unassigned | planned  | Separate infrastructure/model failures, exact cache keys, stable packet prefixes, budgets, fallback after a first-step failure and two-failure start-step routing                                                                                                          |
| A10c     | Use report for each model step and route key                                         | A10b, A09                                            | Unassigned | planned  | Recorded attempts, passes, model failures and tokens per pass for each step. The report never changes the selected models                                                                                                                                                  |
| A10d     | Optional Claude API and Claude Code runners                                          | A08a, A07, A09; applicable authorization             | Unassigned | planned  | Provider validation, serving-model attribution, bounded errors and private-data/policy gates                                                                                                                                                                               |
| A14a     | Controller and corpus process gates                                                  | A03 technical substeps                               | jdharcourt | complete | Seven corpus and fifteen controller scenarios passed at `22a59e68`; extend the gate when interfaces change                                                                                                                                                                 |
| A14b     | Reader, comparator and writer regression gates                                       | A04a, A05; A06 for paired gates                      | jdharcourt | active   | Pinned reader/outcome and native-field refusal gates passed at `22a59e68`. The nine [discovery archive reports](../../Changes/Research/DiscoveryArchiveGate.md) and 45 public Fusion reader cases passed in the [hosted archive step](https://github.com/TryUniCAD/Kit/actions/runs/43730082272/job/132860400807) at `f15b9cea`. Paired comparator and writer acceptance still require A06 and independent native evidence |
| A14c     | Batched remote verification receipts                                                 | A03, A09, A14b                                       | jdharcourt | blocked  | The [paired discovery runner](../../Changes/Research/Controller/PairedDiscoveryReplay.md) settled 25 archive pairs in `waiting_ci`. The [paired CI release](../../Changes/Research/Controller/PairedCiBatchRelease.md) and [candidate selector](../../Changes/Research/Controller/PendingCandidateDependencies.md) preserve the exact attempts and provisional dependencies. Further work waits for A09 and A14b completion. Live successful release and per-member failure isolation remain open |
| A15a     | Two-week deterministic operating pilot, with optional enabled model pools            | A07, A08b, A14; A10c/A10d only when enabled          | Unassigned | planned  | Measure elapsed and active agent time, throughput, recovery, blockers, verified capability gains, and any operator intervention. Track model spend when enabled                                                                                                            |

The model pairs do not become runtime requirements for a models-off pilot.
The coordinating agent runs remote CI in batches. See [batched remote verification](AutomationPlan.md#batched-remote-verification).
A08c includes the [always-busy application loop](ParallelSessions.md#application-workers-that-stay-busy): continuous claims, work ahead of decoding, scheduled resets and batch controls.
A08e targets the controller, supervisor and both applications running on one Windows host. The queued SOLIDWORKS P04 readback has run on that host. Native Fusion execution remains open.
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
The P04 configuration-stream investigation links both sketches to resolved feature records in all eleven discovery captures. Licensed baseline A and YZ traces confirm both exact sketch boundaries and show that each profile reads the same live object from the shared map. The production reader still needs the corresponding versioned walk and a decode of the supporting face occurrence. The independent readback verifies the persistent boss face and both sketch transforms in all eleven. [Licensed archive trace](../../../re/solidworks/records/P04SketchResidence.md#licensed-sketch-boundaries-and-resolved-references), [native readback](../../Changes/Research/Workers/SolidWorksCutFaceReadback.md)
At `cdf53e1f`, the discovery reader agreed with all eleven measured native cut terminations. Ten blind cuts had matching neutral depths, including the 5 mm edit. The through-all cut preserved native code 1 and a missing authored depth. Its neutral definition was a native fallback.
At `dd9dfa9b`, the 25-file local discovery census verified the [typed through-all projection](../../Changes/Research/Readers/SolidWorksThroughAllProjection.md) with no authored length. The change leaves native reconstruction subject to the existing writer gates.
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
The earlier Windows calibration completed 100 decodes and fell short of the eight-worker overlap threshold. The subsequent 64-input sweep qualified all five levels, and the hosted cgroup trial verified kernel OOM backoff. [Matched Windows sweep](../../Changes/Research/Supervisor/SixteenWorkerCalibration.md#windows-sweep-with-the-warm-claim-helper), [kernel OOM witness](../../Changes/Research/Supervisor/HostedSupervisorOom.md)
The corrected `cdf53e1f` Windows and macOS research suites passed 29 and 74 cases respectively. [Windows run](https://github.com/TryUniCAD/Kit/actions/runs/43693322495/job/132748412625), [macOS run](https://github.com/TryUniCAD/Kit/actions/runs/43693322495/job/132748412270)

At `69b9b773`, Windows passed 42 research cases and macOS passed 90, including the recovery and dependency-input process cases. [Windows run](https://github.com/TryUniCAD/Kit/actions/runs/43701120684/job/132772337494), [macOS run](https://github.com/TryUniCAD/Kit/actions/runs/43701120684/job/132772337490)
At `fa7e92d8`, the Windows calibration passed. The claim-group restart fixture failed when its reader and replacement producer opened the same owner barrier pathname. The updated fixture publishes a separate immutable barrier per owner digest. At `b6ce2ec9`, all 55 Windows checks passed, including the updated fixture. [Earlier Windows research job](https://github.com/TryUniCAD/Kit/actions/runs/43725708342/job/132847061624), [passing Windows research job](https://github.com/TryUniCAD/Kit/actions/runs/43728415623/job/132855298282)
At `f15b9cea`, macOS passed 94 worker checks with one Linux-only skip, including the owner archive and its restart replay. Linux passed all 58 supervisor checks at `f15b9cea`. [macOS research job](https://github.com/TryUniCAD/Kit/actions/runs/43730082272/job/132860400795), [Linux research job](https://github.com/TryUniCAD/Kit/actions/runs/43730082272/job/132860400807)
At `8b65c015`, macOS again passed 94 worker checks with one Linux-only skip, including the archived Fusion retry. The Windows calibration sweep passed, while two ownership fixtures required restoration of the member-list interface. The follow-up restores that callable through a complete checked native list. [macOS retry](https://github.com/TryUniCAD/Kit/actions/runs/43733838789/job/132871965585), [Windows sweep and ownership cases](https://github.com/TryUniCAD/Kit/actions/runs/43733838789/job/132871965525)
At `3d683585`, hosted native archive and read/write checks passed. The pre-pilot activity report passed its process fixture on Linux, Windows and macOS. The Windows job passed 56 cases, macOS passed 95 with one Linux-only skip, and Linux passed all 58 supervisor checks. [Hosted workflow](https://github.com/TryUniCAD/Kit/actions/runs/43739105328)
At `62853433`, the Linux archive gate passed 162 cases, the native read/write gate passed 350 with 159 skips, and the supervisor passed 58. macOS passed 97 with one Linux-only skip, including the between-job restart and startup fence checks. Windows passed 61 and failed the single timeout-link case. Its rerun checks single cancellation publication and preserves the first attempt's terminal diagnosis. [Linux job](https://github.com/TryUniCAD/Kit/actions/runs/43743507082/job/132901634724), [macOS job](https://github.com/TryUniCAD/Kit/actions/runs/43743507082/job/132901634705), [Windows job](https://github.com/TryUniCAD/Kit/actions/runs/43743507082/job/132901634428)
At `a006c275`, Windows passed all 64 supervisor checks, including first-attempt timeout linkage and failure to publish cancellation. macOS passed 97 with one Linux-only skip. Linux passed 163 archive checks, 350 native read/write checks with 159 skips, and all 58 supervisor checks. [Hosted workflow](https://github.com/TryUniCAD/Kit/actions/runs/43745878592)
Legacy no-owner controller calls and custom adapters without the fence capability remain explicitly unfenced.

A08c's five [durable-output intake](../../Changes/Research/Workers/DurableWorkerOutputs.md) cases passed on all three platforms.
The twelve [application transport/publication](../../Changes/Research/Workers/LocalApplicationDispatch.md) cases passed Linux/macOS.
Windows passed both unsupported-application parking cases and all four [immutable-record](../../Changes/Research/Workers/WindowsImmutableRecords.md) cases.
The revised sharing case proves refusal through CRT and native APIs plus successful same-path operations after handle release; successful pytest capture did not retain individual numeric error values.
These fixtures did not call native CAD APIs.
Licensed Fusion execution, automatic Fusion startup and CAD restart, batch resets and unattended operation remain open.
Completed and abandoned application spools stay retained until owner verification of actual controller acceptance; the completed-spool bound is 32 files and 520 MiB, not an OS write quota.

A04c records [hashed principal support candidates](../../Changes/Research/PrincipalSupportEvidence.md) for 25 measured identifiers, including three YZ variants.
Licensed traces resolve the principal-plane class in four captures and locate the enclosing profile transform in both traced YZ rectangle profiles. The public reader binds the P01/P03 support records and the later typed P04 face support and constraints. [Licensed loader observations](../../../re/solidworks/records/PrincipalSupportCandidates.md#licensed-loader-observations), [P04 face support](../../Changes/Research/Readers/SolidWorks/SolidWorksCutFacePlacement.md)
The [native-field refusal](../../Changes/Research/Readers/NativeFieldWriteRefusal.md) and [writer qualification](../../Changes/Research/Readers/NativeSemanticWriteQualification.md) regressions passed, preserving required-semantic refusal and destinations through real public/direct boundaries.
The full Fusion run also verifies the corrected explicit/inferred writer-ordering cases.
None of those refusals supplies the missing positive native qualification.

A02d still needs a licensed Fusion run. The documented Fusion bridge refused connections and initial native UI initialization failed. The Windows host completed fresh owned SOLIDWORKS sessions for six P01 and eight P03 files and for all eleven P04 files. The queue recorded passing controls, an unchanged source roster, an observed process exit and acknowledgement for both discovery sets. [Licensed discovery readback](../../Changes/Research/Workers/SolidWorksQueuedReadback.md)
[Fresh-process readback](../../Changes/Research/FusionReadback/FusionFreshProcessEvidence.md) now pins every committed Fusion variant, and [observation-local bindings](../../Changes/Research/FusionSketchBindingCapture.md) are implemented; a native run is still required to close provenance, observation binding and load diagnostics.
P05 stays reserved for holdout. Zero native pairs are qualified.
A06 waits for qualified A02d/A04c/A05c evidence. The [P01 and P03 archive comparison](../../Changes/Research/Readers/Comparison/RectangularPairEvidence.md) matches all fourteen principal perimeters, twenty-eight dimension sizes, and eight signed blind Boss displacements while preserving the tools' dimension and profile declarations. The [P04 archive comparison](../../Changes/Research/Readers/Comparison/ArchivedCutHistory.md) joins each Cut to its target and support on the earlier extrusion. All eleven pairs agree on the saved solid measurements, perimeter edges, Cut support plane, and compared extent fields. Fusion uses a midpoint with driving expressions, and SOLIDWORKS uses derived perimeter offsets. The hosted discovery gate includes blind versus through-all and an ambiguous edge control. A07/A09 and both native writers retain their declared dependencies.
The [A11 origin-coincidence probe](../../Changes/Fusion/Authoring/FusionOriginCoincidenceProbe.md) generates a rectangle with a distinct sketch origin and verifies the archived constraint operands and observer slots against fourteen controls. The [sketch-owned dimension probe](../../Changes/Fusion/Authoring/FusionOwnedDimensionProbe.md) generates two direct driving parameters without global duplicates and compares their saved links with six P01 captures. Licensed opening, independent dimension edits, rebuild, restoration and reopen remain pending.

The [A07 signed depth search](../../Changes/Research/Inference/FusionSignedDepthSearch.md) replayed all eight P03 Fusion saves. Signed little-endian float64 centimetres matched both typed locations. The [affected replay](../../Changes/Research/Inference/FusionDepthAffectedReplay.md) queued one A03 rescan when the signed hypothesis changed to magnitude-only. Seven save predictions stayed unchanged. Which copy controls rebuild remains open.

The [A09 two-pad capture draft](../../Changes/Research/Writers/SolidWorksTwoPadDiscovery.md) compiled a licensed discovery grid with two blind bosses and the upper sketch bound to the lower boss's top face. The draft is preserved in Git. A09 awaits A07 completion and a clean licensed desktop for capture.

The [A12 rectangle field synthesis](../../Changes/Research/Writers/SolidWorksRectangleFieldSynthesis.md) regenerated 114 field spans across six P01 saves. The [sketch style replay](../../Changes/Research/Writers/SolidWorksSketchStyleFields.md) generated 60 visual records and widths. The [part bookkeeping emitter](../../Changes/Research/Writers/SolidWorksPartBookkeeping.md) independently constructed and read back a metadata container. Reference allocation, the remaining configuration streams and complete native part generation remain open.

The [A04c licensed support replay](../../Changes/Research/Readers/SolidWorks/SolidWorksLicensedCutSupport.md) matched the saved support owner, plane and visible cap area to both native observation phases on all eleven P04 parts. The [licensed sketch replay](../../Changes/Research/Readers/SolidWorks/SolidWorksLicensedCutDimensions.md) matched 132 dimension values and roles, 44 centering equation assignments, 264 ordered dimension attachment slots and 330 sketch relations.

The [A04c face producer census](../../Changes/Research/Readers/SolidWorks/SolidWorksCensusFaceProducer.md) matched all 768 comparisons in the 25-file discovery report at `d5102489`. It reports `BlindBoss` for all eleven P04 cut supports. Hosted verification of the updated check is pending.

The [A08b grouped settlement change](../../Changes/Research/Supervisor/GroupedAdaptiveSettlement.md) excludes a physical worker group from adaptive capacity decisions when the controller fences every member's completion. The existing Linux and macOS group selection covers the added generation-change scenario. Hosted verification is pending.

The [Fusion restart intent](../../Changes/Research/Workers/FusionOwnerRestart.md) binds the accepted Phase A result, cleared acknowledgement, retained fence and exact earlier process. The [main-thread readiness grant](../../Changes/Research/Workers/FusionRestartReadiness.md) verifies an idle Fusion process with zero open documents before issuance and consumption. The [exit observer](../../Changes/Research/Workers/FusionQuitObserver.md) records the exact owned macOS process exit under that fence. Its first hosted run passed the disappeared and mismatched peer cases and failed four arming scenarios. The fixture now preserves the observer's failure output. The [owner-directed replacement](../../Changes/Research/Workers/FusionReplacementLaunch.md) submits one exact-bundle launch request, records the new process, and separately checks accepted Phase B evidence on that same process. A [disposable AppKit witness](../../Changes/Research/Workers/AppKitQuitDelegateWitness.md) covers normal quit acceptance and cancellation. Hosted verification of the new fixtures, automatic graceful quit and signed-in Fusion verification remain open. The [hosted paired archive receipt](../../Changes/Research/Controller/HostedPairedArchiveGate.md) records the exact tested tree and the public discovery gate when that workflow step succeeds.
The supplemental two-body scope control holds the Cut geometry fixed across automatic selection, explicit A, and explicit A+B. The [provisional SOLIDWORKS archive replay](../../Changes/Research/Workers/SolidWorks/ProvisionalScopeArchive.md) follows two saved bodies to their separate earlier Boss producers and the shared scope word. The [Fusion phase queue](../../Changes/Research/Workers/FusionPhaseQueue.md) accepts the fixed scope plan. The Windows commissioning run kept Phase A in `waiting_application` and Phase B in `waiting_evidence`, with the controller database unchanged by its audit. Complete native runs still need their licensed applications. [SOLIDWORKS scope control](../../Changes/Research/Workers/SolidWorks/ThroughAllScopeControl.md), [Fusion scope control](../../Changes/Research/FusionReadback/FusionScopeControl.md)
A13 needs native editable acceptance. The [A15 activity report](../../Changes/Research/Supervisor/OfflinePilotEventReport.md) replays recorded controller activity to a fixed cutoff. The [private pre-pilot report](../../Changes/Research/Supervisor/PrivatePilotEvidence.md) replays the same window with separately attested operator interventions, measured agent intervals and independent acceptance evidence. A local read of the licensed timeout controller preserved the ledger bytes and reported these absent sources as unmeasured. The two-week A15 pilot has not started.
The archived evidence replays and licensed readbacks above used their pinned inputs. Automated test suites run in hosted CI.

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

At PR #119 head `ffc86c978ebce37b855c9665b08780e311b94ff4`, [Linux research compatibility](https://github.com/TryUniCAD/Kit/actions/runs/43669001024/job/132674633472) passed seventeen cases with one platform skip in 67.10 seconds, and [Windows research compatibility](https://github.com/TryUniCAD/Kit/actions/runs/43669001024/job/132674633505) passed seventeen in 80.96 seconds. Both still pinned PR #94 `b86f30c7e41abdc3812ada795a193377f6ddd220`. The [conversion/inspection gate](https://github.com/TryUniCAD/Kit/actions/runs/43669001060/job/132674633067) passed all 639 cases in 381.82 seconds and the [CI aggregator](https://github.com/TryUniCAD/Kit/actions/runs/43668999659/job/132674630942) passed.

PR #119 merged into `main` at `249cf7dcde6197c41fafb052eda8afb210bcf49e`. Synchronizing PR #94 brings in that implementation and retains both sets of hosted checks. The next compatibility run selects the installed CLI and a separate research checkout at the workflow candidate SHA on Linux and Windows. A merge-queue shard uses the same checkout rule when it selects research CLI cases. [CLI delivery](https://github.com/TryUniCAD/Kit/pull/119), [candidate compatibility](../../Changes/Commands/ResearchCandidateCompatibility.md)

The two compatibility jobs for `a006c275` independently checked the installed CLI and isolated research checkout at the workflow merge SHA `8d66aa9b38bb3f436678cdad6af3206d0189fb51`. Linux passed 27 with one Windows-only skip and Windows passed 17. [Linux](https://github.com/TryUniCAD/Kit/actions/runs/43745878592/job/132908934845), [Windows](https://github.com/TryUniCAD/Kit/actions/runs/43745878592/job/132908934840)
