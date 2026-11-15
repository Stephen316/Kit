# Worker outputs need intake before cleanup

## Expectation

A successful application runner can return a private output path and rely on its
completion receipt to preserve the generated file.

## Actual behavior

The supervisor removes the private session directory after `FinishJob` returns.
The original controller stored JSON receipts and runner records, but did not copy
files referenced by those records. A successful receipt could therefore outlive
the file it described. Hashing a path in a runner record alone does not establish
that the controller retained those bytes.

## Workaround

Use the version 1 declared-output intake contract described in
[durable worker outputs](../../../Changes/Research/Workers/DurableWorkerOutputs.md).
The controller stages and verifies each file before accepting its durable digest.
It checks the lease after copying and before publishing job state. A stale finish
can leave an unreferenced content-addressed object, but cannot publish an accepted
result or dependency reference.

POSIX intake uses directory-relative file descriptors with no-follow opens and
a nonblocking final open. Windows intake opens reparse points themselves and
rejects them while holding ancestor handles without write/delete sharing. These
checks prevent a regular-file precheck from becoming a blocking FIFO read or a
copy through a replacement link.

Sources: [Microsoft CreateFileW](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew),
[Windows reparse-point operations](https://learn.microsoft.com/en-us/windows/win32/fileio/reparse-points-and-file-operations),
[Python file descriptor operations](https://docs.python.org/3.14/library/os.html#files-and-directories).

Real process coverage is in `tests/Research/Outputs`. Remote execution is pending;
mid-copy mutation and post-copy deadline expiry are not yet independently proved.
