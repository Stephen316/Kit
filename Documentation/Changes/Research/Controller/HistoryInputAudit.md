# Pinned Git history input audit

## Behavior

`re/automation/HistoryInputAudit.py` inventories literal lowercase forty-character Git object IDs in a committed source snapshot.
It distinguishes local commits, blobs, trees, tags and unavailable objects.
References retain their source path, line and byte column.
Longer hexadecimal values do not become shortened Git pins.

For each commit, the report lists every DLL or DMG path in that commit's tree.
It records whether the commit is an ancestor of the explicitly selected main revision.
A negative result in a shallow clone remains unavailable evidence.
For each referenced blob, the report lists its paths in the selected head.

Sealed paired-capture paths are compared through their Git object IDs, file modes and lengths.
The report distinguishes unchanged, changed and missing paths.
These comparisons read tree metadata, not native document contents.
The command never reads vendor payloads, starts CAD, fetches missing objects or changes Git refs.
Replacement refs are disabled during the audit.
Inherited Git repository overrides and legacy graft files cannot redirect the selected repository or its ancestry.

## Usage

Use Git 2.49 or later and Python 3.11 or later.
The repository must contain both selected commits and the source blobs to inspect.

```sh
python3 re/automation/HistoryInputAudit.py --revision HEAD --main refs/remotes/origin/main
```

The default source selection covers research automation, SOLIDWORKS writer research, Fusion local-oracle source and research verification fixtures.
Repeat `--path` to replace that selection with normalized repository-relative files or directories.
Only supported source and configuration extensions are read.
Each file is limited to 4 MiB.
The complete selection is limited to 4,096 files, 64 MiB, 8,192 distinct IDs and 100,000 references.
Each metadata response is limited to 16 MiB.
All Git reads share a 256 MiB limit and a 180-second command budget.
An exceeded limit produces an error instead of a partial inventory.
File count, total bytes and oversized files are checked together from Git tree metadata before any selected source blob is read.
A refused selection reports those totals and up to eight oversized file paths and sizes, then requires reviewed explicit `--path` selectors.
Captured JSON reports remain part of directory selections; the command never silently excludes them or expands its limits.
At `2817a2e90c2ffcf107cad3340021f4a037d12981`, the default selection contains 1,394 supported files and 103,579,917 bytes, including five `NativeAcceptance.json` files above 4 MiB.
That default is intentionally refused; a narrower inventory describes only its explicit selected paths.

The output is deterministic JSON with a SHA-256 over its canonical payload.
Stdout escapes non-ASCII characters so redirected Windows output and restrictive console encodings can carry every path.
The digest still uses the decoded payload serialized as canonical UTF-8 JSON with unescaped Unicode; presentation escaping does not change its definition.
Exit code `0` means the inventory completed.
Exit code `1` means an input, limit or Git metadata operation was refused.
An unavailable object remains an explicit inventory item.
It does not prove that the literal was intended as a local commit pin.

## Verification and limitations

The new process coverage creates independent Git objects and invokes the standalone command.
It covers retained forbidden paths, replacement refs, blob identity, capture-path comparisons, deterministic output and refused selectors or oversized input.
Additional real-process cases run with ASCII-only stdout, preserve a decomposed Unicode source path and recompute the canonical UTF-8 digest.
Oversized ASCII and Unicode paths verify metadata-only refusal diagnostics without partial stdout.
Pinned formatting, type, steering, path, rationale, binary-range and whitespace checks validate the repair statically.
No local tests or collection ran.
Hosted execution remains required for the change revision.
The [Windows output and bounded-selection gotcha](../../../Gotchas/Ci/Commands/HistoryAuditOutputEncoding.md) records the reported operator failure and exact metadata-only findings.

The audit reports dependencies for review.
It neither rewrites history nor supplies replacement provenance.
It does not qualify native models or authorize redistribution of historical vendor software.
The [pinned-capture history gotcha](../../../Gotchas/Git/PinnedCaptureVendorHistory.md) records the observed boundary.
The source uses Git's documented [object metadata](https://git-scm.com/docs/git-cat-file), [tree inventory](https://git-scm.com/docs/git-ls-tree), and [ancestry queries](https://git-scm.com/docs/git-merge-base).
