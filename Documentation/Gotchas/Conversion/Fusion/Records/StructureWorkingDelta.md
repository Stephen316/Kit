# Fusion can save a journal with an open working delta state

## Expectation

The `history_stream` record of a saved `.smbh` journal has `WorkingNode` equal to `-1`. The active delta state then has the `StateId` that `CurrentStateId` names.

## Actual behavior

Nine path-pattern saves set `WorkingNode` to the same node as `ActiveNode`. Kit raised `ValueError("Unsupported Fusion history stream variant")` for these journals.

The working node is an open delta state that has not closed. All nine occurrences have the same shape.

| Field | Value in all 9 journals |
| --- | --- |
| Working `StateId` | `0` |
| Working bulletin boards | 1 board with 0 changes |
| Working `NextNode` | The closed state that `CurrentStateId` names |
| `MaxStatesToKeep` | `0` |
| `OwnerEntity` | `-1` |

The other 744 readable journals keep `WorkingNode` at `-1`.

## Workaround

Accept `WorkingNode` only when it is `-1` or equal to `ActiveNode`. When it is set, `CheckWorking` requires `StateId` `0`, one empty board, and a `NextNode`. Compare `CurrentStateId` with the state that `NextNode` names. Reject every other working-node shape.

## Evidence

- [Stream variants](../../../../../re/Fusion/Reconstruction/ReaderCoverage/JournalStructure/StreamVariants.json)
- [Census delta](../../../../../re/Fusion/Reconstruction/ReaderCoverage/JournalStructure/CensusDelta.json)
