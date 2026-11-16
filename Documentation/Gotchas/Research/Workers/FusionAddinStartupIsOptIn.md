# A launched Fusion process may have no startup add-in

The tracked `KitCaptureRunner` manifest deliberately uses
`runOnStartup: false`. LaunchServices can successfully launch the reviewed
Fusion bundle while the associated worker queue remains unavailable. A PID or
the add-in's old status file cannot establish whether the current process
automatically loaded the reviewed bootstrap.

Commission the owner-private startup copy once and check a fresh nonce
response from the current peer. Fusion provides the startup-versus-manual
invocation signal in the add-in's run context.
[Startup preparation and observation](../../../Changes/Research/Workers/FusionStartupProvision.md)
