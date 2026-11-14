# The legacy Features value is not the timeline cursor

`FusionComponent.m_rFeatures` points to a legacy `Features` collection. Its `m_curFeatureId` is 1 in both the native one-sketch circle and the two-feature cylindrical/frustum controls, while its `children` collection is empty. Treating it as a zero-based current timeline index incorrectly rejects the one-sketch native save.

The qualified projector preserves and checks this empty legacy collection with its observed stored value 1. It does not infer a timeline position or assign an unproven allocator meaning to that field. Timeline completeness comes from `DcCreationOrderFeatures.representationFeatures`, the complete feature-derived entity inventory, active/suppressed/eliminated states and the body's history-state boundaries.

See the [controlled Design evidence](../../../../../re/Fusion/Reconstruction/PublicRotational/ProjectionModel.md) and [native circular projection](../../../../Changes/Fusion/Adapter/FusionNativeCircularProjection.md).
