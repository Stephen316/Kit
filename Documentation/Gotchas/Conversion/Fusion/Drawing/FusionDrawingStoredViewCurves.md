# A drawing shows the view curves stored in its DWG

Fusion 2706.1.17 does not recompute view curves when it opens a drawing.
It shows the curves that the DWG stores in the anonymous `*S` view blocks.
A view whose block holds no curves opens with no curves.

`D2NoViewCurves` starts from the full A1 control.
The other variants start from the A1 control without unused blocks.

| Variant          | Change                                                             | Open time | Curves per view |
| ---------------- | ------------------------------------------------------------------ | --------- | --------------- |
| `D5NoUnusedBlocks` | None beyond the base                                             | 32.6 s    | 5, 4 and 4      |
| `D2NoViewCurves` | Lines, circles and arcs removed from the `*S` blocks               | 371.7 s   | 0, 0 and 0      |
| `E8StaleRevision` | Curves removed and the body revision in the view source changed   | 4.9 s     | 0, 0 and 0      |
| `E7StaleBrep`    | As `E8StaleRevision`, and the tracked body version in the segment set to 0 | 43.1 s | 0, 0 and 0  |

Every variant kept its dimension, and its document reference was not out of date.

A stale body revision did not make Fusion recompute the views on open.
Fusion recomputes view curves when `updateAllReferences()` updates an out-of-date reference.
The [reference update gotcha](FusionDrawingReferenceUpdate.md) records that update.

Kit's DWG author writes empty `*S` view blocks.
No drawing written by that author has opened in Fusion, as the [header tail gotcha](FusionDrawingHeaderTail.md) records.
How Fusion shows those empty views is therefore not observed.
