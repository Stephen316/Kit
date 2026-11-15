# Windows path and handle times

## Expectation

On the pinned CPython 3.14.10 Windows runtime, `stat(path)` and `fstat(fd)`
provide interchangeable `st_ctime_ns` values for one unchanged file.

## Actual behavior

The [Windows job at `95b3f2e4`](https://github.com/TryUniCAD/Kit/actions/runs/43674626489/job/132692019085)
passed sixteen process cases, including all five owner epoch cases. Both new
application parking cases rejected their inputs with `ValueError: application
input changed while reading`. The initial identity check passed; the final
path/handle comparison failed. The log did not retain the differing timestamp
values, so it does not establish a measured timestamp delta.

The pinned [CPython file utility implementation](https://github.com/python/cpython/blob/v3.14.10/Python/fileutils.c)
sets descriptor `st_ctime` from `FILE_BASIC_INFO.ChangeTime`, and birthtime from
`CreationTime`. In contrast, `win32_xstat` in the pinned
[path implementation](https://github.com/python/cpython/blob/v3.14.10/Modules/posixmodule.c)
explicitly replaces path `st_ctime` with birthtime for legacy compatibility.
Consequently, a rewritten or renamed file can fail this cross-provider equality
without any mutation during reading. The same invalid equality existed in the
Windows declared-output reader.

## Workaround

Hold directory and final-file Windows handles throughout the read, opening with
`FILE_SHARE_READ` and `FILE_FLAG_OPEN_REPARSE_POINT`. Reject reparse points,
directories, nonregular files and multiple links. Compare path and descriptor
snapshots through shared file identity, kind, link count, size, modification time,
birthtime and attributes. Use one final path snapshot. Separately retain exact
same-provider descriptor checks, including actual change time, before and after
reading. POSIX comparisons retain their change-time checks.

[CreateFileW sharing rules](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew)
prevent data writes and deletion while those handles remain open. Attribute-only
access is not blocked by file sharing; the descriptor change-time check is still
necessary. [FILE_BASIC_INFO](https://learn.microsoft.com/en-us/windows/win32/api/winbase/ns-winbase-file_basic_info)
distinguishes creation, modification and change times.

The Windows process fixture creates a record with deliberately distinct creation
and change times, rewrites and renames it, then reads it through both boundaries.
It also attempts writes, deletion and renaming from another process, mutates
change time through an attribute-only handle, and checks hardlink, junction,
directory and byte-limit refusal. These are new CI cases; no local tests ran.
