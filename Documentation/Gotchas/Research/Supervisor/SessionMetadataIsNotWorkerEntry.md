# Session metadata does not prove worker entry

The POSIX launch gate intentionally publishes `session.json` before it releases the configured worker.
A polling test can therefore observe valid process metadata while that process is still the bootstrap.
If the test immediately kills the supervisor, the gate sees EOF and exits before recovery starts.
An unmatched orphan identity then proves neither a live-worker cleanup failure nor a reason to weaken recovery assertions.

The [Linux supervisor job](https://github.com/TryUniCAD/Kit/actions/runs/43674626489/job/132692018859) at `95b3f2e478742e3b166aef5ba13b495f2ff6434e` passed 42 cases and failed the old restart fixture for this reason.
That fixture killed the supervisor as soon as `session.json` appeared.

Tests that require a live orphan must wait for a PID-bound marker published by the actual worker in the intended execution phase.
The sleep-first and hold branches share one phase-parameterized marker writer, which writes, syncs and atomically renames the marker before sleeping.
The restart test waits for sleep-first entry before killing the supervisor, while retaining its identity, stopped-process and fake-PID bystander checks.
Both evidence-rebinding cases wait for hold entry before changing the binding, so they continue to test a stale running worker rather than rejected startup.
Their stale-event, running-session and final-result assertions remain intact.
The separate launch-gate cases continue to test supervisor death before release.

The [launch-gate change](../../../Changes/Research/Supervisor/PosixWorkerLaunchGate.md) records the distinction and the repaired fixture's pending remote verification.
