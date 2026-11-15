# Fusion applies a view scale that Kit writes into the DWG

## Expectation

A drawing view's scale is a drawing property, so it should live in the drawing members beside the
sheet name and the view list.

## Actual behavior

The scale lives in the embedded DWG, in two places that must agree:

| Object       | Field                        | Control value | Written value |
| ------------ | ---------------------------- | ------------- | ------------- |
| `DRAWINGVIEW` | `ViewScale`                 | `4.0`         | `2.0`         |
| `SCALE`       | `ScaleName`, `PaperUnits`   | `4:1`, `4.0`  | `2:1`, `2.0`  |

A control changed those fields on `D1FreshLayout`, re-emitted the DWG with `EmitDwgFile`, rebuilt the
F2D and the F3Z, and opened it in Fusion 2706.1.17.
Fusion reported the new scale on the active sheet's first view:

```
control   scales [4.0, error, error]   views [5,4,4]   sheet 420.0 x 297.0   open 4.9 s
written   scales [2.0, error, error]   views [5,4,4]   sheet 420.0 x 297.0   open 240.6 s
```

The two `error` entries are Fusion refusing to read a scale for the projected views, and the control
shows the same two errors, so they are not caused by the edit.

## Cost of the edit

The open took 240.6 s against 4.9 s for the control.
Fusion regenerates the view geometry for the new scale, and that regeneration dominates the open.
A run that changes a scale needs a stall budget well above the usual one, or it will report a stall
for a file that is still working.

## Workaround

Write both the `DRAWINGVIEW` field and the `SCALE` object, and keep them equal.
The header tail is unaffected because the checksum covers the header area and not the view objects,
so the document's own tail stays valid.

## Evidence

| Case              | Change                        | First view scale | Open    |
| ----------------- | ----------------------------- | ---------------- | ------- |
| `C19ControlRaw`   | none, the source bytes        | `4.0`            | 4.9 s   |
| `C22ViewScale2`   | `ViewScale` and `SCALE` to 2  | `2.0`            | 240.6 s |

The builder is
[`BuildViewScaleCase.py`](../../../../re/Fusion/Reconstruction/Drawings/ThirdParty/BuildViewScaleCase.py).

## Limits

Only the active sheet's first view reports a scale through the Fusion API, so this control shows one
view and not all thirteen. The other two views on that sheet refuse a scale read in both the control
and the case.
