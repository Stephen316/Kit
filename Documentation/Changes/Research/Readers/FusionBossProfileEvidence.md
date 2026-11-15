# Fusion P03 saved boss profile and rectangle bindings

The P03 archive command follows the saved boss's profile from its owned proxy to the same rectangle whose support plane and operands the sketch reader verifies. It uses the eight P03 discovery exports and original historical measurements pinned at `89c25945f5833ad9c3a1c6c683df510b5702dd54`. Run it with Python 3.14 or later. [Evidence command](../../../../re/automation/FusionBossProfileEvidence.py), [P03 signed direction evidence](FusionBossDirectionEvidence.md)

```powershell
python -B re/automation/FusionBossProfileEvidence.py > FusionBossProfileEvidence.json
```

All eight native sketches match the [P01 rectangle layout](FusionRectangleSketchEvidence.md). The sketch owns a counted descriptor that leads through a typed leaf to the XY or YZ plane in its component's origin container. The same component owns its sketch transform and identity root occurrence. The saved plane name matches the historical API's support name, and the archived measured sketch axes give the same normal and world frame. The original P03 measurement records directed world lines directly, while its numeric width and height come from the archived document parameter table.

The saved `BlindBoss` feature `277` owns profile proxy `278`. Its dependency list repeats the proxy and descriptor `281`, which independently names `RectangleSketch` definition `202`. The typed loop record `284` points back to that descriptor. Its single outer loop contains all four measured perimeter lines through explicit native curve tags. The audit retains stored membership order. [Fusion profile member order](../../../Gotchas/Research/Readers/FusionBossProfileMemberOrder.md)

| Control | Selected origin plane | Sketch dimension orientation | Stored boss extent | Stored loop member IDs |
| --- | --- | --- | --- | --- |
| Baseline A | XY | Width horizontal, height vertical | `+Z`, `+1.0 cm` | `248,238,244,232` |
| YZ | YZ | Width vertical, height horizontal | `+X`, `+1.0 cm` | `248,232,238,244` |
| Negative direction | XY | Width horizontal, height vertical | `+Z`, `−1.0 cm` | `232,248,238,244` |

Python 3.14.6 verified all eight archives. Thirty-two directed lines agree with the historical world measurements, and the explicit saved records bind 40 geometric relationships and 16 ordered dimensions. Fifteen dimension caches pass. The height-edit cache still contains conflicting 20 mm and 23 mm anchors, with the measured dimension and profile agreeing at 23 mm. Fresh API relation and dimension targets, live selected-profile identity, load diagnostics and editable acceptance remain open.
