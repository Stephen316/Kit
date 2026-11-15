# Recover an owned SOLIDWORKS process after collector failure

The [queued P04 listener](../SolidWorksQueuedReadback.md) accepts an optional `--recover-owned-failure` flag on its `listen` command. Configure it on the owner's dedicated scratch listener. The supervisor submits its normal application request to that listener using the existing installation configuration.

The listener can stop SOLIDWORKS if its collector has exited and the exact ticket proves that the listener started the process in its own desktop session with an empty document set. It verifies the request hash, source revision, build, executable, process ID, creation time and session against the retained handle before termination. Termination must start within the original request deadline. The process exit check uses the remaining deadline and a five-second cap.

The failed phase retains the quarantine and its usual application-wait outcome. When configured, `native-failure-recovery.json` records the collector exit code and any confirmed native exit or refusal in the private spool. The timeout recovery flag, files and automatic timeout rearm still follow the [deadline protocol](TimeoutRearm.md).

The Windows process fixture uses disposable processes to check successful owned termination and refusal for missing tickets, changed tickets, changed process identity and a passed deadline. It also runs the existing timeout recovery cases. Hosted verification of this change is pending.
