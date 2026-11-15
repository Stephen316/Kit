# PID file existence does not prove complete publication

## Expectation

Once `child.pid` exists, the supervisor cleanup fixture can parse the child's process identity.

## Actual behavior

The fixture opened the final path before writing its PID, so a concurrent reader could observe an empty file. The [macOS process run at `6fb599a9`](https://github.com/TryUniCAD/Kit/actions/runs/43672428040/job/132685202111) failed `CheckGroupStop` with an empty integer conversion before exercising restart cleanup.

## Workaround

Write the complete PID into a sibling staging file, close it, then atomically rename it to the observed path. Keep the existing real child handshake, identity checks and descendant cleanup assertions.
This is a fixture publication repair; current-head remote execution is still required.
See [bounded logs and restart cleanup](../../../Changes/Research/Supervisor/BoundedSessionLogs.md).
