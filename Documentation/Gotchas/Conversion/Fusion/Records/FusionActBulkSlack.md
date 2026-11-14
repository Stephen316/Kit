# Current Fusion leaves stray bytes after the final ACT record

## Expectation

The ACT segment bulk stream ends with its final record. The final record is a `RevGUIDACTDataMany` record that holds one `revGuidMap` member. A strict reader can then reject any byte after the decoded members.

## Actual behavior

Fusion 2706.1.17 often writes a few bytes after the final ACT record. Kit's bulk slicer gives the last record every byte up to the stream end. The strict reader then raised `ValueError("Unexplained trailing Fusion entity payload bytes")`.

The runtime reflection capture lists `revGuidMap` as the only own member of `RevGUIDACTDataManyMetaType`. `ACTChangeDataManyMetaType` has no own member.

Repeated native saves of unchanged documents separate the record from the extra bytes.

| Document | Save | Final record fields | Extra bytes |
| --- | --- | --- | --- |
| Fresh design | First | Reference | 0 |
| Fresh design | Second | Equal to first | 0 |
| Fresh design | After reopen | Equal to first | 2, different value |
| Plane Form | First | Reference | 2 |
| Plane Form | Second | Equal to first | 2, equal value |
| Plane Form | After reopen | Equal to first | 2, different value |

The census of 72 affected local archives found these extra byte counts.

| Extra bytes | Archives |
| --- | --- |
| 2 | 68 |
| 16 | 1 |
| 26 | 1 |
| 28 | 2 |

The bytes change between saves of equal records. They may hold uninitialized memory, so treat them as private data.

## Workaround

Read every ACT record except the last one strictly. Read the last record with `ReadSlack` and keep its unread bytes in `ParsedSegment.BulkSlack`. Write those bytes back after the last record so the stream stays byte-exact. The Design stream also keeps a tail of at most 16 bytes, as the [stream padding gotcha](../Assembly/FusionStreamPadding.md) explains. Keep the strict check for every other record.

The Browser stream has the same tail. `re/Fusion/examples/.f3z/example1.f3z` member 7 ends its Browser stream with 5,372 bytes after the last indexed record. Every metadata owner has an index entry, and the last record decodes to its own end. The tail holds 15 zero bytes and then record headers with type code `292` and object ids 21, 22 and 23. These headers are stale records of an earlier save. Kit therefore keeps a Browser tail of any length in `BulkSlack`, as it does for ACT. See the [read gap notes](../../../../../re/Fusion/Reconstruction/ReadGaps/ReadGapNotes.md#browser-stream-tail).

## Evidence

- [Slack census](../../../../../re/Fusion/Reconstruction/ActSlack/SlackCensus.json)
- [Repeated native saves](../../../../../re/Fusion/Reconstruction/ActSlack/Saves.json)
- [Native save probe](../../../../../re/Fusion/LocalOracle/ActSlack/Probe.json)
- [Runtime reflection capture](../../../../../re/Fusion/LocalOracle/Reflection/Versions.json)
- [Form document change entry](../../../../Changes/Fusion/TSpline/FusionFormDocuments.md)
