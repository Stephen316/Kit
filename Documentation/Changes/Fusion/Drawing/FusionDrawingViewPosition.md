# Drawing view position is written in the DWG viewport

## Problem

Kit had no recorded evidence that a view position it writes reaches Fusion. The position is not a
drawing member: it lives in the embedded DWG, in the `VIEWPORT` object's `Center`, and a view uses two
viewports that share one center.

## Change

The finding is recorded, with a control and a case that differ in one input, in the
[view position gotcha](../../../Gotchas/Conversion/Fusion/Drawing/FusionDrawingViewPosition.md).

`BuildViewMoveCase.py` moves the viewport pair of the first view by 20 mm in x on `D1FreshLayout`,
re-emits the DWG, and rebuilds the F2D and the F3Z.
`BeginUploads.py` reads the plan file it writes.

## Behavior

| Case            | Change                            | First view starts (x)             | Open  |
| --------------- | --------------------------------- | --------------------------------- | ----- |
| `C21LayoutA1`   | none to the view geometry         | `236.46875, 100.46875, 100.46875` | 4.9 s |
| `C23ViewMove`   | `Center` +20 mm on two viewports  | `256.46875, 120.46875, 120.46875` | 6.8 s |

Every x moved by exactly 20.0 and every y stayed the same. The curve count, the view counts
`[5, 4, 4]`, the single dimension and the 420 by 297 mm sheet are unchanged.

No reader or writer code changes. The edit keeps the document's own header tail valid because the
checksum covers the header area and not the viewport objects.

## Verification

`C23ViewMove` was built from `D1FreshLayout` by rewriting `Center` on the two viewports that share
`(180.46875, 120.609375)`, then re-emitting the DWG. The emitted DWG reads back with
`(200.46875, 120.609375)` on both, and Fusion reported the matching curve shift.

The control is the same source with only the sheet layout changed, so its view geometry is the
untouched source geometry.

## Limits

The first two attempts at this case stalled at 420 s and the third opened in 6.8 s with the same file
and harness, so a single stall is not evidence that a view edit is wrong.

Only the active sheet's first view is compared, because the Fusion API reports curves for that view.
