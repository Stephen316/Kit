# Windows research supervisor

A08e adds Windows process supervision without a CAD runtime dependency.
The Windows path requires Windows 10 or newer, Python 3.14 and the existing locked `pywin32==312` development extra.
Linux and macOS retain their process-group and `wait4` paths.

## Process containment

The supervisor creates each Windows runner suspended inside its private job object.
`PROC_THREAD_ATTRIBUTE_JOB_LIST` assigns containment during creation, before the initial thread can execute.
The supervisor then resumes that thread.
The job permits no breakaway and sets `JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE`.
Closing the supervisor therefore terminates contained descendants, including descendants in separate console process groups.
A successful leader exit also terminates remaining job processes before result publication.

Windows process creation uses an explicit executable and a standard-handle inheritance list.
Only the input, output and error handles enter the runner.
The job handle remains owned by the supervisor.
Private home and temporary paths remain inside the session directory.
The environment also preserves the Windows system variables needed to start executables.

The session record includes the random job name and exact process creation time.
Restart recovery checks creation time and job membership before stopping a live recorded process.
A mismatched process identity never authorizes termination.
An unavailable containment or resource API fails the affected operation explicitly.

## Resource and stop behavior

`GlobalMemoryStatusEx` supplies available physical memory.
The process affinity mask bounds the logical CPU count.
Each sample sums working sets for the job's current process roster.
The existing headroom, memory-stop and bounded-log settings apply without new configuration fields.

A graceful stop requests `CTRL_BREAK_EVENT` for the initial console process group.
The grace deadline terminates the full job when that request cannot stop every process.
The Windows receipt records an exit code instead of a POSIX signal number.
The sampled group peak and leader peak working set remain separate observations.

Windows byte-range locks enforce exclusive supervisor and adapter ownership.
Python 3.14 supplies nonblocking pipe reads for bounded log collection.
Application authoring workers and native acceptance remain separate A08c and A13 work.

## Verification

The new process coverage runs on an actual Windows runner:

```shell
uv run --frozen --no-default-groups --extra dev --python 3.14 python -m pytest -q tests/Research/Windows
```

The scenarios cover bounded output, private paths, leader exit, descendant cleanup, headroom, memory stops, lock contention, crash recovery and stale identities.
Source inspection and AST syntax checks ran locally.
No local tests, Windows emulation or CAD process ran.
Windows execution and Linux/macOS regression evidence remain pending remote CI.

The child fixture also handles the separate launcher PID used by Windows virtual environments.
It records the interpreter's parent chain and verifies each distinct process against the supervisor's job object.
The [launcher identity gotcha](../../../Gotchas/Research/Supervisor/WindowsVenvLaunchers.md) records the source evidence and pending diagnostic boundary.

The implementation follows [job-object containment](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects), [atomic job and handle assignment](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-updateprocthreadattribute), [creation-time measurement](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-getprocesstimes) and [physical-memory measurement](https://learn.microsoft.com/en-us/windows/win32/api/sysinfoapi/nf-sysinfoapi-globalmemorystatusex).
The [Python subprocess reference](https://docs.python.org/3.14/library/subprocess.html) defines the Windows environment and handle-inheritance requirements.

The first Windows job at `3a432ea0` passed five cases and left the descendant
cleanup case queued rather than completed. The assertion now retains the job
reason, attempts and event history for the next remote run; that diagnostic
change does not establish a repaired lifecycle. Windows fixture liveness uses
the typed Win32 process-handle API. Windows-only signal and subprocess flags
are converted at the runtime attribute boundary so Linux static analysis can
check the fixtures without suppressions.
