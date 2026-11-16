# Aggregate gate cases can time out without output

The former `TestPendingGate` cases could fail without changes to the CI aggregate logic.
The original probe started `node` with a two-second timeout and required a `Waiting for` line before that timeout.
On a loaded queue runner, the process could produce no output in two seconds.
The `quality-missing` case failed in [run 43530545010](https://github.com/TryUniCAD/Kit/actions/runs/43530545010) and passed in [run 43530343040](https://github.com/TryUniCAD/Kit/actions/runs/43530343040) on the same tree.

Compare failures with earlier queue runs of the same tree before changing the aggregate scripts.

The same `quality-missing` case later failed without output in
[the post-merge audit](https://github.com/TryUniCAD/Kit/actions/runs/43695567222/job/132757055841).
Its aggregate script, command runner, case-input builder, and probe source were unchanged from the earlier passing suite.
The [probe repair](../../Changes/Ci/PendingAggregateProbe.md) waits for the actual pending message under a bounded startup allowance,
then retains a full two-second observation that the process stays blocked.
It also retains the missing-evidence assertion and rejects an early process exit.
Production CI budgets and required checks remain unchanged.

The [flaky-test removal](../../Changes/Ci/FlakyPendingGateRemoval.md) subsequently removes all seven pending-gate cases and their four unused helpers.
The synchronized version had no recorded recurrence in this audit; its removal follows the request to delete the historically flaky family.
Completed-result checks remain, but they do not replace coverage of pending-process liveness or missing evidence during waiting.
