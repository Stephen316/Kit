# Construction planes do not take a journal state

## Expectation

Every timeline feature owns one BRep journal state and a start and end state index.
The feature name sits on `DcFeature.featureUserName`, as it does for extrusions, holes and patterns.
The origin planes use the frames that their names suggest.

## Actual behavior

A native offset plane is a timeline feature without a model state.
After a solid feature, it still consumes one operation identifier.
In the native `MirrorFeature` control, the plane takes 306 between the pocket and the mirror.

| Field                                  | Native offset plane                                      |
| -------------------------------------- | -------------------------------------------------------- |
| `DcFeature.startModelHS`               | −1                                                       |
| `DcFeature.endModelHS`                 | −1                                                       |
| `DcFeature.featureUserName`            | Empty                                                    |
| `WorkGeometry.userName`                | The plane name, such as `Mid plane`                      |
| `WorkGeometry.id`                      | The new `WorkGeometries.highWaterMarkPlanes` value       |
| `DRMatrix.matrix3d`                    | Row-major columns u, v, normal and translation           |
| Next solid feature state               | The state after the previous solid feature               |

The native origin plane frames are fixed.

| Origin plane | u axis    | v axis    | Normal    |
| ------------ | --------- | --------- | --------- |
| XY           | (1, 0, 0) | (0, 1, 0) | (0, 0, 1) |
| YZ           | (0, 1, 0) | (0, 0, 1) | (1, 0, 0) |
| XZ           | (0, 0, 1) | (1, 0, 0) | (0, 1, 0) |

The XZ frame differs from a frame built as x-axis by z-axis.
The offset matrix of a 20 mm YZ plane has the translation (2, 0, 0) cm.

## Workaround

Kit treats the plane as stateless.
It writes −1 for both state indices and does not advance the state counter.
It stores the name on the work plane and copies the native frames.
A mirror after the plane takes the next state, so the `MirrorFeature` part has states 4, 5, 5 and 6.

The [native offset plane control](../../../../../re/Fusion/LocalOracle/FeatureAuthoring/Controls/OffsetPlane.f3d) and the [family records](../../../../../re/Fusion/Reconstruction/FeatureAuthoring/FamilyRecords.json.xz) preserve the records.
