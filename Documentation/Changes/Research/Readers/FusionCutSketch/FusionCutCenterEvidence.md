# Fusion P04 cut center and parameter bindings

This research command joins the saved P04 projected origin and construction midpoint to the two driving cut-center dimensions and their boss-dimension expressions. It reads the eleven discovery archives and the historical measurements pinned at `89c25945f5833ad9c3a1c6c683df510b5702dd54`. Run it from the repository root with Python 3.14 or later. [Evidence command](../../../../../re/automation/FusionCutCenterEvidence.py)

```text
python -B re/automation/FusionCutCenterEvidence.py > FusionCutCenterEvidence.json
```

The `CutSketch` projection controller references the origin through two typed paths. Its source proxy and descriptor reach leaf `416`. Its output entry and naming record reach leaf `427`. Both leaves name origin point `38`, which belongs to origin container `37` and reciprocally owned root component `3`. The entry names output point `428`. Points `332` and `379` share its coordinates in all eleven archives. The controller and both dimension records distinguish the selected point by identity. The cached projection agrees with the verified support cap, world frame and historical sketch origin. The proof covers baseline `[0, 0, 10]` mm, boss-depth edit `[0, 0, 12]` mm and YZ `[10, 0, 0]` mm. [Saved face and world frame](../FusionCutFaceEvidence.md), [Coincident projected points](../../../../Gotchas/Research/Readers/FusionCutOriginPointIdentity.md)

Both center dimensions use point `428` followed by point `406`. The saved midpoint relation names point `406` and construction diagonal `405`. The saved midpoint agrees with the center calculated from the historical API's measured construction-line endpoints. The previous sketch evidence retains all six dimension bindings, their operand orders and their separate annotation-cache diagnostics. [Saved sketch and dimension operands](../FusionCutSketchEvidence.md)

The saved expression `width_mm / 2` resolves through the root component's reciprocal parameter name registry to the parameter for the boss width dimension. The expression `height_mm / 2` resolves to the parameter for the boss height dimension. Both correspondences agree with the historical API's `dependencies` and `dependents` name lists. Across 22 bindings, saved scalar values, historical parameter values and absolute local operand separations agree. The YZ width and height orientations are vertical and horizontal, with signed center separations of 20 and −10 mm. The signed separation comes from the saved ordered point coordinates. [Saved expression parser](../../../../../re/Fusion/Study/decode_expression_dependencies.py)

| Historical source control | Center U (mm) | Center V (mm) | Center in world millimeters |
| --- | ---: | ---: | --- |
| Baseline A and B | 20 | 10 | `[20, 10, 10]` |
| Boss width 44 mm | 22 | 10 | `[22, 10, 10]` |
| Boss height 24 mm | 20 | 12 | `[20, 12, 10]` |
| Boss depth 12 mm | 20 | 10 | `[20, 10, 12]` |
| YZ support | 20 | 10 | `[10, 20, 10]` |
| Three cut-size edits, inch display and through-all | 20 | 10 | `[20, 10, 10]` |

Direct inspection of the pinned archives produced eleven origin paths, eleven midpoint constraints and 22 name-resolved bindings. The saved projected-cap-edge report retained its previous SHA-256 `953d58343825f8e657b7fa4cafcf2513f99a96d6f1a948688904609536638cb8`. [Projected cap edges](../FusionCutProjectionEvidence.md)

The saved dependency correspondence derives from parsed expression text and the reciprocal registry. A separate serialized expression dependency table remains unresolved. The historical API recorded parameter getter names, expressions, sketch frames and construction-line endpoints. It did not record projection source identity or live dimension and relation participants. Fresh-process readback and editable acceptance remain open. [Pinned capture provenance](../../../../Reference/Research/PinnedCorpus.md)
