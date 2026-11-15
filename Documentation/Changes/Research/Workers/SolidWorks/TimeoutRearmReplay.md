# Resume a SOLIDWORKS rearm after supervisor interruption

Before A03 settles a typed timeout, the supervisor writes a private rearm intent.
The durable failure result includes its SHA-256.
The intent binds the controller store, original supervisor owner digest, exact attempt, typed queue timeout, runner entry and installation bytes.
The supervisor's owner credential stays in its process and is passed to the rearm command over private standard input.

On restart, the replacement supervisor checks its own normal A03 owner fence before it reads the intent.
It can carry out [rearm](TimeoutRearm.md) when A03's immutable failure and current resource hold bind the original owner and the exact intent.
The native listener must still be the same Windows process and must confirm the original native process exit.
The replacement rechecks the controller epoch after staging the archived bytes.
Changed controller or runner configuration, revoked ownership, replaced listeners and legacy results without a bound intent leave the job parked.

A replay after the rearm transaction commits returns the prior archive without changing admission again.
A rearm that still awaits a terminal record or dispatch lock polls within the existing bounded wait.
An unresolved intent remains available for a later supervisor restart.

The Windows process fixture interrupts the original supervisor after `FinishJob`, keeps the verified listener running and requires a replacement supervisor to issue the same job's next ordinary attempt.
The exact published `5770f1b3` Windows job passed 50 cases, including both timeout rearm variants. [Windows research job](https://github.com/TryUniCAD/Kit/actions/runs/43706418832/job/132788439885)

## Licensed restart witness

Published revision `5770f1b322688e55237172d7a6d57c983f334ce0` ran the controller and licensed SOLIDWORKS listener with a 25-second deadline and two attempts. The supervisor exited immediately after A03 accepted the first timeout. The quarantined spool and private rearm intent remained. A replacement supervisor reused the accepted failure receipt `9e395c8e703e67d02807370ca5d5482f4237d7049dad04453d6b4f37b7e1b4d9` with the same live listener.

The replacement recorded one recovered rearm, removed its committed intent and archived all 22 verified spool files under manifest `2b782bd9681edb391553c758fe5e20341c47399b7d8d3d93a41ce69180441579`. A03 recorded only the second claim after restart. The listener accepted a distinct request under the new lease, and the second short-deadline timeout remained quarantined at the configured attempt limit. The private witness summary SHA-256 is `277c1a21840761475cd277c1b9dd9e20b189a693643e6754207d20898fe211f2`.
