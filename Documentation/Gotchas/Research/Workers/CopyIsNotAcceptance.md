# A session copy is not controller acceptance

## Expectation

After an application worker verifies and copies native output into `session/work`,
it can delete the original application spool.

## Actual behavior

Source review of the initial dispatch implementation found that deletion happened
before the supervisor finished durable intake and before the controller accepted
the current lease. A crash in that interval leaves only the session copy.
Supervisor recovery removes the abandoned session, so the capture can be lost.
Successful copying and a completed application response do not prove accepted
controller storage.

## Workaround

Retain the original spool until actual controller acceptance is verified. The
current local dispatch protocol has no acceptance acknowledgement, so it retains
one outstanding spool and fences the installation for owner verification or
recovery. An application restart does not remove an acceptance fence. A copy
journal records the copied hashes but explicitly remains pending acceptance.

Before manual cleanup, verify the controller's completed job and accepted output
manifest against the retained files. If the attempt is stale or incomplete,
preserve the evidence for recovery or explicit owner disposition. Do not create a
synthetic acknowledgement based on the worker's exit status or copy journal.

Completed spools have a 32-file, 520-MiB check. That is not a disk quota while an
externally owned CAD process writes. Native process limits and automated
acceptance acknowledgement remain open work.

`QueueRecoveryTests.py` adds a real client interruption after verified copying,
then removes the session copy and checks retained bytes, the acceptance record
and blocked new admission. Execution belongs to remote CI; it was not run locally.
The [dispatch change](../../../Changes/Research/Workers/LocalApplicationDispatch.md)
records the exact protocol limits and remaining gaps.
