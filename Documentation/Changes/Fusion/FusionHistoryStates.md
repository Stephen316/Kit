# Fusion history state identities

`HistoryState` now names the ASM journal values. The first two `history_stream` integers are the current state ID and the maximum allocated state ID. A rolled-back archive shows them apart. Kit names the fourth integer the next entity tag, and reads the bulletin board integer as a status enum, not a board number. Those two readings came from binary inspection. They are not confirmed by a black-box experiment.

## API and compatibility

| Previous field                     | Current field    | Meaning                                              |
| ---------------------------------- | ---------------- | ---------------------------------------------------- |
| `CurrentId`                        | `CurrentId`      | ID of the insertion delta state                      |
| `InitialId`                        | `InitialId`      | ID of the initial delta state                        |
| `Generation`                       | `CurrentStateId` | Current state of the owning history stream           |
| Implicit duplicate of `Generation` | `MaxStateId`     | Maximum allocated stream state ID                    |
| `Allocation`                       | `NextEntityTag`  | Next entity tag allocated by the history stream      |
| `BoardNumber`                      | `BoardStatus`    | `0` mainline, `1` stacked, `2` succeeded, `3` failed |

The first five positional arguments retain their order. The optional sixth argument, `MaxStateId`, defaults to the current state ID and is normalized in the immutable model. Existing keyword callers must use the corrected names. The corresponding `AuthorPolicy` names are `HistoryCurrentStateId`, `HistoryMaxStateId`, `HistoryNextEntityTag` and `HistoryBoardStatus`.

Kit bounds all state IDs and entity-tag counters to nonnegative signed 32-bit integers. The maximum state ID cannot be less than the current state ID. The qualified two-state profile still requires the insertion delta ID to follow the initial delta ID. The board status must be 0, 1, 2 or 3.

The canonical authored preamble remains `[4, 4, 0, 1, -1, 0, 1, -1]` and its board remains succeeded (`2`). Default cylinder, cuboid and frustum authoring therefore retains the same bytes. This profile keeps the third preamble integer at zero. Its reading as a retained-state limit came from binary inspection and is not confirmed by a black-box experiment. The profile also keeps its existing four reference values and rejects unsupported state layouts.

## Evidence

The rolled-back archive refutes the earlier idea that the first two values duplicate one generation or size. The earlier readings of the fourth integer as a stream identity or history-entry count were set aside on binary evidence only. The earlier reading of the board integer as an ordinal was also set aside on binary evidence only. A black-box experiment does not confirm the replacement readings.

[The read-only inventory](../../../re/Fusion/Reconstruction/JournalStates/Inventory.json) fully frames 69 distinct histories: 67 two-state and two three-state streams. The rolled-back archive stores current state `3` and maximum state `10`, with next entity tag `6`. Preserving the maximum avoids discarding allocation history during rollback.

## Verification and limits

Six added remote archive integration cases cover the rolled-back native journal and regenerated geometry with its distinct current/maximum metadata. The cases also cover three invalid board-status values and two invalid maximum-state values. Existing authored archive cases exercise the unchanged defaults. Black, Ruff, mypy, strict Pyright and repository steering checks passed the twelve changed or added production/integration modules. No local tests or production codec execution ran for this correction.

This change qualifies the corrected metadata in the existing complete two-state insertion journal. It does not add archived geometry, replacement/deletion bulletins, branching state trees, nonzero retention limits or a `-1` fourth preamble value. That variant is known only from binary inspection. The Draft and offset-cylinder streams have three states and archived revisions; their fully framed research records are not a claim of complete semantic support. See the [state-counter gotcha](../../Gotchas/Conversion/Fusion/Geometry/FusionHistoryCounters.md).

The newly readable rolled-back source also passes [native control/reconstruction comparison](History/FusionRolledHistoryAcceptance.md). The comparison includes initial marker preservation, rollback, restoration of all three future bodies, a driving-parameter edit and native save/reopen. Its former rejection expectation is replaced with positive complete-history reconstruction coverage.
