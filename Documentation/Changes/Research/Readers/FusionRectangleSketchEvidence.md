# Fusion P01 saved rectangle plane and sketch bindings

The P01 archive command reads the six discovery exports pinned at `89c25945f5833ad9c3a1c6c683df510b5702dd54` and verifies the original paired receipt and measurements before comparing them with saved native records. Run it with Python 3.14 or later. [Evidence command](../../../../re/automation/FusionRectangleSketchEvidence.py), [Original P01 capture generator](../../../../re/automation/PairedCaptures/P01/GenerateFusion.py)

```powershell
python -B re/automation/FusionRectangleSketchEvidence.py > FusionRectangleSketchEvidence.json
```

All six archives connect `RectangleSketch` feature `207` and definition `202` through reciprocal owner references. The sketch-owned controller `215` repeats the counted selection of descriptor `211`, which owns typed leaf `214`. The leaf explicitly names origin plane `42` for the five XY captures and `44` for YZ. The selected plane belongs to counted origin container `37`, which references Component `3` in both directions. The component also owns the saved sketch transform and identity document root. The report keeps original indexed classes, offsets and digests throughout this chain.

The selected plane name and normal agree with the original Fusion API getters in all six cases. The root-composed sketch origin and directed X and Y axes also agree. In YZ, the selected plane normal is `+X`. The plane's native X/Y axes are `+Y` and `+Z`, while the sketch's local X/Y axes are `−Z` and `+Y`. All 24 directed lines agree after placing the measured local API endpoints with their respective recorded sketch frames. [P01 sketch endpoint coordinates](../../../Gotchas/Research/Readers/FusionRectangleSketchCoordinates.md)

The command records five geometric relationships and two point dimensions in each file. The archived Fusion inventory independently corroborates the relation kinds, driving status, dimension names, expressions, measured values and areas. The serialized arguments establish the actual saved operands.

| Saved operand | Record references |
| --- | --- |
| Coincident corner and separate point at the sketch origin | Points `228`, `205` |
| Four local axis relations | Lines `232`, `238`, `244`, `248` |
| `width_mm` | Ordered points `228`, `230` on line `232` |
| `height_mm` | Ordered points `242`, `228` on line `248`, with reversed dependency-list order |

The YZ control makes width vertical and height horizontal in the saved sketch basis. Width `41 mm` produces `820 mm²` and height `23 mm` produces `920 mm²`. The baselines, inch display and YZ produce `800 mm²`. Eleven of twelve dimension measurement caches pass. The height-edit cache retains a `20 mm` second anchor and a `23 mm` repeated anchor, so its cache remains unresolved while its attached parameter and profile measurements agree. [Dimension anchor copies](../../../Gotchas/Research/Readers/FusionDimensionAnchorCopies.md)

Python 3.14.6 processed all six archives. The receipt SHA-256 is `88ca575b5176e61cd25d585c9cb6804d6ea2c1b3d3ef843ac2d2bcb43593a4db` and its measurement SHA-256 is `b72ced596918c120921beca92ffaa1febb808d7c30320682083e263e75a26906`. The baseline B comparison uses the observation before its repeat export. The other comparisons use the historical same-process reopen observations. Live API relation and dimension target matches, fresh-process Fusion readback and editable acceptance remain open.
