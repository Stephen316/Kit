# Exclusive creation is not complete publication

`O_CREAT | O_EXCL` prevents two writers from creating the same final path.
It does not keep a successful writer's empty file invisible while that writer fills and syncs it.
An application host polling for `.request`, or a client polling for `.done`, can therefore parse a partial record.

Write and sync a private sibling first, then publish it with a native atomic no-overwrite rename.
Linux requires `renameat2(RENAME_NOREPLACE)` and macOS requires `renamex_np(RENAME_EXCL)` support from the filesystem.
Windows `os.rename` already refuses replacement.
A hard-link followed by unlink is unsuitable here: readers would briefly see two links and correctly reject the file under the transport's single-link rule.

Keep the single-link and identity checks active after publication.
Report directory-sync failures without assuming the already-published destination is absent.
The [publication change](../../../Changes/Research/Workers/AtomicApplicationPublication.md) records primary API definitions, remote process fixtures and the remaining evidence limits.
