# Fusion bulletin boards can hold more than 1000 changes

## Expectation

A `delta_state` bulletin board holds at most 1000 changes. A `delta_state` record holds fewer than 4096 ASM tokens, like every other journal record.

## Actual behavior

Pattern and emboss saves write large single boards. Kit raised `ValueError("Oversized Fusion bulletin board")` for 8 files. Kit raised `ValueError("Oversized Fusion ASM record")` for 6 files.

A census of the 816 `.smbh` journals under `re/` gave these maxima.

| Measure | Maximum |
| --- | --- |
| Changes in one board | 2224 |
| Boards in one state | 1 |
| Tokens in one `delta_state` record | 6687 |
| Tokens in any other record | 3670 |
| Entities in one journal | 2427 |
| Repeats of one entity reference in one board | 1 |

No board holds more changes than its journal holds entities. Each change writes 3 tokens.

## Workaround

Bound one board by `KBoardChanges` in `ReadBoardMut`, which is 4096. This value is equal to the existing journal entity quota. Bound each journal record by `KRecordTokens` in `AsmTable`, which is 16384. This bound holds one full board at 3 tokens for each change. The reader and the writer use the same two bounds.

## Evidence

- [Record sizes](../../../../../re/Fusion/Reconstruction/ReaderCoverage/JournalStructure/BoardSizes.json)
- [Board changes](../../../../../re/Fusion/Reconstruction/ReaderCoverage/JournalStructure/BoardChanges.json)
- [Census delta](../../../../../re/Fusion/Reconstruction/ReaderCoverage/JournalStructure/CensusDelta.json)
