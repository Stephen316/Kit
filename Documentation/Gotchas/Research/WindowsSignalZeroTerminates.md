# Signal zero can terminate a Windows process

## Expectation

On POSIX systems, `os.kill(pid, 0)` checks whether a process exists without sending a terminating signal.
A shared liveness helper can therefore appear safe on Windows.

## Actual behavior

Windows supports console control events through `os.kill`.
Other signal values call `TerminateProcess`, and the supplied value becomes the exit code.
Zero does not provide the POSIX existence check.

The [Python process reference](https://docs.python.org/3.14/library/os.html#os.kill) documents this difference.
Source inspection found that the existing research test helper used the POSIX check without a Windows branch.
No process was terminated to reproduce that behavior locally.

## Workaround

Windows process coverage uses `OpenProcess` and a zero-time `WaitForSingleObject` query.
It closes the query handle afterward.
The supervisor uses exact creation times for restart fencing and job objects for descendant termination.
Keep POSIX-only liveness helpers out of Windows process checks.
