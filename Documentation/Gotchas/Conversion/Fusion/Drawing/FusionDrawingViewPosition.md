# Fusion places a drawing view where the DWG viewport says

## Expectation

A drawing view's position is a drawing property, so it should live in the drawing members beside the
view list and the sheet.

## Actual behavior

The position lives in the embedded DWG, in the `VIEWPORT` object's `Center`.
A view uses two viewports that share one center: the frame and the geometry.

A control changed `Center` on that pair from `(180.46875, 120.609375)` to
`(200.46875, 120.609375)`, re-emitted the DWG with `EmitDwgFile`, rebuilt the F2D and the F3Z, and
opened it in Fusion 2706.1.17.
Fusion reported every curve of the first view shifted by exactly 20 mm in x:

```
control   starts [[236.46875, 120.609375], [100.46875, 160.609375], [100.46875, 80.609375]]
moved     starts [[256.46875, 120.609375], [120.46875, 160.609375], [120.46875, 80.609375]]
```

The y values, the curve count of 5, the view counts `[5, 4, 4]`, the single dimension and the
420 by 297 mm sheet are unchanged.

## Workaround

Write `Center` on both viewports of the view and keep them equal.
The header tail is unaffected because the checksum covers the header area and not the viewport
objects, so the document's own tail stays valid.

## Evidence

| Case            | Change                        | First view starts (x)          | Open  |
| --------------- | ----------------------------- | ------------------------------ | ----- |
| `C21LayoutA1`   | none to the view geometry     | `236.46875, 100.46875, 100.46875` | 4.9 s |
| `C23ViewMove`   | `Center` +20 mm on two viewports | `256.46875, 120.46875, 120.46875` | 6.8 s |

The builder is
[`BuildViewMoveCase.py`](../../../../re/Fusion/Reconstruction/Drawings/ThirdParty/BuildViewMoveCase.py).

## Limits

The first two attempts at this case stalled at 420 s and the third opened in 6.8 s, with the same
file and the same harness. The stall was the harness, not the drawing, so a single stall is not
evidence that a view edit is wrong.

Only the active sheet's first view is compared, because the Fusion API reports curves for that view.
