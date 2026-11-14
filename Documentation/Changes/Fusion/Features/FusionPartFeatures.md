# Independent part features

`DocumentSpec.Features` adds an ordered sequence of parametric part features to an independently authored part. Each feature becomes a native Fusion timeline item with its own parameters. `EmitDocument` writes a fresh Design graph, a solved multi-state BRep journal and an exact mass cache. No captured record, source archive or donor geometry is a runtime input.

A part starts from a sketch extrusion with `ProfileKind="part"`, or from the unconstrained cuboid with `ProfileKind="cuboid"`. The part profile supports sketch extrusions, revolves, holes, rectangular and circular feature patterns, offset construction planes and mirrors. It also supports construction axes on vertical body edges and construction points on their bottom vertices. Both profiles support fillets, chamfers and shells. A hole can add a counterbore or a countersink. A shell can also open a connected run of straight side faces. A move turns the body about the Z axis and then translates it. An offset face moves the top face or one straight side face along its normal. A draft tilts every straight side face about the bottom face. A fillet or chamfer can round or cut several vertical edges, and a chamfer can take two distances or a distance and an angle. With `LevelMm`, a fillet or chamfer rounds or cuts horizontal edges instead, lines or arcs, along their tangent chains, as [edge rounds](FusionEdgeRounds.md) describes.

A part can also hold several bodies. A later `new` extrusion or `new` revolve adds a body. A combine joins, cuts or intersects bodies. A split cuts a body in two along an offset plane. A body pattern copies a whole body along a grid or around the Z axis. A loft joins two parallel profiles as a new body. A sweep moves a rectangle along a path of lines and arcs as a new body. A paste copies a visible body in place, as [body copy and paste](FusionBodyPaste.md) describes.

## Usage

```python
from pathlib import Path

from convert.formats.Fusion.DocumentCodec.EmitDocument import EmitDocument
from convert.formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.ArcCurve import ArcCurve
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.ExtrudeSpec import (
    ExtrudeSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.FilletSpec import (
    FilletSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.HoleSpec import HoleSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.LineCurve import (
    LineCurve,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.MirrorSpec import (
    MirrorSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PatternSpec import (
    PatternSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PlaneSpec import PlaneSpec

Block = (
    LineCurve((0.0, 0.0), (40.0, 0.0)),
    LineCurve((40.0, 0.0), (40.0, 30.0)),
    LineCurve((40.0, 30.0), (0.0, 30.0)),
    LineCurve((0.0, 30.0), (0.0, 0.0)),
)
Slot = (
    LineCurve((10.0, 19.0), (14.0, 19.0)),
    ArcCurve((14.0, 22.0), 3.0, -90.0, 180.0),
    LineCurve((14.0, 25.0), (10.0, 25.0)),
    ArcCurve((10.0, 22.0), 3.0, 90.0, 180.0),
)
Specification = DocumentSpec(
    "Pocket plate",
    "height",
    20.0,
    ProfileKind="part",
    BodyName="Body1",
    Features=(
        ExtrudeSpec(Block, 20.0, "new", "one", 0.0, "Base sketch", "Base extrude"),
        ExtrudeSpec(Slot, 8.0, "cut", "one", 0.0, "Slot sketch", "Slot pocket"),
        HoleSpec((8.0, 8.0), 4.0, FeatureName="Corner hole"),
        PatternSpec(2, 2, 12.0, 1, 10.0, "Hole row"),
        FilletSpec((40.0, 30.0), 3.0, "Corner rounds", ((40.0, 0.0),)),
        PlaneSpec(20.0, "yz", "Mid plane"),
        MirrorSpec(1, 5, "Slot mirror"),
    ),
)
Path("PocketPlate.f3d").write_bytes(EmitDocument(Specification))
```

`MakeFusionDoc` accepts the same specification through the public adapter. It adds one `FeatureStep` for each feature. A step owns one driving length parameter when the feature has one.

| Specification  | `FeatureKind` | Adapter driving parameter |
| -------------- | ------------- | ------------------------- |
| `ExtrudeSpec`  | `KExtrusion`  | `AlongDistance`           |
| `HoleSpec`     | `KHole`       | `HoleDiameter`            |
| `PatternSpec`  | `KPattern`    | `uSpaceDistance`          |
| `CircularSpec` | `KPattern`    | None                      |
| `MirrorSpec`   | `KMirror`     | None                      |
| `PlaneSpec`    | `KReference`  | `AlongDistance`           |
| `AxisSpec`     | `KReference`  | None                      |
| `PointSpec`    | `KReference`  | None                      |
| `FilletSpec`   | `KFillet`     | `Radius`                  |
| `ChamferSpec`  | `KChamfer`    | `Distance`, or `Distance 1` with a second distance |
| `ShellSpec`    | `KShell`      | `innerThickness`          |
| `RevolveSpec`  | `KRevolution` | None                      |
| `MoveSpec`     | `KNative`     | None                      |
| `OffsetSpec`   | `KOffset`     | `distance`                |
| `DraftSpec`    | `KDraft`      | None                      |
| `CombineSpec`  | `KBoolean`    | None                      |
| `SplitSpec`    | `KNative`     | None                      |
| `BodyGridSpec` | `KPattern`    | `uSpaceDistance`          |
| `BodyRingSpec` | `KPattern`    | None                      |
| `LoftSpec`     | `KLoft`       | `AlongDistance` of the loft plane |
| `SweepSpec`    | `KSweep`      | None                      |
| `PasteSpec`    | `KNative`     | None                      |

## Feature inputs

