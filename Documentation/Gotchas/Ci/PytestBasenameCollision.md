# Pytest imports unpackaged cases by basename

## Expectation

Process cases in different directories can share a filename when selected together.

## Actual behavior

The [macOS grouped gate at `6e2da255`](https://github.com/TryUniCAD/Kit/actions/runs/43673027349/job/132687037442) stopped during collection because both the existing supervisor suite and the new grouping directory contained `SupervisorFenceTests.py`. The files are in unpackaged directories, so the configured pytest import mode used the same module name.
No process cases ran in that job; source type checks did not exercise collection.

## Workaround

Give the new grouped fence module the unique basename `GroupedFenceTests.py`. Keep both test selections and every existing fence assertion.
The [grouped-session change](../../Changes/Research/Supervisor/GroupedSmallFileSessions.md) records the current remote verification requirement.
