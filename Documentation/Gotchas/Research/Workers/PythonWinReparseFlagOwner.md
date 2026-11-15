# Pywin32 reparse flag owner

## Expectation

The pinned `pywin32==312` package exports every file-opening flag through
`win32con`.

## Actual behavior

The [Windows job at `ef431a17`](https://github.com/TryUniCAD/Kit/actions/runs/43668887044/job/132674284189)
reported three failed and eight passed process cases. The intake paths failed
with `AttributeError` because `win32con.FILE_FLAG_OPEN_REPARSE_POINT` is absent.
This prevented the secure file open from reaching byte copying.

The pinned [b312 file API source](https://github.com/mhammond/pywin32/blob/b312/win32/src/win32file.i)
exports `FILE_FLAG_OPEN_REPARSE_POINT` through `win32file`. The
[b312 constant module](https://github.com/mhammond/pywin32/blob/b312/win32/Lib/win32con.py)
contains the other constants used by intake: `FILE_SHARE_READ`, `OPEN_EXISTING`,
`FILE_FLAG_BACKUP_SEMANTICS`, `FILE_ATTRIBUTE_DIRECTORY`,
`FILE_ATTRIBUTE_REPARSE_POINT` and `GENERIC_READ`.

## Workaround

Use `win32file.FILE_FLAG_OPEN_REPARSE_POINT` for ancestor and final-file opens.
Keep the flag mandatory and retain the existing reparse-point rejection and
sharing restrictions. Do not substitute a missing flag with zero.

The repair was verified against the pinned source without importing Windows
modules or running local tests. A fresh real Windows process run is required.