| Specification  | Fields                                                                                    | Fusion feature          |
| -------------- | ----------------------------------------------------------------------------------------- | ----------------------- |
| `ExtrudeSpec`  | `Profile`, `DistanceMm`, `Operation`, `Extent`, `AgainstMm`, `SketchName`, `FeatureName` | `DcExtrudeFeature`      |
| `HoleSpec`     | `CenterMm`, `DiameterMm`, `DepthMm`, `BoreDiameterMm`, `BoreDepthMm`, `FeatureName`, `SinkDiameterMm`, `SinkAngleDegrees` | `DcHoleFeature` |
| `RevolveSpec`  | `InnerMm`, `OuterMm`, `LowerMm`, `UpperMm`, `AngleDegrees`, `Operation`, `SketchName`, `FeatureName` | `DcRevolveFeature` |
| `PatternSpec`  | `SourceIndex`, `CountU`, `SpacingUMm`, `CountV`, `SpacingVMm`, `FeatureName`              | `DcRectangularPattern`  |
| `CircularSpec` | `SourceIndex`, `Count`, `TotalDegrees`, `FeatureName`                                     | `DcCircularPattern`     |
| `PlaneSpec`    | `OffsetMm`, `BasePlane`, `FeatureName`                                                    | `DcWorkPlane`           |
| `AxisSpec`     | `CornerMm`, `FeatureName`                                                                 | `DcWorkAxis`            |
| `PointSpec`    | `CornerMm`, `FeatureName`                                                                 | `DcWorkPoint`           |
| `MirrorSpec`   | `SourceIndex`, `PlaneIndex`, `FeatureName`                                                | `DcMirrorPattern`       |
| `FilletSpec`   | `CornerMm`, `RadiusMm`, `FeatureName`, `MoreCornersMm`, `LevelMm`                         | `DcFilletEdgeFeature`   |
| `ChamferSpec`  | `CornerMm`, `DistanceMm`, `FeatureName`, `SecondMm`, `AngleDegrees`, `MoreCornersMm`, `LevelMm` | `DcChamferFeature` |
| `ShellSpec`    | `ThicknessMm`, `FeatureName`, `SidesMm`                                                   | `DcShellFeature`        |
| `MoveSpec`     | `OffsetMm`, `FeatureName`, `TurnDegrees`                                                  | `DcMoveFeature`         |
| `OffsetSpec`   | `DistanceMm`, `FeatureName`, `SideMm`                                                     | `DcOffsetFacesFeature`  |
| `DraftSpec`    | `AngleDegrees`, `FeatureName`                                                             | `DcDraftFeature`        |
| `CombineSpec`  | `TargetBody`, `ToolBodies`, `Operation`, `KeepTools`, `FeatureName`                       | `DcCombineFeature`      |
| `SplitSpec`    | `PlaneIndex`, `TargetBody`, `FeatureName`                                                 | `DcSplitBodyFeature`    |
| `BodyGridSpec` | `SourceBody`, `CountU`, `SpacingUMm`, `CountV`, `SpacingVMm`, `FeatureName`               | `DcRectangularPattern`  |
| `BodyRingSpec` | `SourceBody`, `Count`, `TotalDegrees`, `FeatureName`                                      | `DcCircularPattern`     |
| `LoftSpec`     | `LowerProfile`, `UpperProfile`, `HeightMm`, `LowerName`, `PlaneName`, `UpperName`, `FeatureName` | `DcLoftFeature` |
| `SweepSpec`    | `Path`, `LeftMm`, `RightMm`, `LowerMm`, `UpperMm`, `ProfileName`, `PathName`, `FeatureName` | `DcSweepFeature` |
| `PasteSpec`    | `SourceBody`, `FeatureName`                                                               | `DcPasteBodies` and `DcBaseFeature` |

All coordinates are millimetres on the XY sketch plane. Every sketch lies on the origin XY plane, except the revolve and sweep profiles on the XZ plane and the top sketch of a loft. Every extrusion runs along Z.

| `ExtrudeSpec` field | Values                                                                                                     |
| ------------------- | ---------------------------------------------------------------------------------------------------------- |
| `Profile`           | One closed loop of `LineCurve` and `ArcCurve` values, or one `CircleCurve`, with at most 64 curves          |
| `Operation`         | `new` for the first feature or another body, `join`, `cut` or `intersect` while one body is visible       |
| `Extent`            | `one` along +Z, `flip` along −Z, `symmetric` about the sketch plane, `two` with `AgainstMm` along −Z        |

An `ArcCurve` takes a centre, a radius, a start angle and a signed sweep in degrees. The sweep must be shorter than a full turn. A hole is drilled downward from the current top face at `CenterMm`. `DepthMm` of 0 cuts through all, and a blind hole has a flat 180° tip. A positive `BoreDiameterMm` and `BoreDepthMm` add a counterbore. A positive `SinkDiameterMm` adds a countersink cone instead. `SinkAngleDegrees` sets its included angle and defaults to 90. A countersunk hole must be the last solid feature.

`RevolveSpec` sketches a rectangle on the XZ plane and turns it about the Z axis. The rectangle spans `InnerMm` to `OuterMm` from the axis and `LowerMm` to `UpperMm` along Z. `AngleDegrees` of 360 gives a full ring, and a smaller angle gives a sector. `Operation` is `new`, `join` or `cut`.

`MoveSpec` moves the whole body as a free move. It first turns the body by `TurnDegrees` about the Z axis through the origin. It then translates the body by the `(x, y, z)` offset `OffsetMm`. The move matrix is the only input, so the feature has no driving parameter. Later features see the moved body. A hole cannot follow a move, because in both observed runs a recompute placed such a hole away from its authored centre.

`OffsetSpec` moves one planar face along its outward normal by `DistanceMm`. A negative distance moves the face inward. Without `SideMm` the feature moves the top face. Otherwise the `(x, y)` point `SideMm` names one straight side face, and both of its neighbours must be straight. The body must be one prism slab without circular walls or a countersink.

`DraftSpec` tilts every side face of a one-slab prism about its bottom edge, with the bottom face as the fixed plane. A positive `AngleDegrees` leans the faces out, so the top face grows. A negative angle leans them in. Every side must be straight, and the draft must be the last solid feature.

`PatternSpec` and `CircularSpec` copy an earlier cut extrusion or hole, named by its index in `Features`. A rectangular pattern steps along X and Y. A circular pattern turns about the Z axis through `TotalDegrees`, with 360 giving an even full ring. `PlaneSpec` offsets an origin plane along its normal. `AxisSpec` places an axis on the vertical body edge at `CornerMm`, from the floor to the roof. `PointSpec` places a point on the bottom vertex of that edge. The edge must run through every slab of the body with the same two walls. `MirrorSpec` reflects an earlier cut extrusion or hole about an earlier `PlaneSpec` parallel to YZ.

