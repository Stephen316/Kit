# Fusion P04 saved sketch bindings

The archive command joins the indexed P04 sketch records to the historical Fusion capture at `89c25945f5833ad9c3a1c6c683df510b5702dd54`. It uses the same discovery split, receipt, measurement and archive verification as the cut-extent study. Run it with Python 3.14 or later. [Extent evidence](FusionCutExtentEvidence.md), [Evidence command](../../../../re/automation/FusionCutSketchEvidence.py)

```powershell
python -B re/automation/FusionCutSketchEvidence.py > FusionCutSketchEvidence.json
```

Python 3.14.6 read all eleven pinned archives. Each has six linear dimensions and ten geometric relationship records across `RectangleSketch` and `CutSketch`. The command verifies the stored constraint kinds against the historical API inventory and all 143 curve records against uniquely measured directed world endpoints. The six dimensions per archive agree with the recorded parameter name, driving state, expression and value. Representative saved operands are listed below in record order. IDs remain scoped to their source archive.

| Sketch | Stored relationship or dimension | Saved operands |
| --- | --- | --- |
| `RectangleSketch` | Two axis relations per sketch axis | Lines `232`, `238`, `244`, `248` |
| `RectangleSketch` | Coincident | Points `228`, `205` |
| `RectangleSketch` | `width_mm`, `height_mm` | Points `228`, `230` and `242`, `228` respectively |
| `CutSketch` | Two axis relations per sketch axis | Lines `393`, `396`, `399`, `400` |
| `CutSketch` | Midpoint | Point `406` and construction line `405` |
| `CutSketch` | `cut_width_mm`, `cut_height_mm` | Points `389`, `391` and `397`, `389` respectively |
| `CutSketch` | `cut_center_u_mm`, `cut_center_v_mm` | Points `428`, `406` for both |

The height and center dimensions use the same two point IDs in a different order in the dependency prefix and operand tail. The tail order matches the authored endpoint order. The P04 report explicitly enables this layout for the shared linear dimension class, the two stored horizontal or vertical codes and reversed pairs of typed points from one sketch. It keeps both orders in the output. In the YZ archive, nominal width becomes vertical in sketch coordinates and nominal height becomes horizontal. Both retain the same archive-local operand roles. [Original P04 generator](../../../../re/automation/PairedCaptures/FusionCapture.py)

Of the 66 dimension binding records, 57 also pass the measurement cache checks. Nine copied anchors disagree in the four planar size edits. For example, the boss height edit to 24 mm stores the second anchor at 20 mm and the repeated anchor at 24 mm. The evidence leaves these caches unresolved and retains both values. [Fusion dimension anchor copies](../../../Gotchas/Research/Readers/FusionDimensionAnchorCopies.md)

The baseline A and variant comparisons use recorded same-process reopens. The baseline B comparison uses the rebuild observation before its repeat export. Those API observations captured kinds and dimensions, while the saved record references establish the operands. Fresh Fusion readback of the actual constraint and dimension targets, native edit/export/reopen and exact BRep supporting-face resolution remain open.
