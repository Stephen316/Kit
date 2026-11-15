# Atomic application record publication

Application request and response names now become visible only after their bytes are written, flushed, file-synced and closed.
The prior `O_EXCL` creation exposed the final path before writing it, so a polling transport peer could read an empty or incomplete JSON record.
The same publication path applies to new copied files and ordinary worker result records.

## Publication contract

`write_new` stages bytes in an exclusive private sibling file, then publishes that completed file with a no-overwrite rename.
No hard-link publication window is introduced; existing singly-linked regular-file and read-identity checks remain active.
A destination that already exists raises `FileExistsError` and retains its bytes.
Temporary files are removed on ordinary errors, including a competing publication.
A process killed before publication can leave a private hidden stage; it does not expose a final request or response name.
Spool size/file limits still count such files rather than hiding them from admission.

Linux uses libc `renameat2` with `RENAME_NOREPLACE`; macOS uses `renamex_np` with `RENAME_EXCL`.
The ctypes signatures declare all argument and return types.
Missing native functions and unsupported kernel/filesystem flags fail explicitly.
The implementation does not fall back to an overwriting rename or a link/unlink sequence.

Windows uses `os.rename`, which refuses an existing destination there.
This preserves ordinary result and application-parking record publication.
It does not qualify a native Windows application counterpart.
`replace=True` still intentionally replaces an existing record, after writing a complete private stage.

## Durability and platform limits

On POSIX systems the implementation also opens and syncs the containing directory after publication.
A directory-sync failure is reported even though the completed destination may already be visible.
Callers must not interpret that error as proof that no publication occurred.
Windows performs the file sync but does not claim directory-sync or sudden-power-loss durability.
A successful file/directory sync is also not a claim that every storage device has committed its volatile hardware cache.
The transport requires a private local filesystem; network filesystem crash semantics are not qualified.

## Verification

The new process fixtures run an actual application `HostQueue` and `QueueClient` in separate processes for 32 round trips with request and response payloads above 900 KiB.
A concurrent observer and six publisher processes check complete singly-linked records and one exclusive winner.
A separate publisher verifies that pre-existing destination bytes survive and temporary stages are removed.
These are filesystem/transport fixtures and make no native CAD qualification claim.

Local verification is limited to source AST checks, pinned Black, Mypy, Pyright, repository Steering, and documentation links.
No local tests or reproductions ran.
Remote Linux/macOS execution and ordinary Windows compatibility results must be recorded against the tested commit before qualification.

## Primary definitions

- [Linux rename contract](https://man7.org/linux/man-pages/man2/rename.2.html)
- [Linux rename flags](https://github.com/torvalds/linux/blob/master/include/uapi/linux/fs.h)
- [Linux directory descriptor constants](https://github.com/torvalds/linux/blob/master/include/uapi/linux/fcntl.h)
- [Apple rename definitions](https://github.com/apple-oss-distributions/xnu/blob/main/bsd/sys/stdio.h)
- [Apple exclusive volume rename support](https://developer.apple.com/documentation/foundation/urlresourcevalues/volumesupportsexclusiverenaming)
- [Python Windows rename behavior](https://docs.python.org/3/library/os.html#os.rename)
- [Linux file and directory sync](https://man7.org/linux/man-pages/man2/fsync.2.html)

The [macOS gate at `3327f7fe`](https://github.com/TryUniCAD/Kit/actions/runs/43673846094/job/132689552836) passed all fifty cases in 382.80 seconds, including three publication cases with 32 near-limit bidirectional exchanges and competing exclusive publishers. Linux process evidence and later shared-runtime changes remain unverified.