Bodies are numbered from 1 in the order they are made. A combine, split or body pattern names a visible body by its number. `CombineSpec` merges each body in `ToolBodies` into `TargetBody` with the `join`, `cut` or `intersect` operation. The tools disappear unless `KeepTools` is true, and each tool must be one straight slab. `SplitSpec` cuts `TargetBody` along the earlier `PlaneSpec` at index `PlaneIndex`, and the plane must cross the body. The piece on the lower side of the plane keeps the body number, and the other piece takes the next number. `BodyGridSpec` and `BodyRingSpec` copy `SourceBody` like `PatternSpec` and `CircularSpec`, and the copies take the next numbers. A part holds at most 16 bodies. A `new` extrusion or revolve can follow any number of bodies, but every other feature needs exactly one visible body. Combines and splits reject drafted bodies, and only the part profile can add bodies.

`LoftSpec` sketches `LowerProfile` on the XY plane and adds a construction plane `HeightMm` above it. It sketches `UpperProfile` on that plane and lofts between the two profiles as a new body. Both profiles use the `ExtrudeSpec` curve rules, need the same number of curves and list matching curves in the same order. Each pair of lines must be parallel and point the same way, and a pair of circles must share a centre. Therefore, every side face is a plane or a cone. Arcs are rejected. The loft is the first feature or another body. No later feature can change the loft body, and combines reject it.

`SweepSpec` sketches a rectangle on the XZ plane and sweeps it along `Path` as a new body. The rectangle spans `LeftMm` to `RightMm` along X and `LowerMm` to `UpperMm` along Z. `Path` holds lines and arcs on the XY plane. The path starts at the origin, leaves it along +Y and chains end to start. Each joint must be smooth, and two neighbouring curves cannot lie on the same line or circle. The profile must stay clear of every arc centre, and the swept body cannot cross itself. The edge of the profile at +X follows the right-hand side of the path. The feature keeps the native `AlongDistance` parameter, which sets the swept fraction of the path. A sweep is the first feature or another body. No later feature can change the sweep body. Combines, splits and body patterns reject it.

`CornerMm` is an `(x, y)` point on one convex vertical corner between two straight sides of the current body. `MoreCornersMm` adds up to seven more corners to the same feature. `DistanceMm` runs along the side that ends at the corner. A positive `SecondMm` runs along the side that leaves it. A positive `AngleDegrees` sets the angle between the chamfer face and the first side instead. Fillets and chamfers can follow earlier features. With `LevelMm`, each point names the horizontal edge through `(x, y, LevelMm)`, and such edge rounds must follow every other solid feature. A shell opens the top face, keeps the outer walls and must be the final feature. Each `(x, y)` point in `SidesMm` names one straight side face to open as well. The open sides must form one connected run, and the sides next to the run must be straight.

`CheckFeatures` rejects unsupported families, non-finite or non-positive values and more than 16 features. A part must start with a `new` extrusion or revolve, a loft or a sweep. Copies accept at most 64 occurrences. It also rejects invalid names and a user parameter named `d<digits>`. `SolvePart` rejects a feature that misses the body, consumes an adjacent side or collapses the profile.

## Construction

`SolvePart` applies every feature to an exact prism model and keeps each intermediate solid. The model stores a stack of slabs with vertical walls and flat caps. Profile booleans cut and join these slabs exactly. Wall pieces with the same label on one line merge across slabs into one face. An open shell side is therefore one U-shaped face, as in the native control. An offset face keeps its tag and appends the negated first operation of the feature. Each face that shares an edge with it appends the negated second operation, as in the native controls. A drafted slab keeps its bottom profile and stores the leaning top profile. A loft slab stores the top profile in the same way. The loft slab has both caps and every side tagged by the loft operation and no sketch curve links, as in the native control. Its side faces are exact planes, and its rising edges are slanted lines. Edge rounds on horizontal edges are applied last, to the finished body. They add cylinders and planes along lines, tori and cones along arcs, and elliptic mitre edges where two rounds meet at a sharp corner. A sweep is one slab whose outline follows the path. Its walls are planes along the path lines and vertical cylinders along the path arcs. The floor and the roof are each one face that carries the tags of every path segment. Each drafted face appends the negated first operation, and both caps keep their tags, as in the native control. `EmitPartHist` writes one journal state for each solid-changing feature. Each state contains the complete solved body, with exact planes, cylinders, lines and circles. Fusion does not recompute features when it opens a document, so these solved states are required. With several bodies, each state holds every body made so far, including the tools that a combine consumed. Each body claims its tag in the first state that holds it, in body order. The Design marks a consumed body hidden and eliminated. See [the stale-open gotcha](../../../Gotchas/Conversion/Fusion/Features/FeatureStaleOpen.md).

Each feature subgraph contains the feature, its parameters, its references, its geometry caches and its progenitor tables. An extrusion also writes its sketch, curves, region recipe and profile. A pattern or mirror writes the source references, one occurrence for each copy and one operation identifier per copy. `LinkTimeline` adds the features to the creation order, the identifier maps, the per-class index map and the component operation seed.

