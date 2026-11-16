# Short leases in Windows calibration

The Windows sweep checks that the fixed archive decoder accepts every input and retains physical measurements and cleanup evidence at all four requested levels.

At `3cd136ad8`, the first trial completed seven of eight jobs in 38.93 seconds. One worker stopped with `stale_lease` before the trial's 45-second bound. With the three-second fixture lease, the first renewal was due after one second and went through a separate controller process. The log did not record the timing or cause of the stale heartbeat. [Hosted Windows failure](https://github.com/TryUniCAD/Kit/actions/runs/43781577583/job/133019771915)

The Windows success case uses a 12-second lease with the same 30-second job deadline and 45-second trial bound. The dedicated controller process tests still exercise renewal and expiry with one- and two-second leases. Hosted verification of the fixture change is pending.
