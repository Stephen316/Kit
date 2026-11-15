# Direct ownership for queued SOLIDWORKS readback

The [queued P04 listener](../SolidWorksQueuedReadback.md) starts the registered SOLIDWORKS executable after the pinned PowerShell launcher has verified its installed build, interop, and scratch inputs.
It uses the exact executable with no arguments and holds the Windows handle returned by process creation.

The collector passively attaches to SOLIDWORKS and compares its COM process ID, creation FILETIME, canonical image and desktop session with the listener's launch record.
It verifies the expected build and an empty application before it publishes `native-owner.json` in the private readback spool.
The ticket binds this process to the exact queued request and source revision.
The queued worker requires the matching ticket and a signaled launch handle before it accepts the collector's result.
Successful measurements retain the ticket and the dispatch receipt records its canonical SHA-256.

Use a dedicated licensed desktop with SOLIDWORKS closed before starting the listener.
Standalone calls to `ReadP04SolidWorks.ps1` keep their existing invocation and COM activation.
Missing ownership proof leaves the run failed and its spool fenced.

## Bound timeout recovery

On a dedicated unattended scratch desktop, start the listener with `--recover-owned-timeout` to enable a bounded forced exit after a collector timeout.
Use this only for a session reserved for the P04 worker and its read-only scratch documents.
The listener first stops its timed-out collector, then checks the complete request ticket and remeasures the creation time, image and session on the still-held Windows process handle.
It acts only on that handle and waits at most five seconds for it to signal.
The listener never reopens a process by PID for timeout recovery.

`native-recovery.json` records whether the owned process already exited, was terminated and observed to exit, or remains quarantined.
A missing or mismatched ticket or handle stays quarantined.
The failed result, spool and quarantine remain available for disposition even after a confirmed exit.
Starting a new listener does not clear a SOLIDWORKS fence.

A separate licensed probe verified direct launch, passive COM identity, read-only healthy control rebuild and normal exit via the held handle.
The Windows process checks use a disposable operating-system child to exercise missing tickets, changed tickets and mismatched handle identity.

## Licensed queue verification

Two licensed Windows runs used revision `566ec2c705aa50a5576570d30d08fb79439de162` and SOLIDWORKS `34.4.1.1011`. The normal run read and rebuilt all eleven P04 discovery files, verified every supporting face, observed exit on the held native handle and acknowledged the accepted spool. Recomputing the ownership ticket digest from the accepted measurements matched the durable dispatch proof. The accepted result SHA-256 is `c48724c377c328c5471504c62749b6847c8d023e31d0d7024675b74ecc8ee9a7`. The ticket SHA-256 is `cdbd56b064b2db891e38d7f65f043c0af8fad3618dc398be33c2cdcb877610c4`.

The short-deadline run used a 25-second controller job limit and enabled owner timeout recovery. The collector had published the verified empty-startup ticket when its request expired. The listener stopped the collector, verified the exact ticket and held native identity, terminated the owned process and observed its exit. A03 recorded `waiting_application` for attempt one. The phase expired with an empty artifact list, and the quarantine and spool remained present. The controller receipt SHA-256 is `6b517d8aedd737ba58243de8b46ab48ab3603c83b809211e1f16a31d94b17c24`. The recovery receipt SHA-256 is `68769557195d000dde1eba144c99694efe185ea620dcb270c8011ffa28790da8`.

The independent refusal cases still await remote CI. Releasing the resource and scheduling a bounded retry after confirmed cleanup remain separate operations.
