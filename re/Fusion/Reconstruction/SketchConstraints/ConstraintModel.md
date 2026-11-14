# Rectangular sketch orientation, fixed anchor and dimensions

## Evidence and scope

`CaptureRectangleConstraints.py` creates one fresh native Fusion 2706.1.17 document and saves nine successive controlled states. The starting rectangle is 17 × 23 mm. Four orientation constraints, one fixed corner and two driving dimensions make it fully constrained. Editing the user parameters to 19 × 29 mm preserves its lower-left corner at the origin and produces exactly those dimensions. The capture closes its document and restores the previously active document.

`InspectConstraints.py` reads each saved Design stream through the research decoder. All 2,360 physical records and 224,888 payload bytes are consumed with no unexplained suffix. `ConstraintSummary.json` binds each source archive to its digest and records class-level deltas; `ConstraintGraphs.json.xz` contains complete typed groups, schemas and field differences. These are native captures and read-only research evidence, not acceptance of a new production writer.

## Stage inventory

| Stage                | Physical records | Primary entities | Payload bytes | Native geometric constraints | Native dimensions | Native fully constrained |
| -------------------- | ---------------: | ---------------: | ------------: | ---------------------------: | ----------------: | ------------------------ |
| Baseline             |              256 |              232 |         24069 |                            0 |                 0 | false                    |
| Orientation1         |              257 |              233 |         24196 |                            1 |                 0 | false                    |
| Orientation2         |              258 |              234 |         24323 |                            2 |                 0 | false                    |
| Orientation3         |              259 |              235 |         24450 |                            3 |                 0 | false                    |
| Orientation4         |              260 |              236 |         24577 |                            4 |                 0 | false                    |
| FixedAnchor          |              260 |              236 |         24577 |                            4 |                 0 | false                    |
| WidthDimension       |              266 |              240 |         25570 |                            4 |                 1 | false                    |
| WidthDepthDimensions |              272 |              244 |         26563 |                            4 |                 2 | true                     |
| EditedDimensions     |              272 |              244 |         26563 |                            4 |                 2 | true                     |

## Geometric constraint record

Each horizontal or vertical line constraint adds one primary `SketchGeomConstraint` entity, class `60403D47-0C49-49B0-BDE8-1679608164A2`, schema version 3. It derives directly from the base entity class and has no separate continuation in these controls. Its complete physical payload is 116 bytes. The owning sketch gains one local reference, giving a total Design payload increase of 127 bytes per constraint.

The own member order is:

| Member           | Native type                           | Observed meaning                               |
| ---------------- | ------------------------------------- | ---------------------------------------------- |
| `ParentNode`     | passive entity reference              | owning `MSketch`, identity 202 in this capture |
| `constraintType` | `uint64` enum                         | 64 for horizontal; 128 for vertical            |
| `geometries`     | vector of passive geometry references | one constrained `Line3D`                       |
| `isVisible`      | Boolean                               | false in all four native captures              |

All four members carry persistence option mask 51. The entity frame has no root name, one subject referring to the same line, observer index zero, and named `EntityGenesis` metadata with `uint64` value 2. Each line receives its own constraint, so index zero here is local to four different observed entities; it is not a universal global observer slot.

The bottom, right, top and left lines have identities 236–239. New constraint identities 245–248 use types 64, 128, 64 and 128 respectively. `MSketch.constraints` lists these four entities in insertion order. Driving dimensions remain in the separate `MSketch.dimensions` collection and are not counted as geometric constraint entities.

## Fixed anchor

Setting the lower-left corner's native `isFixed` property does not add a constraint entity. The physical record and primary entity counts remain unchanged. It changes the existing `Point3D` identity 228's own `isFixed` field from false to true. Its coordinates remain `(0,0,0)` and its two curve uses remain attached to the existing lines.

The sketch already has a distinct origin `Point3D`, identity 205, whose `isOrigin`, `isFixed` and `isFullyConstrained` fields are true. A rectangle corner at identical coordinates remains a different entity; coordinate equality does not create an identity join or a coincident constraint. The native fixed-corner operation anchors the actual rectangle point, not only the separate sketch origin.

`Point3D` version 11 member order is `curveUses`, `isCachedProjected`, `isCoincident`, `isConstraintOnPlane`, `isFixed`, `isFullyConstrained`, `isOrigin`, `isProjected`, `lowerSelectionPriority`, `point`, `specialType`. The first is a strong reference, the next eight are Booleans, `point` is a typed AcGe three-double point and `specialType` is `uint32`.

A subtle distinction is that all four non-origin corner records retain persisted `isFullyConstrained=false`, even after the native sketch API reports `isFullyConstrained=true`. The fixed corner's `isFixed=true` is persisted. The whole-sketch solver result must not be inferred by reading each point's cached flag or by forcibly changing those flags during authoring.

Fixing the point also causes normal native regeneration: the sketch body ID, passive ID allocator, cache identities, timestamps and package part names change. Those are distinct from the one semantic constraint change. The paired graph records make this regeneration explicit rather than treating every differing byte as a fixed-point field.

## Driving dimensions and edit behavior

Width and depth dimensions use the previously decoded `FusionSketchLinearDim`, `Dimension` continuation, model `Parameter`, `DcDoubleParameter` plus `ManagedEntity` continuation and `DynamicUpdateData` graph. Each adds six physical records representing four logical entities. The width type is 4194304 and the depth type is 8388608. The model parameter expressions reference `controlledWidth` and `controlledDepth` user parameters.

The fixed anchor and four line constraints remove shape translation and skew freedoms. After the dimensions are added, native `sketch.isFullyConstrained` becomes true. Changing the inputs to 19 mm and 29 mm produces corner coordinates `(0,0)`, `(1.9,0)`, `(1.9,2.9)` and `(0,2.9)` in stored centimetres. The three non-anchor corners change; the anchor does not. Each `Line3D` callback updates its starting point and displacement while keeping the same endpoint identities. A line displacement is dimensional and need not have unit length.

Without the anchor, the earlier dimensional capture moved the lower edge to satisfy the depth edit while preserving the upper edge. The new control establishes the additional semantics needed for predictably placed, fully constrained authoring. It does not by itself establish that the independent document writer emits those records correctly; that requires a separate generated artifact and native acceptance.
