# Orphan controller subprocesses can publish late claims

## Expectation

After a supervisor dies, the next supervisor can scan private claim files once
and recover every outstanding attempt.

## Actual behavior

Killing the supervisor does not necessarily stop an already launched controller
subprocess. That subprocess can begin its transaction and publish a claim after
the replacement supervisor's recovery scan. The claimed jobs then have no local
worker session and wait for lease expiry, potentially consuming their attempt
budget without doing work. The race affects both solo and grouped claims.

A transaction barrier alone is insufficient: an older invocation can start after
the barrier. Holding only supervisor OS locks also does not fence a controller
subprocess that outlives the process which owned those locks.

## Workaround

Rotate an owner epoch inside the controller before scanning recovery files. Check
the exact supplied epoch inside the same immediate write transaction as every
participating invocation. Transaction serialization orders old claim publication
before recovery or rejects the replaced owner before publication.

Use the optional capability only with adapters that implement it. Legacy
controller calls and older supervisors without an epoch remain unfenced.

The [owner-epoch change](../../../Changes/Research/Workers/SupervisorOwnerEpoch.md)
records the protocol and interruption scenarios. Remote execution is pending.
Windows process-chain checks use
[Win32_Process](https://learn.microsoft.com/en-us/windows/win32/cimwin32prov/win32-process),
because a venv launcher PID can differ from its interpreter PID.
