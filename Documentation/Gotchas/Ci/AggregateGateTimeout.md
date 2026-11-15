# Aggregate gate cases can time out without output

`TestPendingGate` in `tests/Policy/ReviewerAggregationTests.py` might appear to fail only when the CI aggregate logic changes.
Each case starts `node` with a 2 second timeout and expects a `Waiting for` line before the timeout.
On a loaded queue runner, the process can produce no output in 2 seconds.
The `quality-missing` case failed in [run 43530545010](https://github.com/TryUniCAD/Kit/actions/runs/43530545010) and passed in [run 43530343040](https://github.com/TryUniCAD/Kit/actions/runs/43530343040) on the same tree.

Compare the failure with an earlier queue run of the same tree before you change the aggregate scripts.

The same `quality-missing` case later failed without output in
[the post-merge audit](https://github.com/TryUniCAD/Kit/actions/runs/43695567222/job/132757055841).
Its aggregate script, command runner, case-input builder, and probe source were unchanged from the earlier passing suite.
The [probe repair](../../Changes/Ci/PendingAggregateProbe.md) waits for the actual pending message under a bounded startup allowance,
then retains a full two-second observation that the process stays blocked.
It also retains the missing-evidence assertion and rejects an early process exit.
Production CI budgets and required checks remain unchanged.
