# Rectangle dimensions do not anchor its position

Width and depth dimensions constrain size, but they do not fix a rectangle's translation or prevent every orientation freedom. In the initial native control, editing depth moved the lower edge while preserving the upper edge. A rectangle corner whose coordinates equal the sketch origin is still a different entity; coordinate equality creates no coincident constraint.

The qualified fully constrained profile fixes the actual lower-left corner and adds horizontal/vertical constraints to all four lines before attaching two driving dimensions. It fixes `Point3D.isFixed` on that corner. The separate origin point remains unchanged. No additional fixed-point constraint entity is created by this native operation.

The saved corner `isFullyConstrained` flags remain false even when the native sketch API reports the entire sketch fully constrained. These fields are not a substitute for solver acceptance and must not be rewritten merely to make them agree with the sketch result.

Dimension construction also crosses two namespaces before its continuation boundary. `FusionSketchLinearDim` and `SketchDimension` remain in the same primary record although their class namespaces are `Fusion` and `MSketch`. The continuation starts at `Dimension`, not at the first namespace change. A generic namespace split alone is insufficient for this hierarchy.

The [controlled differential model](../../../../../re/Fusion/Reconstruction/SketchConstraints/ConstraintModel.md) distinguishes fixed-point, geometric-constraint and dimension changes. [Independent native acceptance](../../../../../re/Fusion/LocalOracle/DimensionAuthoring/NativeAcceptance.json) verifies fully constrained, origin-stable editing and save/reopen for the [opt-in writer](../../../../Changes/Fusion/FusionConstrainedRectangles.md).
