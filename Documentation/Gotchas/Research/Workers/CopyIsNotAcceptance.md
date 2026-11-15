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
local dispatch protocol retains one outstanding spool and fences the installation
for owner verification or recovery. An application restart does not remove an
acceptance fence. A copy journal records the copied hashes as pending acceptance.

Use the [owner command](../../../Changes/Research/Workers/ApplicationAcceptance.md)
to verify the controller's completed job and accepted output manifest against
the retained files. The command leaves a stale or incomplete attempt fenced.
The worker exit status and copy journal are insufficient for acknowledgement.

The transport checks completed spools against limits of 32 files and 520 MiB.
Writes from the externally owned CAD process still need a disk quota.
Use the [supervisor binding](../../../Changes/Research/Workers/SupervisedApplicationAcceptance.md)
to invoke acknowledgement automatically after successful controller settlement.

`QueueRecoveryTests.py` adds a real client interruption after verified copying,
then removes the session copy and checks retained bytes, the acceptance record
and blocked new admission. Execution belongs to remote CI; it was not run locally.
The [dispatch change](../../../Changes/Research/Workers/LocalApplicationDispatch.md)
records the exact protocol limits and remaining gaps.