The feature vocabulary in `PartFeatures/Vocabulary/FeatureDefaults.json` holds only schema-neutral defaults: null, zero, false, the empty string or an empty list. `re/Fusion/Reconstruction/FeatureAuthoring/MakeFeatureVocabulary.py` generates it from the class schemas and copies no value from a native control. Points, vectors, cached curves, transforms, identifier maps, tags, recipes and mode codes have no default. Each writer supplies them from its spec or from a mode code that every native control of its family shares. A sweep takes its profile normal from its profile sketch frame, and a rectangular pattern takes its deduced direction from its V axis. A missing field raises `ValueError` naming the class and the field. The [data model](../../../Reference/Research/FusionDataModel.md#feature-defaults-and-mode-codes) lists each mode code with its native evidence.

| Family              | Operations                   | Journal state |
| ------------------- | ---------------------------- | ------------- |
| Extrusion           | 3                            | One           |
| Hole                | 1                            | One           |
| Rectangular pattern | `CountU` × `CountV`          | One           |
| Circular pattern    | `Count`                      | One           |
| Mirror              | 2                            | One           |
| Construction plane  | 1                            | None          |
| Construction axis   | 1                            | None          |
| Construction point  | 1                            | None          |
| Fillet or chamfer   | 1                            | One           |
| Shell               | 2                            | One           |
| Revolve             | 2                            | One           |
| Move                | 1                            | One           |
| Offset face         | 2                            | One           |
| Draft               | 2                            | One           |
| Combine             | 1                            | One           |
| Split               | 1                            | One           |
| Body pattern        | `CountU` × `CountV` or `Count` | One         |
| Loft                | 4                            | One           |
| Sweep               | 3                            | One           |
| Paste               | 2                            | One           |

Four journal and record rules are necessary for native acceptance:

| Rule                                                                         | Failure without the rule                                     |
| ---------------------------------------------------------------------------- | ------------------------------------------------------------ |
| The body claims tag 0, the `mapBodyId` key                                   | The body opens without geometry                              |
| A face replaced by delete and insert receives a fresh tag                    | Fusion cannot open the document                              |
| `BrepRef.rScope` and `ETCachedTopology.scope` carry the component identifier | `computeAll` loses the shell face and reverts to the box     |
| Every bulletin names the object's identity entity on its new side            | Fusion terminates while it disposes the closed document      |

The [body tag gotcha](../../../Gotchas/Conversion/Fusion/Features/FeatureBodyTag.md) and the [reference rules gotcha](../../../Gotchas/Conversion/Fusion/Features/FeatureReferenceRules.md) record the evidence. The [stateless plane gotcha](../../../Gotchas/Conversion/Fusion/Features/FeatureStatelessPlane.md) and the [copy occurrence gotcha](../../../Gotchas/Conversion/Fusion/Features/FeatureCopyOccurrence.md) record the native rules for planes and copies. The [hole placement gotcha](../../../Gotchas/Conversion/Fusion/Features/FeatureHolePlacement.md) records how a hole keeps its centre through a recompute. The [bulletin identity gotcha](../../../Gotchas/Conversion/Fusion/Features/FeatureBulletinIdentity.md) records the journal rule that keeps Fusion alive after closing an authored document. The [circle seam gotcha](../../../Gotchas/Conversion/Fusion/Features/FeatureCircleSeam.md) records where profile circles start. The copy occurrence gotcha also records why a copy names the base face of its source extrusion. The [revolve frame gotcha](../../../Gotchas/Conversion/Fusion/Features/FeatureRevolveFrame.md) records the native frame of the XZ sketch plane. The [combine tool gotcha](../../../Gotchas/Conversion/Fusion/Features/FeatureCombineTools.md) records how a consumed tool stays in the journal. The [split sides gotcha](../../../Gotchas/Conversion/Fusion/Features/FeatureSplitSides.md) records the native labels of the two pieces of a split. The [loft sections gotcha](../../../Gotchas/Conversion/Fusion/Features/FeatureLoftSections.md) records how a loft pairs its section curves. The [sweep faces gotcha](../../../Gotchas/Conversion/Fusion/Features/FeatureSweepFaces.md) records the native face tags of a sweep. The [chamfer legs gotcha](../../../Gotchas/Conversion/Fusion/Features/FeatureChamferLegs.md) records which face takes the first chamfer distance on a horizontal edge.

## Native acceptance

The [acceptance script](../../../../re/Fusion/LocalOracle/FeatureAuthoring/AcceptAuthoredFeatures.py) builds a native API control in the same session for each case. It then opens the Kit document without a recompute, walks every rollback marker and runs `computeAll`. It applies the driving edits, exports the document, reopens it and runs `computeAll` again. Geometry must match the control in volume, area, faces, edges, vertices, surface types, bounds and centre of mass.

Construction cases also compare the origin and direction of each axis and the position of each point. Each suite ran in Fusion 2706.1.17 with no document open before or after the run. `MultiPocketPart`, `MultiDiscPart`, `CornerSetPart` and `ConstructionPart` combine several families in one part.

| Suite        | Report                              | Accepted cases |
| ------------ | ----------------------------------- | -------------- |
| Corners      | `NativeAcceptance.json`             | 5 of 5         |
| Extrusions   | `NativeAcceptanceExtrudes.json`     | 15 of 15       |
| Holes        | `NativeAcceptanceHoles.json`        | 4 of 4         |
| Patterns     | `NativeAcceptancePatterns.json`     | 5 of 5         |
| Multi        | `NativeAcceptanceMulti.json`        | 2 of 2         |
| Edges        | `NativeAcceptanceEdges.json`        | 5 of 5         |
| Construction | `NativeAcceptanceConstruction.json` | 2 of 2         |
| Revolves     | `NativeAcceptanceRevolves.json`     | 4 of 4         |
| Countersinks | `NativeAcceptanceCountersinks.json` | 2 of 2         |
| Shells       | `NativeAcceptanceShells.json`       | 2 of 2         |
| Moves        | `NativeAcceptanceMoves.json`        | 2 of 2         |
| Offsets      | `NativeAcceptanceOffsets.json`      | 4 of 4         |
| Drafts       | `NativeAcceptanceDrafts.json`       | 3 of 3         |
| Bodies       | `NativeAcceptanceBodies.json`       | 11 of 11       |
| Lofts        | `NativeAcceptanceLofts.json`        | 3 of 3         |
| Sweeps       | `NativeAcceptanceSweeps.json`       | 4 of 4         |
| Pastes       | `NativeAcceptancePastes.json`       | 6 of 6         |
| Rounds       | `NativeAcceptanceRounds.json`       | 30 of 30       |

Volumes are those of the opened Kit document after `computeAll`. The edited volume follows the listed parameter edits.

### Corners

| Case | Features | Volume (cm³) | Faces, edges, vertices | Edits | Edited volume (cm³) |
| --- | --- | ---: | --- | --- | ---: |
| `Fillet` | fillet 3 mm | 23.96137167 | 7, 15, 10 | Fillet size 4 mm | 23.93132741 |
| `Chamfer` | chamfer 3 mm | 23.91000000 | 7, 15, 10 | Chamfer size 2 mm | 23.96000000 |
| `Shell` | shell 2 mm | 7.15200000 | 11, 24, 16 | Shell size 3 mm | 10.12800000 |
| `FilletShell` | fillet 3 mm, shell 2 mm | 7.11723450 | 13, 30, 20 | Shell size 1.5 mm, height size 25 mm | 6.48656166 |
| `MultiFeature` | fillet 3 mm, chamfer 3 mm, fillet 4 mm, shell 2 mm | 7.00410156 | 17, 42, 28 | Corner Round size 5 mm, height size 25 mm | 8.24214524 |

### Extrusions

| Case | Features | Volume (cm³) | Faces, edges, vertices | Edits | Edited volume (cm³) |
| --- | --- | ---: | --- | --- | ---: |
| `ExtrudeNew` | rectangle new 20 mm | 24.00000000 | 6, 12, 8 | Base extrude AlongDistance 25 mm | 30.00000000 |
| `ExtrudeSymmetric` | rectangle new symmetric 20 mm | 24.00000000 | 6, 12, 8 | Base extrude AlongDistance 16 mm | 19.20000000 |
| `ExtrudeTwoSided` | rectangle new two-sided 20 mm | 30.00000000 | 6, 12, 8 | Base extrude AgainstDistance 8 mm | 33.60000000 |
| `ExtrudeFlip` | rectangle new flipped 20 mm | 24.00000000 | 6, 12, 8 | Base extrude AlongDistance -12 mm | 14.40000000 |
| `ProfileSlot` | slot new 20 mm | 14.28318531 | 6, 12, 8 | Slot extrude AlongDistance 15 mm | 10.71238898 |
| `ProfileConcave` | arc profile new 20 mm | 20.85840735 | 8, 18, 12 | Notch extrude AlongDistance 15 mm | 15.64380551 |
| `ProfileCircle` | circle new 20 mm | 6.28318531 | 3, 2, 2 | Disc extrude AlongDistance 15 mm | 4.71238898 |
| `ExtrudeJoin` | rectangle new 20 mm, circle join 30 mm | 24.78539816 | 8, 14, 10 | Boss AlongDistance 35 mm | 25.17809725 |
| `ExtrudeCut` | rectangle new 20 mm, circle cut 20 mm | 22.42920367 | 7, 14, 10 | Base extrude AlongDistance 25 mm | 28.42920367 |
| `ExtrudeIntersect` | rectangle new 20 mm, circle intersect 20 mm | 6.28318531 | 3, 2, 2 | Core AlongDistance 15 mm | 4.71238898 |
| `ExtrudeBlindCut` | rectangle new 20 mm, circle cut 10 mm | 23.21460184 | 8, 14, 10 | Pocket AlongDistance 6 mm | 23.52876110 |
| `ExtrudeSlotCut` | rectangle new 20 mm, slot cut 20 mm | 20.42920367 | 10, 24, 16 | Base extrude AlongDistance 25 mm | 26.42920367 |
| `ExtrudeSymmetricCut` | rectangle new 20 mm, circle cut symmetric 20 mm | 23.21460184 | 8, 14, 10 | Pocket AlongDistance 12 mm | 23.52876110 |
| `PartCutFillet` | rectangle new 20 mm, slot cut 20 mm, fillet 3 mm, chamfer 2 mm | 20.35057534 | 12, 30, 20 | Corner Round size 4 mm, Base extrude AlongDistance 25 mm | 26.29336294 |
| `PartConcaveShell` | arc profile new 20 mm, fillet 4 mm, shell 2 mm | 7.16870700 | 17, 42, 28 | Hollow size 1.5 mm, Notch extrude AlongDistance 25 mm | 6.61558154 |

### Holes

| Case | Features | Volume (cm³) | Faces, edges, vertices | Edits | Edited volume (cm³) |
| --- | --- | ---: | --- | --- | ---: |
| `HoleFlat` | rectangle new 20 mm, hole 8 mm blind 10 mm | 23.49734518 | 8, 14, 10 | Top hole HoleDiameter 6 mm, Top hole HoleDepth 12 mm | 23.66070799 |
| `HoleThrough` | rectangle new 20 mm, hole 8 mm through | 22.99469035 | 7, 14, 10 | Top hole HoleDiameter 10 mm, Base extrude AlongDistance 25 mm | 28.03650459 |
| `HoleCounterboreFlat` | rectangle new 20 mm, hole 6 mm blind 10 mm counterbore | 23.51619473 | 10, 16, 12 | Top hole CBDiameter 12 mm, Top hole CBDepth 3 mm | 23.46278766 |
| `HoleCounterbore` | rectangle new 20 mm, hole 6 mm through counterbore | 23.23345139 | 9, 16, 12 | Top hole HoleDiameter 5 mm, Base extrude AlongDistance 25 mm | 29.27350670 |

### Patterns

| Case | Features | Volume (cm³) | Faces, edges, vertices | Edits | Edited volume (cm³) |
| --- | --- | ---: | --- | --- | ---: |
| `PlaneOffset` | rectangle new 20 mm, XY plane 15 mm | 24.00000000 | 6, 12, 8 | Offset plane AlongDistance 12 mm, Base extrude AlongDistance 25 mm | 30.00000000 |
| `RectPattern` | rectangle new 20 mm, circle cut 20 mm, pattern 3 × 2 | 20.60707993 | 12, 24, 20 | Pocket grid uSpaceDistance 11 mm, Pocket grid CountV 1 | 22.30353997 |
| `FeatureCircPattern` | rectangle new 20 mm, circle cut 20 mm, circular 2 over 40 deg | 23.03560990 | 9, 20, 14 | Pocket arc TotalAngle 30 deg | 22.87278292 |
| `MirrorFeature` | rectangle new 20 mm, circle cut 20 mm, YZ plane 20 mm, mirror | 22.86902664 | 8, 16, 12 | Mid plane AlongDistance 18 mm | 22.86902664 |
| `HoleGrid` | rectangle new 20 mm, hole 5 mm blind 10 mm, pattern 3 × 2 | 22.82190275 | 18, 24, 20 | Hole grid vSpaceDistance 12 mm, Corner hole HoleDepth 8 mm | 23.05752220 |

### Multi-family parts

| Case | Features | Volume (cm³) | Faces, edges, vertices | Edits | Edited volume (cm³) |
| --- | --- | ---: | --- | --- | ---: |
| `MultiPocketPart` | rectangle new 20 mm, slot cut 8 mm, hole 4 mm through, pattern 2 × 1, fillet 3 mm, YZ plane 20 mm, mirror | 22.62232750 | 19, 43, 30 | Hole row uSpaceDistance 10 mm, Corner Round size 4 mm, Mid plane AlongDistance 21 mm | 22.59228325 |
| `MultiDiscPart` | circle new 12 mm, circle cut 6 mm, circular 4 over 360 deg, hole 8 mm through counterbore | 13.38318470 | 14, 14, 14 | Pocket ring countU 6, Center bore CBDiameter 16 mm | 12.85539714 |

### Edge sets

| Case | Features | Volume (cm³) | Faces, edges, vertices | Edits | Edited volume (cm³) |
| --- | --- | ---: | --- | --- | ---: |
| `ChamferTwoDistances` | rectangle new 20 mm, chamfer 3 mm and 2 mm | 23.94000000 | 7, 15, 10 | Corner bevel Distance 2 1 mm | 23.97000000 |
| `ChamferDistanceAngle` | rectangle new 20 mm, chamfer 3 mm at 30 deg | 23.94803848 | 7, 15, 10 | Corner bevel Rotate Angle 40 deg | 23.92448103 |
| `FilletTwoEdges` | rectangle new 20 mm, fillet 3 mm on 2 edges | 23.92274334 | 8, 18, 12 | Corner rounds size 4 mm | 23.86265482 |
| `ChamferTwoEdges` | rectangle new 20 mm, chamfer 3 mm on 2 edges | 23.82000000 | 8, 18, 12 | Corner bevels size 2 mm | 23.92000000 |
| `CornerSetPart` | rectangle new 20 mm, hole 6 mm through, fillet 4 mm on 2 edges, chamfer 3 mm at 30 deg | 23.24520662 | 10, 23, 16 | Corner rounds size 5 mm, Corner bevel Rotate Angle 45 deg, Side hole HoleDiameter 8 mm | 22.69008851 |

### Construction geometry

| Case | Features | Volume (cm³) | Faces, edges, vertices | Edits | Edited volume (cm³) |
| --- | --- | ---: | --- | --- | ---: |
| `ConstructionSet` | rectangle new 20 mm, XY plane 15 mm, axis at (40, 30) mm, point at (40, 30) mm | 24.00000000 | 6, 12, 8 | Offset plane AlongDistance 12 mm, Base extrude AlongDistance 25 mm | 30.00000000 |
| `ConstructionPart` | rectangle new 20 mm, circle cut 20 mm, axis at (0, 0) mm, point at (40, 0) mm, fillet 3 mm | 23.39588499 | 8, 17, 12 | Base extrude AlongDistance 26 mm, Corner round size 4 mm | 30.54523896 |

### Revolves

| Case | Features | Volume (cm³) | Faces, edges, vertices | Edits | Edited volume (cm³) |
| --- | --- | ---: | --- | --- | ---: |
| `RevolveFull` | rectangle 10 to 20 mm by 0 to 30 mm, revolve 360 deg | 28.27433388 | 4, 4, 4 | Tube revolve AlongAngle 270 deg | 21.20575041 |
| `RevolveHalf` | rectangle 10 to 20 mm by 0 to 30 mm, revolve 180 deg | 14.13716694 | 6, 12, 8 | Tube revolve AlongAngle 120 deg | 9.42477796 |
| `RevolveJoin` | circle new 10 mm, rectangle 10 to 15 mm by 10 to 20 mm, join 360 deg | 23.56194490 | 7, 6, 6 | Ring revolve AlongAngle 180 deg, Disc extrude AlongDistance 12 mm | 25.13274123 |
| `RevolveCut` | circle new 10 mm, rectangle 15 to 22 mm by 6 to 10 mm, cut 90 deg | 18.82128159 | 8, 14, 10 | Groove revolve AlongAngle 120 deg | 18.55005742 |

### Countersinks

| Case | Features | Volume (cm³) | Faces, edges, vertices | Edits | Edited volume (cm³) |
| --- | --- | ---: | --- | --- | ---: |
| `HoleCountersink` | rectangle new 20 mm, hole 6 mm through, countersink 10 mm at 90 deg | 23.38843663 | 8, 15, 11 | Top hole CSDiameter 12 mm, Base extrude AlongDistance 25 mm | 29.18004432 |
| `HoleCountersinkFlat` | rectangle new 20 mm, hole 6 mm blind 10 mm, countersink 12 mm at 82 deg | 23.58715306 | 9, 15, 11 | Top hole CSAngle 100 deg, Top hole HoleDepth 14 mm | 23.50925939 |

### Open shells

| Case | Features | Volume (cm³) | Faces, edges, vertices | Edits | Edited volume (cm³) |
| --- | --- | ---: | --- | --- | ---: |
| `ShellOpenSide` | shell 2 mm, top and front faces open | 5.85600000 | 10, 24, 16 | Open shell size 3 mm, height size 25 mm | 9.80400000 |
| `ShellOpenCorner` | shell 2 mm, top, front and right faces open | 4.84800000 | 9, 21, 14 | Open corner size 4 mm, height size 15 mm | 7.70400000 |

### Moves

| Case | Features | Volume (cm³) | Faces, edges, vertices | Edits | Edited volume (cm³) |
| --- | --- | ---: | --- | --- | ---: |
| `MoveBody` | cuboid moved 10 mm along X | 24.00000000 | 6, 12, 8 | height size 25 mm | 30.00000000 |
| `MoveTurnPart` | part turned 30° about Z and moved (5, 5, 2) mm, then a 3 mm fillet | 23.96137167 | 7, 15, 10 | Base extrude AlongDistance 25 mm, Turned round size 4 mm | 29.91415927 |

### Offset faces

| Case | Features | Volume (cm³) | Faces, edges, vertices | Edits | Edited volume (cm³) |
| --- | --- | ---: | --- | --- | ---: |
| `OffsetTop` | top face raised 5 mm | 30.00000000 | 6, 12, 8 | Top offset distance 8 mm, Base extrude AlongDistance 25 mm | 39.60000000 |
| `OffsetTopTrim` | top face lowered 5 mm | 18.00000000 | 6, 12, 8 | Top trim distance -8 mm | 14.40000000 |
| `OffsetSide` | right face pushed out 4 mm | 26.40000000 | 6, 12, 8 | Side offset distance 6 mm, Base extrude AlongDistance 25 mm | 34.50000000 |
| `OffsetRoundFront` | 3 mm fillet, then front face pushed out 4 mm | 27.16137167 | 7, 15, 10 | Front offset distance -5 mm, Corner round size 4 mm | 19.93132741 |

### Drafts

| Case | Features | Volume (cm³) | Faces, edges, vertices | Edits | Edited volume (cm³) |
| --- | --- | ---: | --- | --- | ---: |
| `DraftSides` | four sides drafted 5° out | 26.53132809 | 6, 12, 8 | Side draft Angle1 8 deg, Base extrude AlongDistance 25 mm | 36.56015581 |
| `DraftInward` | four sides drafted 5° in | 21.63196293 | 6, 12, 8 | Side taper Angle1 -3 deg | 22.56187898 |
| `DraftCutPart` | 3 mm chamfer, then five sides drafted 5° out | 26.40707624 | 7, 15, 10 | Side draft Angle1 3 deg, Corner cut size 4 mm | 25.31089818 |

### Bodies

Each volume lists the visible bodies in the order Fusion returns them. Every case was compared body by body with its native control.

| Case | Features | Volume (cm³) | Faces, edges, vertices | Edits | Edited volume (cm³) |
| --- | --- | ---: | --- | --- | ---: |
| `ExtrudeSecondBody` | block, then a 5 mm circle extruded 20 mm as a new body | 24.00000000 + 1.57079633 | 6, 12, 8; 3, 2, 2 | Post extrude AlongDistance 15 mm | 24.00000000 + 1.17809725 |
| `RevolveBody` | block, then a 60 to 80 mm by 0 to 10 mm ring revolved as a new body | 24.00000000 + 87.96459430 | 6, 12, 8; 4, 4, 4 | Ring revolve AlongAngle 180 deg | 24.00000000 + 43.98229715 |
| `CombineJoin` | block and a 10 mm post, joined | 28.71238898 | 7, 15, 10 | Post extrude AlongDistance 30 mm | 31.85398163 |
| `CombineCut` | block and a 10 mm post, post cut from the block | 22.42920367 | 7, 15, 10 | Post extrude AlongDistance 15 mm | 22.82190275 |
| `CombineIntersect` | block and a 10 mm post, intersected | 1.57079633 | 5, 9, 6 | Base extrude AlongDistance 15 mm | 1.17809725 |
| `CombineKeep` | block and a 10 mm post, joined with the tool kept | 28.71238898 + 6.28318531 | 7, 15, 10; 3, 2, 2 | Post extrude AlongDistance 30 mm | 31.85398163 + 9.42477796 |
| `SplitYZ` | block split by a YZ plane at 20 mm | 12.00000000 + 12.00000000 | 6, 12, 8 each | Split plane AlongDistance 25 mm | 15.00000000 + 9.00000000 |
| `SplitXZ` | block split by an XZ plane at 10 mm | 8.00000000 + 16.00000000 | 6, 12, 8 each | Split plane AlongDistance 20 mm | 16.00000000 + 8.00000000 |
| `SplitXY` | block split by an XY plane at 8 mm | 9.60000000 + 14.40000000 | 6, 12, 8 each | Split plane AlongDistance 12 mm | 14.40000000 + 9.60000000 |
| `BodyRectPattern` | 10 mm cube, body pattern 3 × 2 at 15 and 20 mm | 6 × 1.00000000 | 6, 12, 8 each | Cube grid uSpaceDistance 18 mm, Cube grid CountV 3 | 9 × 1.00000000 |
| `BodyCircPattern` | 10 mm cube, body pattern 4 over 360 deg | 4 × 1.00000000 | 6, 12, 8 each | Cube ring countU 6 | 6 × 1.00000000 |

### Lofts

The two rectangle and circle cases match the native loft controls. The edit moves the loft plane, so the top profile rises or falls.

| Case | Features | Volume (cm³) | Faces, edges, vertices | Edits | Edited volume (cm³) |
| --- | --- | ---: | --- | --- | ---: |
| `LoftRects` | 40 × 30 mm rectangle lofted to a 20 × 10 mm rectangle 30 mm higher | 19.00000000 | 6, 12, 8 | Loft plane AlongDistance 40 mm | 25.33333333 |
| `LoftCircles` | 10 mm circle lofted to a coaxial 5 mm circle 30 mm higher | 5.49778714 | 3, 2, 2 | Loft plane AlongDistance 20 mm | 3.66519143 |
| `LoftWedgeBody` | block, then a 40 × 30 mm rectangle lofted to an off-centre 20 × 5 mm rectangle 25 mm higher as a new body | 24.00000000 + 14.16666667 | 6, 12, 8 each | Wedge plane AlongDistance 30 mm | 24.00000000 + 17.00000000 |

### Sweeps

`SweepBend` and `SweepHook` match the native sweep controls. Each edit shortens the sweep to a fraction of its path.

| Case | Features | Volume (cm³) | Faces, edges, vertices | Edits | Edited volume (cm³) |
| --- | --- | ---: | --- | --- | ---: |
| `SweepBend` | 10 × 10 mm rectangle swept along a 20 mm line and a quarter arc of 30 mm radius | 6.71238898 | 8, 18, 12 | Bend sweep AlongDistance 0.5 | 3.35619449 |
| `SweepHook` | the same rectangle along a line, a quarter arc and a second 20 mm line | 8.71238898 | 10, 24, 16 | Bend sweep AlongDistance 0.75 | 6.53429174 |
| `SweepSCurve` | 8 × 6 mm rectangle off the path centre, swept along a line and two quarter arcs of 20 mm radius that turn opposite ways | 3.49592895 | 10, 24, 16 | Bar sweep AlongDistance 0.5 | 1.68456625 |
| `SweepSecondBody` | block, then a rectangle 5 to 15 mm left of the bend path swept as a new body | 24.00000000 + 5.14159265 | 6, 12, 8; 8, 18, 12 | Rail sweep AlongDistance 0.5, Base extrude AlongDistance 25 mm | 30.00000000 + 2.90412966 |

### Pastes

[Body copy and paste](FusionBodyPaste.md) lists the six paste cases, their volumes and their edits.

### Rounds

[Edge rounds](FusionEdgeRounds.md) lists the 30 edge round cases, their volumes and their edits.

The [manifest](../../../../re/Fusion/LocalOracle/FeatureAuthoring/Authored/Manifest.json) records the SHA-256 of each authored document. Each acceptance report repeats that digest and records the digest of the Fusion-saved export.

## Verification

The integration cases live in `tests/convert/formats/FusionCodec/Documents/PartFeatures`. They run remotely, and no local tests were executed.

| File                    | Checks                                                                   |
| ----------------------- | ------------------------------------------------------------------------ |
| `PartArchiveTests.py`   | Timeline order, cached mass, journal states and exact re-emission        |
| `PartSolidTests.py`     | Solved stages, volumes and topology counts                               |
| `PartRejectTests.py`    | Rejected inputs raise `ValueError`                                       |
| `PartAdapterTests.py`   | The public adapter and its feature steps                                 |
| `PartJournalTests.py`   | Journal tag chains, reference scopes and bulletin identities             |
| `PartEvidenceTests.py`  | Corner documents against the manifest and their acceptance report        |
| `FamilyTests.py`        | Family solids, native control geometry, records, plane states and rejects |
| `SuiteEvidenceTests.py` | Every acceptance report, its digests and its bulletin identities         |
| `WorkGeomTests.py`      | Axis and point states and records against the native control             |
| `CopyFaceTests.py`      | Copy face tags, source tracks and the adjacent face cache of a pattern    |
| `BodyTests.py`          | Multi-body solids against native controls, body records, states and rejects |
| `LoftTests.py`          | Loft solids against native controls, records, sketch frames, states and rejects |
| `SweepTests.py`         | Sweep solids against native controls and path lengths, face tags, records, states and rejects |
| `PasteTests.py`         | Paste solids against native controls, copy face labels, records, class scope and rejects |
| `RoundTests.py`         | Edge round solids against native controls, records, tori, chamfer leg sides, loop volumes and rejects |
| `VocabTests.py`         | Neutral feature defaults, required geometry and identifier fields, and the error for a missing field |

`PartCases.py`, `FamilyCases.py`, `PartRecords.py`, `NativeControl.py` and `BulletinRefs.py` are shared helpers. Local Black, Ruff, Mypy, Pyright, steering, rationale-comment and path-policy checks passed.

## Limits

The writer authors bodies from sketch extrusions on the origin XY plane along Z and from revolves about Z. The writer also authors bodies from lofts between profiles parallel to XY and from sweeps along paths in the XY plane. Every authored surface is a plane, a vertical cylinder or a cone about a vertical axis, except the faces of edge rounds. Those are horizontal cylinders, tori about vertical axes, cones and planes.

| Request                                                                    | Status                                       |
| -------------------------------------------------------------------------- | -------------------------------------------- |
| Sweep profiles other than a rectangle on the XZ plane                      | Not authored                                 |
| Sweep paths off the XY plane, with splines, twist, taper or guide rails    | Not authored                                 |
| Sweep paths that miss the origin, leave it off +Y or kink, and sweeps that cross themselves or reach an arc centre | Rejected with `ValueError` |
| Features that change a sweep body, and combines, splits or body patterns of it | Rejected with `ValueError`               |
| Lofts with arcs, twisted or off-axis pairs, or curve counts that differ    | Rejected with `ValueError`                   |
| Lofts with rails, more than two sections or sections off the XY direction  | Not authored                                 |
| Features that change a loft body, and combines with a loft body            | Rejected with `ValueError`                   |
| Drafts of some sides, curved sides or about another fixed plane            | Not authored                                 |
| Drilled tips                                                               | Not authored                                 |
| Pastes of several bodies at once, cut and paste, and pastes into another component | Not authored; [body copy and paste](FusionBodyPaste.md) lists the paste limits |
| Splits along a face, a body or a plane that is not an offset origin plane  | Not authored                                 |
| Combine tools with several slabs, and combines or splits of drafted bodies | Rejected with `ValueError`                   |
| Mirrors of bodies                                                          | Not authored                                 |
| Other features while several bodies are visible                            | Rejected with `ValueError`                   |
| Moves that turn about an axis other than Z                                 | Not authored                                 |
| Holes after a move                                                         | Not authored                                 |
| Offset faces on curved faces or on several faces at once                   | Not authored                                 |
| Offset faces on bodies with several slabs, circles or countersinks         | Rejected with `ValueError`                   |
| Axes and points that are not on a vertical body edge                       | Not authored                                 |
| Edge rounds with ends that are not square, concave sharp corners or variable radius | Rejected or not authored; [edge rounds](FusionEdgeRounds.md) lists the limits |
| Shells that open curved sides or separate runs of sides                    | Rejected with `ValueError`                   |
| Feature patterns and mirrors of joins or fillets                           | Rejected with `ValueError`                   |
| Mirrors about planes that are not parallel to YZ                           | Rejected with `ValueError`                   |

[Native records for the missing families](../../../../re/Fusion/Reconstruction/FeatureAuthoring/FamilyRecords.json.xz) are captured as research evidence only. A corner edit next to a curved side raises `ValueError`.
