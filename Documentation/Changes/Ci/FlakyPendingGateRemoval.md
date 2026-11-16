# Remove flaky pending aggregate tests

## Behavior

Remove `TestPendingGate` from `tests/Policy/ReviewerAggregationTests.py`, including all seven parameterized cases.
Remove its unused `WaitPending`, `WaitSignalMut`, `ReadLinesMut`, and `ReleaseChildMut` modules.
No replacement timing probe is added.

The removed cases covered pending security reports, rejected report provenance, missing acceptance reports, missing quality reports, and pending CLI compatibility groups.
The remaining process checks still exercise completed aggregate results and exclusion of review reports from CI aggregation.
They do not replace the removed assertions about continued process liveness or missing evidence while checks remain pending.

Production aggregation, its timeout, the CI allowlist, workflow triggers, security checks, and queue acceptance requirements retain their existing behavior.
No configuration change is required.
See [queue operations](../../../MergeQueue.md) and the [startup timing gotcha](../../Gotchas/Ci/AggregateGateTimeout.md).

## Evidence and limits

The original `quality-missing` case failed in [run 43530545010](https://github.com/TryUniCAD/Kit/actions/runs/43530545010).
It passed on the same tree in [run 43530343040](https://github.com/TryUniCAD/Kit/actions/runs/43530343040).
The [post-merge audit](https://github.com/TryUniCAD/Kit/actions/runs/43695567222/job/132757055841) recorded another failure before Node emitted output.
The [earlier synchronization repair](PendingAggregateProbe.md) separated startup from the two-second liveness observation.
No recurrence of that repaired version was found in this audit.
This change removes the historically flaky family as requested, including the two subsequently added CLI cases.

The investigation inspected all 46 failed queue-workflow runs created from November 12 through November 15, 2026, before this change.
It read 58 failed test-job logs and identified 18 pending-gate case failures.
Other observed failures concerned deterministic contracts, fixtures, packaging, or missing compression support; they did not justify more deletions.
This bounded audit cannot establish that every remaining test is free of intermittent failures.

No tests ran locally.
Formatting and source-diff checks are local static validation only.
Current-revision PR checks and automated approval remain required.
Full-suite and heavy security acceptance remain deferred to the native merge queue.
This PR is intended to remain open and unmerged.
