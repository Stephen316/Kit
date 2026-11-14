# A fully constrained sketch can retain false point flags

A reader might expect `Point3D.isFullyConstrained` to match whether the native sketch solver considers a corner constrained. In the controlled rectangle, all four non-origin corner records retain `isFullyConstrained=false`. The records keep that value even after four line orientation constraints, a fixed corner and two dimensions make native `sketch.isFullyConstrained` true.

The fixed corner instead persists `isFixed=true` on its existing point record. No new geometric constraint entity is added. The sketch's distinct origin point already has both flags true, but a separate corner at the same coordinates is not automatically anchored to that origin.

Preserve the recorded point fields, resolve actual constraint/dimension relationships, and use the native solver result for acceptance. Do not synthesize solver state by setting every point's cached flag to true or by merging distinct same-coordinate points.

The [controlled capture](../../../../../re/Fusion/LocalOracle/RectangleConstraints/Capture.json) records native solver state at every stage. The [typed differential model](../../../../../re/Fusion/Reconstruction/SketchConstraints/ConstraintModel.md) identifies the exact persisted fields and coordinate changes.
