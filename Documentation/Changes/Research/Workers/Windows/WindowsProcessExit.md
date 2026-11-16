# Observe an exact Windows process exit

The Windows research worker can watch a caller-pinned process through
a single Windows kernel handle. Use `watch_peer(peer, executable)`
with the process ID and its `windows:<creation FILETIME>` identity.
Supply the absolute path to the expected executable. Arming verifies
the PID, creation time, resolved image path, and caller's user SID and
Windows session while the process is live.
[Observer source](../../../../../re/automation/ApplicationWorkers/WindowsProcessExit.py)

Inside the watch context, call `observe_exit(watch, timeout_ms)` with an
integer from 0 through 300,000 milliseconds. A timeout returns `None`.
When the handle signals, the observer verifies the same process lifetime
and returns its PID, creation identity, exact kernel exit FILETIME and
exit code. Access is limited to process queries and synchronization.
Process startup, termination and ownership changes remain under the
existing application operator's controls.

Context exit waits for any active observation before clearing and
closing the handle. The observer retains that handle through the wait
and exit reads, and a closed watch refuses reuse. An unavailable or
already exited process cannot arm a new watch.

## Verification

The published observer recorded the exact exit FILETIME and code 37 from
a disposable Python child that exited normally. The context close
waited for the active native wait before releasing the handle.
[Disposable-child observation](https://github.com/TryUniCAD/Kit/pull/94#issuecomment-6927963176)

The hosted Windows supervisor suite includes a disposable-child check
for the concurrent wait and close, a live timeout, identity mismatch
and refusal to reuse a closed or exited watch.
[Windows process check](../../../../../tests/Research/Windows/ProcessExit/WindowsProcessExitTests.py)
The standalone observation covers Windows process exit. Fusion restart
dispatch and licensed acceptance have their own evidence requirements.
[Fusion phase audit](../FusionPhaseAudit.md)
