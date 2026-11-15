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
The fixture and licensed verification of this revision remain pending.
