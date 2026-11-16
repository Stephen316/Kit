# Archive reader and process gate steering repair

## Behavior

The native SOLIDWORKS reader applies its final document projections through `ProjectPartDoc`.
The Cut, scope, second-pad and circular projections retain their existing order.
This keeps `ReadNativePart` within the declaration limit.

The archive process checks use `CheckFeatIndex` and `CheckExchange` as their collected names.
Their subprocess commands, pinned input revisions, counts, refusal checks and expected digests are unchanged.
No command-line option or public SDK signature changes.

## Verification and limits

The [hosted steering failure](https://github.com/TryUniCAD/Kit/actions/runs/43918468820/job/133478955245) identified all three violations at `7f65ede9b6c81a6ed1d952d02a5c510f59531f8e`.
Source inspection found no callers that require the previous check names.
The existing archive process gate collects both checks through its directory selection.
The repair was published concurrently at `bbf4853f4e148c42e0c7343bd7538eed7e779a2e`.
The alternate unpublished patch was withdrawn during coordination.
The [hosted steering check](https://github.com/TryUniCAD/Kit/actions/runs/43920099627/job/133484758140) passed for that revision.
Its [Pyright check](https://github.com/TryUniCAD/Kit/actions/runs/43920099312/job/133484757009) also passed.
Local tests and collection were not run.
Hosted reader and archive execution have separate results.

The [research harness steering gotcha](../../../../Gotchas/Ci/Policy/ResearchHarnessSteering.md) explains the scope boundary.
Current programme dependencies remain in the [step register](../../../../Reference/Research/AutomationSteps.md).
This repair does not establish native writer qualification or bidirectional acceptance.
