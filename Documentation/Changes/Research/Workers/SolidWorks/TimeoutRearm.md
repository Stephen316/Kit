# Retry a confirmed queued SOLIDWORKS timeout

Use the [queued readback configuration](../SolidWorksQueuedReadback.md) with an owner-configured application installation, one capacity-one controller resource and `--recover-owned-timeout` on its dedicated scratch listener.
The normal supervisor attempts a rearm after A03 settles an explicitly [linked deadline failure](TimeoutProvenance.md).
The failed attempt stays a `waiting_application` result in its immutable receipt and history.

The rearm checks the same live listener, authenticated A03 owner, exact failed execution, and [current resource hold](../../Controller/ApplicationHoldEpoch.md).
It waits briefly for the terminal result of an already running request.
It requires the listener to attest exit of the ticketed native process.
Unclaimed requests, unknown owners, changed epochs, incorrect tickets and older failure evidence leave the job parked.

While holding the endpoint dispatch lock, rearm stages every failed spool file in immutable A03 storage and retains the spool under `failed-spools`.
The manifest binds the spool to the failed controller receipt and result.
A03 rechecks the hold and releases the capacity-one resource and the same parked job in one transaction.
The exact quarantine is removed only after archival and final checks.
A repeat of the exact intent returns the already recorded archive.
A failure before the A03 transaction commits leaves the resource unavailable. [Supervisor restart recovery](TimeoutRearmReplay.md) can verify an already archived spool.

Each retry uses the next ordinary controller lease, the submitted `max_attempts` and the configured exponential backoff.
The resource stays unavailable when the budget is exhausted.
Other explicitly parked attempts retain their park flags.

The remote Windows fixture runs the real queue, supervisor and controller with a disposable Windows process.
It checks one successful rearm, exhaustion on the next attempt, retention of the first failed evidence and preservation of the second quarantine.
Remote and licensed verification remain pending for this revision.
