# Controlled rectangular sketch constraints

Nine native Fusion captures now isolate horizontal/vertical line constraints, a fixed corner, two driving dimensions and a subsequent width/depth edit. They extend the earlier dimension model with enough explicit constraints to make the native sketch fully constrained and keep the lower-left corner at the origin.

Each line constraint adds one `SketchGeomConstraint` version-3 entity. Horizontal and vertical types are `uint64` values 64 and 128. The entity owns a passive line reference and observes that line; the sketch owns the constraint through its separate constraints collection. Fixing the corner changes the existing point's `isFixed` flag and adds no constraint entity.

The final native 17×23 mm rectangle becomes 19×29 mm through user parameters, remains fully constrained and preserves its anchor. All nine Design streams decode completely: 2,360 records and 224,888 payload bytes, with no unexplained suffix. These captures are research evidence; independently authored dimensional documents require separate native acceptance.

Use [CaptureRectangleConstraints.py](../../../re/Fusion/LocalOracle/CaptureRectangleConstraints.py) through the documented native oracle only when a new controlled capture is needed. Use [InspectConstraints.py](../../../re/Fusion/Reconstruction/SketchConstraints/InspectConstraints.py) for read-only differential analysis. The [native report](../../../re/Fusion/LocalOracle/RectangleConstraints/Capture.json), [digest inventory](../../../re/Fusion/Reconstruction/SketchConstraints/ConstraintSummary.json) and [detailed model](../../../re/Fusion/Reconstruction/SketchConstraints/ConstraintModel.md) bind the result to exact artifacts.

[Point constraint flags](../../Gotchas/Conversion/Fusion/Sketch/FusionPointConstraintFlags.md) explain why point-level persisted flags are insufficient to infer the sketch solver result. No production behavior or acceptance gate is changed by this research addition, and no local automated tests were run.
