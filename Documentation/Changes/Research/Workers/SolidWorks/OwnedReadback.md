# Direct ownership for queued SOLIDWORKS readback

The [queued P04 listener](../SolidWorksQueuedReadback.md) starts the registered SOLIDWORKS executable after the pinned PowerShell launcher has verified its installed build, interop, and scratch inputs.
It uses the exact executable with no arguments and holds the Windows handle returned by process creation.

The collector passively attaches to SOLIDWORKS and compares its COM process ID, creation FILETIME, canonical image and desktop session with the listener's launch record.
It verifies the expected build and an empty application before it publishes `native-owner.json` in the private readback spool.
The ticket binds this process to the exact queued request and source revision.
The queued worker requires the matching ticket and a signaled launch handle before it accepts the collector's result.

Use a dedicated licensed desktop with SOLIDWORKS closed before starting the listener.
Standalone calls to `ReadP04SolidWorks.ps1` keep their existing invocation and COM activation.
Missing ownership proof leaves the run failed and its spool fenced.

A separate licensed probe verified direct launch, passive COM identity, read-only healthy control rebuild and normal exit via the held handle.
The queued implementation still requires licensed verification.
