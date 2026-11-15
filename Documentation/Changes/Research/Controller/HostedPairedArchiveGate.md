# Observe the hosted paired archive gate

The Linux policy job in `Workflow quality` publishes `PairedArchiveGate-RUN_ATTEMPT` after its existing archive test step passes on a pull request. The receipt records the passing P01/P03 public reader history check and P04 paired cut history check, the GitHub workflow run and attempt, and the exact tested synthetic merge and its head and base commits. It includes the tested merge tree and head tree so a consumer can compare inputs when the base contributes changes.

The corpus section binds the original paired capture commit, specification digest and six capture receipt digests to the native save pins. Its `saves` map matches the shape of the [stage 11 result](PairedDiscoveryReplay.md), with six P01, eight P03 and eleven P04 variant pairs and distinct repeat-save pins for both applications. The receipt covers discovery data. The job uploads the compact JSON and retains the raw pytest report on the runner.

Use the read-only verifier with the exact workflow and aggregate runs, the [pending roster](PendingCiRoster.md), and a full audited commit present in the local Git checkout. Set `GH_TOKEN` or `GITHUB_TOKEN` through the authorized read-only credential source.

```sh
python3 re/automation/CiArchiveObservation.py --repository TryUniCAD/Kit --pull 94 \
  --aggregate-run AGGREGATE_RUN --aggregate-attempt 1 \
  --workflow-run WORKFLOW_RUN --workflow-attempt 1 \
  --roster /private/path/Batch.json --roster-sha256 ROSTER_PAYLOAD_SHA256 \
  --audited-revision FULL_COMMIT_SHA --saves-sha256 SAVE_ROSTER_SHA256
```

The audited commit must have the exact tree tested by the hosted workflow. Review its workflow, collector, tests and dependencies before supplying that pin. A pull request head is usable when its tree equals the tested merge tree. The verifier checks the authenticated pull request and current merge parents, the workflow run and GitHub Actions check suite, the ordered successful job steps, the artifact's ZIP digest and the recorded test and workflow source blobs against the audit pin. It reports the ZIP and receipt digests and checks for a competing head, base, workflow run or attempt before returning the evidence.

The verified archive result can accompany locally leased stage 11 evidence. The `archive_gate_verified` status requires a successful policy job. If its three archive steps passed and the policy job failed only at later steps, the observer reports `archive_steps_verified_job_failed` and includes the job's failure conclusion. A cancelled policy job or an unsuccessful archive step cannot supply that evidence. A [terminal aggregate failure](TerminalCiBatchObservation.md) remains unattributed even when the archive route passes. The archive observation keeps member attribution unavailable and leaves licensed readback, per-member certification and controller release to their respective evidence sources.

The producer runs directly after the existing hosted archive tests and requires a complete passed setup, call and teardown for both selected tests. Reading the six pinned Git receipts establishes the expected save roster SHA-256 `f4ff4fca58aa3c32bb57d890a1c74b8d69714887d8acea5e24f46b69b5c523f1`. The verifier's hosted process fixture exercises a successful archive result with both green and red aggregates, a rerun during verification, and mismatches in the audit, source, checked node, job step and archive bytes.

On PR head `08f2f8e6514ca1dfcf8a2dba98845d1c53430af1`, the three archive gate steps passed in [policy job 132958035635](https://github.com/TryUniCAD/Kit/actions/runs/43761784793/job/132958035635). The authenticated download of artifact `14180761180` matched ZIP SHA-256 `28715d3f515013bb36b05964822759b208f39c1e36ed8b555cdefac509ca3e6b`. Its receipt has canonical SHA-256 `d53b99d389e9c8703dab024a00c4b9e34bf9ea11c08b16e348d387c63d4f181d`, matches the expected save roster, and records the tested merge `7daf9ba0b3dce4b9e5b55ec481122a04d5707737` with identical head and tested trees. The later output-intake step failed when pytest collected two Fusion restart helpers as tests. The policy job and aggregate both concluded in failure.
