# A process leader can exit before its children

## Expectation

A stopped session leader can appear to establish that the session's process group stopped.

## Actual behavior

The previous restart cleanup returned success when the recorded leader disappeared or became a zombie.
A child in the same group can ignore `SIGTERM` and continue running after that event.
Source inspection identified this early-success condition in `orphan_gone`.
The new restart process scenario creates that exact leader-and-child arrangement.
Its remote result remains pending when this page is introduced.

## Workaround

Validate the leader's recorded start identity before the first signal.
Track non-zombie members of the entire group during the grace period.
Send `SIGKILL` to surviving members before recording cleanup success.
Keep the session and its lease evidence when cleanup cannot establish success.
Children that create another process group need a separate containment mechanism.

See [the change entry](../../Changes/Research/Supervisor/BoundedSessionLogs.md).
