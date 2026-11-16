# History audit output encoding and bounded default selection

## Expectation

A pinned history inventory should survive redirection on Windows without altering Unicode source identities or its canonical payload digest.
Directory defaults should either fit the declared source budgets or explain why the selection must be narrowed.

## Actual behavior

The [licensed operator's report](https://github.com/TryUniCAD/Kit/pull/94#issuecomment-6925944949) found that a combining character in an unescaped JSON path could fail stdout encoding on Windows.
The same report found 103,511,341 selected bytes and five files above the 4 MiB individual limit in its default snapshot.
An explicit eight-file selection completed; it is evidence for that selected scope, not a completed default inventory.

Git tree metadata at `2817a2e90c2ffcf107cad3340021f4a037d12981` identifies 1,394 eligible files totaling 103,579,917 bytes.
The five oversized files are captured outputs under `re/Fusion/LocalOracle/FormDocuments/`:

| Relative path                           |      Bytes |
| --------------------------------------- | ---------: |
| `CageDocuments/NativeAcceptance.json`   | 22,162,376 |
| `StencilAccept/NativeAcceptance.json`   | 17,731,260 |
| `FourthDocuments/NativeAcceptance.json` | 15,699,123 |
| `Sourceless/NativeAcceptance.json`      |  5,995,717 |
| `MergeDocuments/NativeAcceptance.json`  |  4,706,694 |

These figures come only from committed tree metadata; no audit, source-blob scan, tests or CAD process ran locally to establish them.
The later revision and the operator's earlier totals are distinct snapshots.

## Workaround and repair

The audit emits ASCII-escaped JSON on stdout and escaped refusal text on stderr.
Parse the JSON normally to recover the original Unicode path.
Recompute `report_sha256` from the payload without that field using sorted keys, compact separators, `ensure_ascii=False` and UTF-8 encoding.
The stdout presentation uses `ensure_ascii=True`; hashing the displayed report bytes is not the payload digest algorithm.

The command checks selected file counts, sizes and total bytes from tree metadata before reading selected source blobs.
Over-budget selections refuse with an empty stdout, selected totals and up to eight oversized examples.
Repeat `--path` for reviewed repository-relative files or directories that fit the existing limits.
Retain the exact selectors with the resulting report and review omitted pin-bearing sources separately before making any broader claim.
No oversized file is silently omitted, no cap is raised and no partial inventory is accepted.

ASCII-only real-process integration cases cover Unicode source paths, canonical digest preservation and oversized-path refusal.
Those cases require hosted execution; local validation is limited to static checks.
