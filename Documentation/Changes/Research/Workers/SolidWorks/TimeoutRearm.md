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
Consuming pending application settlement counts as supervisor work in that pass, so a just-rearmed job can enter its configured backoff with a fresh idle interval.

The remote Windows fixture runs the real queue, supervisor and controller with a disposable Windows process.
The listener waits for the exact queue client's exit and timeout cancellation before closing the owned fixture process and publishing terminal evidence.
The case checks one successful rearm, exhaustion on the next attempt, cleanup evidence for both retained spools and the final controller result's binding to the second quarantine.

All three rearm cases passed at PR head `3cd136ad` and tested merge `e1fa7f1d`. That job also reported a collection error for the new timeout assertion helper and a separate calibration failure. The helper rename at `d7a2f3ce` keeps it outside pytest's selection while retaining the rearm assertions. [Hosted Windows job](https://github.com/TryUniCAD/Kit/actions/runs/43781577583/job/133019771915)

## Licensed two-attempt witness

Published revision `41c963c57489de030766be33c5e91fa061ad6861` ran the normal Windows controller, supervisor and licensed SOLIDWORKS listener against the pinned eleven-file P04 workload. The job used a 25-second deadline and two attempts. Attempt one timed out, the listener confirmed termination through its retained native handle, and A03 accepted the waiting-application receipt `5e794ed859dbc32c9cdd1119bd6bb64dd6b7eade008daf0448dab4c4075cb8bb`. The listener's owner-ticket SHA-256 was `67bde8a1a3a702708c4aef51d85037c8cf7519e6b790f64b236b78f46cb0dd7b`.

The ordinary supervisor recorded one rearm with archive manifest `b32df62f40e91985f9fb5864ae47ab9056565e6a094a546d5665ee833a4eb7be`. All 22 archive files matched the recorded digests and sizes. A03 recorded its second claim, and the same listener accepted a new request with a distinct job ID and request hash. Attempt two also hit the short deadline. Its separate quarantine remained in place because the attempt budget was exhausted. The final A03 waiting-application receipt was `4c94c65bd70790a022a5a0fc8ecc7318f1725ae9d4fdaf6a5488c5f7bf41a052`. The two-attempt witness covers rearm and budget exhaustion on the live Windows application path. [Replacement-supervisor replay](TimeoutRearmReplay.md) has a separate verification requirement.
