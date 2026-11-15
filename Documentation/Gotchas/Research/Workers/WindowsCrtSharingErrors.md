# Windows CRT sharing errors

## Expectation

Every refused Windows file mutation reports the native sharing or access error
through `OSError.winerror`.

## Actual behavior

The [Windows job at `2ff96767`](https://github.com/TryUniCAD/Kit/actions/runs/43676632437/job/132698100644)
passed twenty-one cases and failed only the new protected-reader sharing case in
70.20 seconds. Every mutation action raised an exception; an action that succeeded
would already have failed the fixture subprocess. The later assertion requiring
all `winerror` values to be 5 or 32 failed, but the original assertion did not print
the individual values. That log does not establish which value differed.

The pinned [CPython 3.14.10 FileIO source](https://github.com/python/cpython/blob/v3.14.10/Modules/_io/fileio.c)
opens Windows files with CRT `_wopen`. On failure it raises through
`PyErr_SetFromErrnoWithFilenameObject`, rather than the native Windows-error
constructor. Consequently, `Path.write_bytes` refusal can be a
`PermissionError` with `errno == EACCES` and no `winerror`. Native file API calls
retain the Windows sharing or access error code.

## Workaround

Retain each operation's refusal requirement. Record exception type, errno,
winerror and message, and print the full operation dictionary before assertions.
Require the CRT writer to raise `PermissionError` with `EACCES`, accepting an
absent native code or the native access/sharing codes. Independently attempt a
native `CreateFile` write, requiring native error 5 or 32. Require those same
native codes from deletion, file rename and ancestor rename.

After releasing the reader, require all five operations on the same path to
succeed and preserve the original bytes. This distinguishes protection by the
held reader from unrelated path or permission failures. The repair changes the
process fixture only; production sharing restrictions remain unchanged. A new
real Windows run must verify these stronger controls; no local tests ran.
