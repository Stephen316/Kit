# POSIX worker launch gate

The supervisor now records POSIX process recovery metadata before the configured worker can execute.
Previously `Popen` could run the worker and create descendants before `session.json` existed.
A supervisor killed in that interval had no durable process identity for recovery.

## Startup and cleanup

POSIX startup creates a private pipe and launches an isolated Python bootstrap in the new process group.
The bootstrap uses `-I -S` so user startup modules cannot run before the gate.
Only the pipe reader is inherited by the bootstrap; the parent writer is not inherited.
The bootstrap waits up to 30 seconds for one release byte, closes its reader and executes the configured argument vector in place.
EOF or an invalid byte exits without executing the worker.
The 30-second bound covers the gate wait after bootstrap initialization, rather than arbitrary kernel or filesystem stalls.

The parent measures the bootstrap's process identity, writes and file-syncs `session.json`, and syncs its containing directory before sending the release byte.
The parent also renews and checks the current logical lease or grouped leases and execution stop time before release.
The worker retains the same process ID, process group and process-start identity across `exec`.
Before execution the bootstrap restores Python-ignored pipe/file-size signals to the defaults used by [ordinary subprocess startup](https://docs.python.org/3/library/subprocess.html#subprocess.Popen).
A parent killed before release closes the writer automatically, so the bootstrap exits without running worker code or creating worker descendants.
If metadata publication fails, startup closes the writer, stops and reaps the bootstrap through the existing process-group path.
Descriptor cleanup also covers failed process creation and successful release.
A bootstrap or worker execution error remains a bounded failed/retryable research attempt; it does not establish native acceptance.

Windows retains its existing Job Object creation and cleanup path and does not use the POSIX pipe bootstrap.
This change makes no new Windows native-application qualification claim.

## Verification

The new process fixtures kill a real launcher while its actual bootstrap is blocked, check the real 30-second no-release exit, and reject a real invalid metadata destination.
Worker-entry markers prove that those cases do not execute the configured worker.
A native `/usr/bin/yes` process with a closed output pipe verifies the ordinary SIGPIPE termination contract after bootstrap execution.
A separate full supervisor/controller/runner case verifies that a normal worker reads its process metadata, retains the recorded identity across execution, and leaves no live same-group descendant after its leader exits.
No clock replacements or production timing hooks are used.

Local verification is limited to source AST checks, pinned Black, Mypy, Pyright, repository Steering, and documentation links.
No local tests or reproductions ran.
The [Linux supervisor stage](https://github.com/TryUniCAD/Kit/actions/runs/43674626489/job/132692018859) at `95b3f2e478742e3b166aef5ba13b495f2ff6434e` passed 42 cases, including the new launch cases.
Its existing live-orphan restart case failed because it killed the supervisor on metadata visibility, before worker entry was guaranteed.
That fixture now waits for an atomically published worker-entry marker and retains every identity, stopped-process and fake-PID protection assertion.
Both held-evidence rebinding cases also wait for the actual hold phase, using the same marker writer and waiter with an explicit phase parameter.
Their stale/running-session assertions remain unchanged.
See [the fixture gotcha](../../../Gotchas/Research/Supervisor/SessionMetadataIsNotWorkerEntry.md).
The repaired restart case, macOS process results and existing Windows compatibility gates still require evidence on the tested revision.
The [startup gotcha](../../../Gotchas/Research/Supervisor/WorkersCanStartBeforeMetadata.md) describes the original recovery gap.
