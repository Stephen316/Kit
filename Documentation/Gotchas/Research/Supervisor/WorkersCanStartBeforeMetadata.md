# Workers can start before process metadata

`Popen` can execute a worker as soon as it returns a process handle.
Writing `session.json` afterwards leaves a recovery gap: the worker may create descendants before the supervisor records their process-group identity.
Killing the supervisor in that gap can leave executable work without recovery metadata.

POSIX startup now runs a small isolated bootstrap behind an inherited read-only pipe.
The parent writes and syncs process metadata before releasing it.
Closing the parent writer without a release byte makes the bootstrap exit before worker execution; a fixed gate wait bounds a live but stalled launch.
An in-place `exec` then preserves the recorded process identity for normal recovery.

Do not run user Python startup modules before the gate or inherit its writer into the child.
Do not release the worker after a metadata-write or directory-sync failure.
See [the launch-gate change](../../../Changes/Research/Supervisor/PosixWorkerLaunchGate.md) for actual process fixture boundaries and the remaining remote evidence limit.
