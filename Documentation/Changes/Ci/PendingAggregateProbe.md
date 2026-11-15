# Synchronize pending aggregate probes

## Behavior

The aggregate command probes wait for their expected `Waiting for` message before observing continued liveness.
All five existing pending scenarios retain their selected check, two-second pending observation, and absence-of-evidence assertion.
An early process exit fails the probe, including an exit after the expected message.

Node startup has a separate bounded thirty-second allowance.
The supervisor drains process output while waiting, then kills and reaps the child and joins its output reader.
Process and reader cleanup each have a five-second limit.
The production aggregate's polling budget and CI job timeout are unchanged.
The output reader, pending-message observer, supervisor, and cleanup each own a focused module.
Queue and handle mutators carry the required `Mut` suffix, and imports name their exact defining symbols.

## Cause and verification

The [post-merge audit](https://github.com/TryUniCAD/Kit/actions/runs/43695567222/job/132757055841)
passed all seventeen security jobs but failed the `quality-missing` pending probe before Node emitted any output.
The aggregate script, command runner, case-input builder, and probe source were unchanged from the original merged revision's passing suite.
This matches the [documented loaded-runner race](../../Gotchas/Ci/AggregateGateTimeout.md).

The previous harness stopped the whole process after two seconds, counting interpreter startup against a pending-state assertion.
The synchronized probe still requires the exact pending message and two more seconds without an exit.
It never accepts a pending check as healthy or publishes partial CI evidence.

No tests ran locally.
The existing real command scenarios run in the complete remote suite; its completeness report remains the acceptance evidence.
See the [audit repair entry](PostMergeAuditRepairs.md).
