# Typed Fusion Form documents

Kit reads and writes complete Fusion Form documents through `ReadDocument` and `EmitParsed` in `convert.formats.Fusion.DocumentCodec`. A Form document joins a T-spline control cage, a Form feature graph and a converted BRep body. Earlier Kit readers rejected these documents.

Kit also converts cages exactly. Open grid cages use a closed-form rule, also with one whole-number knot interval on every edge. Every other closed or creased cage converts by general rules computed from its topology, also with weighted grips and one whole-number knot interval. Kit ships no per-layout table. Kit puts a new cage into a Form document of the same layout, or writes a new Form document from the cage alone. It refuses a cage that the rules cannot convert exactly.

## Model

`DocumentModel.Forms` contains one `DocumentForm(Name, Surface)` for each `TSplines.BlobParts/TSpline.<uuid>.tsm` member. `Surface` is the typed `TsplineSurface` from `ReadTspline`. The writer derives the member text with `EmitTspline`. The Design records stay in the typed entity model. `FormClasses.json` adds the Form vocabulary to the document schema catalog.

The converted body uses three new journal entity types in `convert.formats.Fusion.BrepCodec.Journal.Spline`.

| Entity           | Type           | Main fields                                                                                              |
| ---------------- | -------------- | -------------------------------------------------------------------------------------------------------- |
| `spline-surface` | `SplineNode`   | `Surface` as `TsplineSurf`, `SubtypeRef` or a general `SubtypeNode`, four bounds                         |
| `intcurve-curve` | `IntcurveNode` | `Curve` as an `exact_int_cur` `SubtypeNode` or a `SubtypeRef`                                            |
| `pcurve`         | `PcurveNode`   | `Curve` as an `exp_par_cur` `SubtypeNode` whose `spline` support holds a `TsplineSurf` or a `SubtypeRef` |

`TsplineSurf` holds the revision, the `NubsSurface` geometry, the fit tolerance, six jump arrays, four optional ranges, a type code and a face index. Its `Subtrans` field is a `SubtransNode` or a `SubtypeRef`. A `SubtransNode` holds the embedded `TsplineSurface` and the patch program as `PatchCell` rows. `CoedgeNode.Pcurve` now keeps the coedge reference to its `pcurve`.

The complex geometry change merged these entities with the general subtype grammar. The [complex geometry change entry](../Geometry/FusionComplexGeometry.md) describes that model.

`ListPrograms(Entities)` returns the embedded T-spline programs of a body. `ListTsplines(Entities)` returns each `TsplineSurf` in stream order. `ListSubtypes` and `CheckSubtypes` expose and check the subtype table. `ReadAsmToken` reads tag 8 text, and `EmitWireField` writes tags 8, 13 and 21. `NamedMetadata.ElementName` keeps the element metatype of `Vector` named metadata.

## Joins

`CheckDocForms` runs during `ReadDocument` and before `EmitParsed` writes a document. It raises `ValueError` when one of these joins fails.

| Join                   | Rule                                                                                            |
| ---------------------- | ----------------------------------------------------------------------------------------------- |
| Serializer and member  | Each `TSplineSerializer.partName` names one TSM member, and each member has one serializer      |
| Serializer and surface | `TsSurface.rSerializer` names the serializer that names the surface                             |
| Control frame          | Facet, edge, vertex and grip `tsID` values equal `range(n)` for the TSM table counts            |
| Surface node           | `TsSurface.rVSurface` names the `SubDSurfaceNode`, and the node names the surface               |
| Converted body         | `BASEFEAT_PM_BODIES_REF` names each `Body`, and each `FORMFEAT_DM_SUBD_REF` names the node back |
| Embedded program       | Each T-spline program in the `.smb` and `.smbh` members equals a TSM member                     |

The reader also checks the canonical patch program, the canonical text width and the order of subtype references. It rejects a knot multiplicity above the degree and a pole count above 65,536.

## Archives saved by current Fusion

Fusion 2706.1.17 often writes a few bytes after the final record of the ACT segment bulk stream. Kit refused these archives with `Unexplained trailing Fusion entity payload bytes`. The final record is a `RevGUIDACTDataMany` record, and its native member set has only `revGuidMap`.

`ReadDocSegment` now reads the last ACT record with `ReadSlack`. `DecodeSlack` returns the decoded record and its unread bytes. `ParsedSegment.BulkSlack` keeps those bytes, and `EmitDocSegment` writes them after the last record. Every other record and every other segment still refuses trailing bytes. `DecodeRecord` gives the new fields their defaults for legacy native state. The [ACT slack gotcha](../../../Gotchas/Conversion/Fusion/Records/FusionActBulkSlack.md) gives the save evidence.

Edited Form archives also store graphics world kind 2. `XferTSplineMut` reads and writes it with the BRep level-of-detail layout of `XferLodsMut`, without a `ValidBody` flag. The attribute rules add `OpacityAttribute` with `Absolute` and `Opacity`. The [edited world gotcha](../../../Gotchas/Conversion/Fusion/TSpline/EditedFormGraphicsWorld.md) gives the layout.

## Grid cage conversion

`ConvertGrid(Surface)` in `convert.formats.Fusion.BrepCodec.Journal.Spline.Conversion` returns a `GridResult`. The result holds the exact `NubsSurface`, the patch cells, four boundary curves, four corner points and the discontinuity lists.

| Step                     | Function                  | Result                                                                  |
| ------------------------ | ------------------------- | ----------------------------------------------------------------------- |
| Qualify the cage         | `CheckGridCage`           | The grip mapping, or `ValueError`                                       |
| Number the spokes        | `SpokeIndices`            | One spoke index from 0 to 3 for each link                               |
| Place the vertices       | `PlaceVertices`           | One grid position for each vertex                                       |
| Place the grips          | `PlaceGrips`              | Pole counts and the grip order of the poles                             |
| Make the knots           | `GridKnots`               | Multiples of the knot interval with end multiplicity 3                  |
| Make the patch program   | `GridPatches`             | One `PatchCell` for each face, spanning one knot interval per direction |
| Make the boundary        | `GridBounds`              | Four boundary curves in loop order                                      |
| Find the discontinuities | `GridJumps`, `ThirdJumps` | Interior knots with a third-derivative jump                             |
| Write a curve list       | `JumpCurve`               | An `exact_int_cur` with its order-3 discontinuity list                  |

`SwapEntity` replaces the converted surface, curves and corner points of one entity. It first checks that the entity holds the conversion of the old cage. It raises `ValueError` on a stale surface, a stale boundary curve, a stale corner point or another patch program.

`SwapGridCage(Model, Surface)` in `convert.formats.Fusion.DocumentCodec.Auxiliary.Form` returns a new `DocumentModel`. It needs exactly one Form and the same patch cells and knots for the old and the new cage. It replaces the cage, every converted history and snapshot entity, and sets `Graphics` to `None`. Fusion regenerates the graphics when it opens the document.

The [grid pole order gotcha](../../../Gotchas/Conversion/Fusion/TSpline/GridCagePoleOrder.md) gives the conversion rules. The [discontinuity gotcha](../../../Gotchas/Conversion/Fusion/TSpline/ConvertedDiscontinuityLists.md) gives the jump rule.

`CheckGridCage` accepts one knot interval c on every edge, where c is a whole number from 1 to 4096. `ConvertGrid` multiplies the knots, patch cells and progenitor windows by c. It computes the jump lists on the unit-parameter surface and scales them by c. The [knot interval gotcha](../../../Gotchas/Conversion/Fusion/TSpline/KnotIntervalConversion.md) gives the native probe and the refused cases.

## General cage conversion

Fusion converts a cage with a map that is linear in the homogeneous grips. The [linearity gotcha](../../../Gotchas/Conversion/Fusion/TSpline/ConversionIsLinear.md) gives the probe. Kit derives every part of that map from the cage topology. It ships no table for any layout, and nothing in `src` reads a Fusion save. `ConvertCage(Surface)` in `convert.formats.Fusion.BrepCodec.Journal.Spline.Stencil` builds the rows of the cage and returns a `CageResult`.

| Part           | Function or type                                                | Rule                                                                                                                                                                               |
| -------------- | --------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Face layout    | `CappedLayout`, `DrawLines`, `GroupBlocks`                      | A face is a block of cage faces. Creases and lines traced from extraordinary points bound it. The lines advance one link per round, and the line past a dart starts one round late |
| Face knots     | `SpokeKnots`                                                    | Unit knots per cage face, plus double knots at h and 2h from each extraordinary point                                                                                              |
| Regular poles  | `BuildTable`                                                    | Blossoms of the Catmull–Clark net at the face knots                                                                                                                                |
| Vertex points  | `LimitRow`                                                      | The Catmull–Clark limit mask                                                                                                                                                       |
| Cap knots      | `CapPlaces`                                                     | Along each spoke, the cap sees the knots of the strip of cells beside it                                                                                                           |
| Cap poles      | `SolveCaps`, `HardRows`, `WindowRows`, `RingRows`, `SolveLeast` | One exact linear solve per extraordinary point                                                                                                                                     |
| Creased caps   | `CreaseRows`                                                    | One crease at an extraordinary point keeps its net poles and replaces the rows that cross it with two crease relations                                                             |
| Spoke angles   | `RoundCosine`, `RoundSine`                                      | cos and sin of 2πk/n rounded from 90-digit `Decimal` values, so every platform writes the same bits                                                                                |
| Darts          | `DartRows`                                                      | A crease end at a valence-4 vertex is capped like valence 4, with midpoints across the crease line and ten mirror relations                                                        |
| Knot intervals | `KnotScale`                                                     | One whole-number interval c on every edge scales every parameter by c                                                                                                              |
| Row values     | `EvaluateRows`, `StencilRows`                                   | Each row applied to the homogeneous grips, with its pole weight and a weighted flag                                                                                                |
| Result         | `CageResult`, `FaceResult`                                      | Each face surface with its jumps, each boundary curve with its three lists, and each vertex point                                                                                  |
| Jump rule      | `SurfaceOrders`, `CurveOrders`                                  | The lowest jumping derivative order at each interior knot                                                                                                                          |
| Curve form     | `OrderCurve`                                                    | An `exact_int_cur` with all three discontinuity lists                                                                                                                              |
| Entity swap    | `SwapStencil`, `StencilSwap`                                    | Replaces the surfaces, the subtransform cage, the curves and the points of one entity                                                                                              |
| Document swap  | `SwapFormCage`                                                  | Replaces the cage and the converted bodies and snapshots of a one-Form document                                                                                                    |

The [cap gotcha](../../../Gotchas/Conversion/Fusion/TSpline/ExtraordinaryCapIsSolved.md) lists the cap rows and the experiments that recovered them. Every row has integer coefficients in 1, cos(2π/n), a knot ratio and 1/(n + 5). The rows leave no free direction. `SolveLeast` is a pivoted Householder solve in pure Python. It zeroes solution entries below its own rounding bound, so rounding residue on a weighted grip does not make a face rational.

A weighted cage needs no other rule. Its grips enter as (w x, w y, w z, w). A face or curve is rational only when one of its poles depends on a weighted grip, as the [weighted face gotcha](../../../Gotchas/Conversion/Fusion/TSpline/WeightedFaceRationality.md) records.

`ConvertCage` raises `ValueError` for a cage the rules cannot convert exactly. `SwapFormCage` needs the same layout for the old and the new cage. It checks that every stored surface, curve and point is the conversion of the old cage, and it refuses stale geometry. It keeps the patch cells, pcurves, edge convexity and naming of the document, and it sets `Graphics` to `None`. It refuses a new cage when `CageBody` refuses it or gives a crease edge another class than the old cage.

The [platform trigonometry gotcha](../../../Gotchas/Conversion/Fusion/TSpline/PlatformTrigBits.md) shows why the cap rules do not call `math.cos`.

`CheckVertices` accepts valence 8, and the [valence gotcha](../../../Gotchas/Conversion/Fusion/TSpline/CageValenceAboveFour.md) gives the native evidence.

## Source-free Form documents

`EmitFormDoc(FormSpec)` in `convert.formats.Fusion.DocumentCodec.Form` writes a complete Form `.f3d` from a cage and a typed converted body. It reads no source archive and copies no template bytes. Each document gets a new asset ID, new entity identities, a new geometry stamp and the current time.

`ConvertForm(Surface)` derives the body from the cage alone. It uses `GridBody(ConvertGrid(Surface))` for an open grid without interior creases and `CageBody` for every other cage.

| Type          | Fields                                                                                                                           |
| ------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| `FormSpec`    | `Title`, the `TsplineSurface` cage, the `FormBody`, optional body and feature names and a `MaterialSpec`                         |
| `FormBody`    | `PointsCm`, `Edges`, `Faces`, and `Regions` as one patch program for each face                                                   |
| `FormFace`    | `Surface`, `Uses` in loop order, `Label`, `DoubleSided`, `Contained`                                                             |
| `FormSurface` | `Cache` as the exact `NubsSurface`, six discontinuity lists, and `Region` as the patch program index                             |
| `FormEdge`    | Start and end vertex, `Curve` as an open clamped `BsCurve`, three discontinuity lists, `Convexity`, `Label`, `Windows`, `Bounds` |
| `FormUse`     | `EdgeIndex`, `Reversed`, `Pcurve` in face parameters over the full curve range, `Fit`                                            |
| `FormWindow`  | Cage face index and one progenitor parameter box                                                                                 |

| Function                                                 | Result                                                                                              |
| -------------------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| `ConvertForm(Surface)`                                   | The converted body of a supported cage, or `ValueError`                                             |
| `CageBody(Surface)`                                      | `ShapeBody`, then `ClassifyEdges` and `CheckFolds`                                                  |
| `ShapeBody(Surface)`                                     | The `ConvertCage` result placed in the body shape that `CappedLayout` computes from the cage        |
| `ClassifyEdges(Body)`                                    | Each crease edge with the class Fusion gives it, or `ValueError`                                    |
| `CheckFolds(Body)`                                       | `ValueError` for a folded face or edge                                                              |
| `GridBody(Result)`                                       | The body of a `ConvertGrid` result                                                                  |
| `CreateFormBrep(Surface, Model, Marks)`                  | History and snapshot journals in native record and owner order                                      |
| `FormLabels(Model)`                                      | Progenitor windows for each labelled face and edge                                                  |
| `BuildFormDesign(SpecValue, AssetId, Parts, UnixMicros)` | The Form feature, SubD node, control frame, T-spline serializer, progenitor tables and body records |
| `PackDocument(Design, Title, Parts)`                     | The member packing that `EmitDocument` and `EmitFormDoc` share                                      |
| `CheckFormSpec`, `CheckFormBody`                         | `ValueError` for bad text, labels, windows, pcurve ranges, loops and closed edges                   |

`CheckFormBody` refuses open loops, edges with more than two coedges and closed edges. It also refuses pcurve range faults, repeated labels and unknown cage faces.

The writer follows six native rules.

| Rule                                               | Gotcha                                                                                       |
| -------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| Records follow breadth-first order from the body   | [Converted record order](../../../Gotchas/Conversion/Fusion/TSpline/ConvertedRecordOrder.md) |
| Edge and vertex owners follow creation order       | [Converted owner order](../../../Gotchas/Conversion/Fusion/TSpline/ConvertedOwnerOrder.md)   |
| Split edge pieces share one curve and one pcurve   | [Split edge carriers](../../../Gotchas/Conversion/Fusion/TSpline/SplitEdgeCarriers.md)       |
| Progenitor windows are patch cell boxes            | [Progenitor windows](../../../Gotchas/Conversion/Fusion/TSpline/ProgenitorWindows.md)        |
| A closed body has `bodyType` 2                     | [Form body type](../../../Gotchas/Conversion/Fusion/TSpline/FormBodyType.md)                 |
| The cached tool entity needs a top-entity identity | [Cached tool identity](../../../Gotchas/Conversion/Fusion/TSpline/CachedToolIdentity.md)     |

The document has no graphics segment, texture mapping, browser entries or ACT body entries. Fusion accepted every document without them and builds the display when it opens the document. Fusion assigns progenitor labels in no fixed order, so Kit labels can differ from a native conversion of the same cage. No local archive has a label above 9.

`CappedLayout` computes the body shape from the cage. It gives the vertex and edge order, edge convexity, progenitor windows and bounds, and each face's loops, pcurves, sidedness and patch cells. Labels number the tagged edges after the faces. Each pcurve is an exact line in face parameters, so Kit writes a fit tolerance of 0. Fusion stores rounding values below 1e-14 cm there. `CageBody` then classifies the crease edges. Fusion numbers labels anew in each document, so a Kit label can differ from a native conversion of the same cage. The [seam pcurve gotcha](../../../Gotchas/Conversion/Fusion/TSpline/SeamPcurvePlacement.md) gives the rule for seams of closed faces.

## Crease edge classes

Fusion stores a class on each converted edge. A crease between two faces is `tangent` while the faces meet flat and `unknown` once they bend. Fusion also splits some bent creases into two edges. A fixed body shape cannot hold this, because the split point moves with the geometry. The [crease edge class gotcha](../../../Gotchas/Conversion/Fusion/TSpline/CreaseEdgeClass.md) gives the probe.

`ClassifyEdges` measures the signed angle between the two face normals at eight points per knot span, ends included. It refines the peak with a golden-section search. It splits a crease at flat knots. A sign change inside a cage span gets one cut, at the zero or at a cage knot, by the one-cut rule in the gotcha. Each piece is `tangent` when its largest angle is at most 1°, and `unknown` otherwise. `ClassifyEdges` raises `ValueError` for more than one sign change on an edge and for undecided branches of the one-cut rule. It also raises for a cut inside a span that holds only the refinement knots of both its ends.

| Measured piece                 | Kit class   | Native evidence                                                                          |
| ------------------------------ | ----------- | ---------------------------------------------------------------------------------------- |
| Largest angle at most 1°       | `tangent`   | Constant folds of 0.99999° and 1.0°; held-out peaks of 0.608°, 0.667°, 0.775° and 0.999° |
| Largest angle above 1°         | `unknown`   | Constant fold of 1.000001°; held-out peaks of 1.0006°, 1.002° and 1.216°                 |
| Flat knot inside a bent crease | split there | 333 saved archives: 5509 curve groups equal, 46 refused, 0 different                     |

An earlier version of this entry used 0.65° and 1.15° bounds and refused the band between them. The held-out cases above sit inside that band and follow the 1° rule.

Fusion refused cages whose faces fold back on themselves. `CheckFolds` samples four normals in each knot span of every face and four tangents in each span of every edge. It refuses a body when two neighbouring samples differ by 60° or more. The [folded cage gotcha](../../../Gotchas/Conversion/Fusion/TSpline/FoldedCageRefusal.md) gives the separation.

## Authoring boundary

The stored surface of a converted Form face is exact geometry. `t_spl_sur` derives from `exact_spl_sur`, and the kernel refuses a surface without its B-spline data. Fusion 2706.1.17 used a moved stored surface as the face geometry and kept it after `computeAll`. A set `TsSurface.bConversionFailed` flag did not start a conversion. No procedural surface route exists, so a writer must store the exact conversion. The [converted surface gotcha](../../../Gotchas/Conversion/Fusion/TSpline/ConvertedSurfaceIsExact.md) gives the evidence.

The `Body.cache` must derive physical properties from that geometry. [Derived mass caches](FusionFormMassCache.md) replace the earlier zero center with measured area, volume, center, and inertia.

Kit therefore authors only the cages that `ConvertGrid` or `ConvertCage` converts exactly.

| Cage                                                                        | Kit result                                       | Reason                                                                                                       |
| --------------------------------------------------------------------------- | ------------------------------------------------ | ------------------------------------------------------------------------------------------------------------ |
| Open plane grid without interior creases                                    | Exact conversion, document swap and new document | Each interior vertex has valence 4, and the limit surface is one B-spline                                    |
| Such a grid with one whole-number knot interval on every edge               | Exact conversion and new document                | A uniform interval scales the parameters and keeps the geometry                                              |
| A closed or creased quad cage with extraordinary points of valence 3 to 8   | Exact conversion, document swap and new document | The general rules give Fusion's linear map                                                                   |
| Such a cage with grip weights                                               | Exact rational conversion and new document       | The rules apply to the homogeneous grips                                                                     |
| Such a cage with one whole-number knot interval on every edge               | Exact conversion and new document                | The interval scales every parameter                                                                          |
| `G0CAPS`, `G1CAPS`, or `G2CAPS` with star smoothness 0, 1, or 2             | Exact conversion and new document                | Fusion ignores these declarations during its cap solve                                                       |
| A crease that Kit cannot classify                                           | `ValueError`                                     | Fusion may split the edge or give it another class                                                           |
| A swap that changes a crease edge class                                     | `ValueError` from `SwapFormCage`                 | The swap keeps the stored class, so `EmitFormDoc` writes a new document instead                              |
| A folded face or edge                                                       | `ValueError`                                     | Fusion refuses to convert the cage                                                                           |
| Face lines that reach one vertex in the same round from perpendicular sides | `ValueError`                                     | Fusion follows the grip geometry at these ties                                                               |
| Two creases at one extraordinary point                                      | `ValueError`                                     | Kit has no cap rule for them yet                                                                             |
| A dart with no extraordinary point or crease next to it                     | `ValueError`                                     | Fusion leaves the dart uncapped, and Kit has no rule for those poles yet                                     |
| Two dart lines that share one link                                          | `ValueError`                                     | Fusion leaves that link out, and Kit has no rule for the rest of these layouts yet                           |
| Grid grip weights other than 1                                              | `ValueError`                                     | No local archive holds a weighted grid conversion                                                            |
| Mixed or fractional grid knot intervals                                     | `ValueError`                                     | Fusion records jumps with a geometric test, and Kit's patch cells hold integers                              |
| A closed or creased cage with mixed or fractional knot intervals            | `ValueError`                                     | Kit has no rule for them yet                                                                                 |
| A new layout in an old document                                             | `ValueError` from both swaps                     | The Design progenitor tables and frame entities would change, so `EmitFormDoc` writes a new document instead |

The [cap gotcha](../../../Gotchas/Conversion/Fusion/TSpline/ExtraordinaryCapIsSolved.md) gives the cap region and the recovered cap rows. The [declaration acceptance](FusionCapDeclarationProfiles.md) qualifies the three cap types and three star values. The [layout gotcha](../../../Gotchas/Conversion/Fusion/TSpline/LayoutFollowsGeometry.md) gives the band cages. The [weighted face gotcha](../../../Gotchas/Conversion/Fusion/TSpline/WeightedFaceRationality.md) gives the rational rule. The [knot interval gotcha](../../../Gotchas/Conversion/Fusion/TSpline/KnotIntervalConversion.md) gives the interval probe.

Fusion keeps a stale stored body without a warning, as the [stored body authority gotcha](../../../Gotchas/Conversion/Fusion/TSpline/StoredFormBrepAuthority.md) shows. Kit therefore refuses every cage whose crease class or fold it cannot match.

## Verification

[The production round trip](../../../../re/Fusion/Reconstruction/FormDocuments/RoundTrip.json) read 32 local Form archives with Python 3.14.7. All 32 archives gave an equal model after `EmitParsed` and equal member names. All members were byte-equal after decompression, except the `.protein` material packages. The existing material writer emits those packages in canonical form.

The [spline census](../../../../re/Fusion/Reconstruction/FormDocuments/SplineCensus.json) read all 64 BRep members of the 32 archives. Every embedded program equals the TSM member of its archive.

The [ACT slack census](../../../../re/Fusion/Reconstruction/ActSlack/SlackCensus.json) read 72 focus archives that earlier stopped on the trailing bytes. All 72 read, gave an equal model after `EmitParsed` and gave byte-equal ACT streams. In the 308-archive corpus, 76 archives read with slack bytes and 164 without. The remaining 68 stop for other reasons.

The [grid census](../../../../re/Fusion/Reconstruction/FormDocuments/GridCensus.json) compared `ConvertGrid` with every converted Form body in 68 local Form archives.

| Result    | Archives | Detail                                                                                  |
| --------- | -------- | --------------------------------------------------------------------------------------- |
| Equal     | 28       | Knots, patch cells, discontinuity lists and curve forms equal, points within 8.9e-16 cm |
| Refused   | 35       | Box, symmetric box and interior crease cages                                            |
| Different | 4        | Deliberately stale probe variants                                                       |
| No body   | 1        | The probe variant without BRep members                                                  |

[Grid acceptance](../../../../re/Fusion/LocalOracle/FormDocuments/Grid/NativeAcceptance.json), SHA-256 `ba7536f4cfed4b6cc60a50aed672d62bbcb96168571c3050527f4fd024266769`, has status `accepted` in Fusion 2706.1.17. Zero documents were open before and after the run. `PrepareGrid.py` wrote an affine and a warped 2 × 3 plane cage, and `SwapGridCage` put each cage into the native plane document. The [preparation](../../../../re/Fusion/LocalOracle/FormDocuments/Grid/Preparation.json) binds each input to its SHA-256.

For each case, Fusion converted the same TSM in a new Form as the oracle. Both documents then ran `computeAll`, moved the first cage vertex by (0.11, 0.07, 0.13) cm, converted, saved and reopened. The run compared body counts, area, NURBS poles and knots, 49 face points, 28 edge points and vertices within 1e-8.

| Case   | Area as loaded (cm²) | Area after edit (cm²) | Largest Kit and oracle gap (cm)  | Problems |
| ------ | -------------------- | --------------------- | -------------------------------- | -------- |
| Affine | 3.981294020792737    | 3.9230459543150173    | 4.4e-16 before the edit, 0 after | 0        |
| Warped | 4.005512887961321    | 3.9455217633195576    | 4.4e-16 before the edit, 0 after | 0        |

The Form health and the timeline health were 0 at every stage. The cage TSM digests were equal, and the reopened Kit body equalled the edited body. The same run converted four new plane primitives, which the grid census found equal.

| Faces | Size (cm) | Poles | Area (cm²)        |
| ----- | --------- | ----- | ----------------- |
| 1 × 1 | 2.0 × 1.5 | 4 × 4 | 3.0               |
| 3 × 2 | 3.0 × 2.0 | 6 × 5 | 6.000000000000001 |
| 4 × 4 | 2.5 × 2.5 | 7 × 7 | 6.249999999999998 |
| 2 × 5 | 1.7 × 4.1 | 5 × 8 | 6.969999999999999 |

[Form acceptance](../../../../re/Fusion/LocalOracle/FormDocuments/Acceptance/NativeAcceptance.json), SHA-256 `b018171b82ad933a65611f5e56b54f0b48b6660bae06bc936267544f876fa552`, has status `completed` in Fusion 2706.1.17. All four re-emitted cases have status `accepted`, and zero documents remained open. Each case compared the native control and its `EmitParsed` output within 1e-7 through open, edit, conversion, save and reopen.

| Case          | Faces, edges, vertices | Area before edit (cm²) | Area after edit (cm²) | Volume after edit (cm³) |
| ------------- | ---------------------- | ---------------------- | --------------------- | ----------------------- |
| Plane         | 1, 4, 4                | 3.831410566653259      | 3.75882224444742      | None, open sheet        |
| Creased plane | 2, 7, 6                | 3.8314105666532576     | 3.7597048123427688    | None, open sheet        |
| Box           | 6, 12, 8               | 23.395349005089184     | 23.229292504382165    | 9.339333654763482       |
| Symmetric box | 6, 12, 8               | 23.229718749711484     | 22.896262895240067    | 9.137857029717933       |

The re-emission report scope reads "Production Form document re-emission and source-free authoring". That run covered only the four re-emitted controls, and the reports below cover new documents. The report stays unchanged, because tests pin the archives it saved.

### Stencil and source-free verification

`StencilCensus.py` compared `ConvertCage` with every converted body in the local Form archives. Probe outputs in ignored folders were excluded.

| Result    | Archives | Detail                                                                                                    |
| --------- | -------- | --------------------------------------------------------------------------------------------------------- |
| Equal     | 127      | Layout, jumps and points within 1e-12 cm                                                                  |
| Different | 6        | Two stale probe variants, and four saves of the edited fresh creased plane, where Fusion split the crease |
| Refused   | 56       | Layouts without a table                                                                                   |
| No body   | 1        | The probe variant without BRep members                                                                    |

`BuildShapes.py` compared `CageBody` with the 88 Fusion-saved archives among the equal ones. Every archive had equal structure, edge classes and split bounds, and the geometry stayed within 1.2e-13 cm. The [shape report](../../../../re/Fusion/Reconstruction/FormDocuments/Cages/StencilShapes.json) lists them. The [crease check](../../../../re/Fusion/Reconstruction/FormDocuments/Cages/CreaseCheck.json) and the [fold check](../../../../re/Fusion/Reconstruction/FormDocuments/Cages/FoldCheck.json) found no Kit body that differs from a Fusion conversion.

Three Fusion 2706.1.17 runs accepted Form documents that Kit wrote. Each run converted the same TSM in a new Form as the oracle. Both documents then ran `computeAll`, moved the first cage vertex by (0.11, 0.07, 0.13) cm, converted, saved and reopened. Each run compared body counts, area, NURBS poles and knots, 49 face points, 7 edge points and the vertices within 1e-8 cm.

| Report                                                                                                 | SHA-256                                                            | Status     | Kit documents                                    |
| ------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------ | ---------- | ------------------------------------------------ |
| [Source-free bodies](../../../../re/Fusion/LocalOracle/FormDocuments/Sourceless/NativeAcceptance.json) | `acc43da40fa16f28a3441f719c43cf6608b0b56081e1606495e2a986fd646ee4` | `accepted` | `EmitFormDoc` with typed bodies for 9 cages      |
| [Cage documents](../../../../re/Fusion/LocalOracle/FormDocuments/CageDocuments/NativeAcceptance.json)  | `76d2a6a35c902f6776270584b1db9363b0f6ecb9c4c2e85c3e68e26822a7ad8f` | `accepted` | `EmitFormDoc` with `ConvertForm` for 14 cages    |
| [Stencil swaps](../../../../re/Fusion/LocalOracle/FormDocuments/StencilAccept/NativeAcceptance.json)   | `f7455953a99fb482fa03054aa73e165a40cbf0d683c87a8139f6dae84e25a95d` | `accepted` | `SwapFormCage` into native documents for 8 cages |

Zero documents were open before and after each run. The Form health and the timeline health were 0 at every stage. Each reopened Kit body equalled the edited body, and every closed body stayed solid.

The cage documents took no archive. `ConvertForm` derived each body from the cage alone. The fresh cages took no part in any fit, and the bent, sagged, twisted and sheared cages are new copies of the vendor creased cages. The oracle was also saved as loaded, so its stored edge classes could be compared offline.

| Case                  | Faces, edges, vertices | Area as loaded (cm²) | Area after edit (cm²) | Largest gap as loaded (cm) |
| --------------------- | ---------------------- | -------------------- | --------------------- | -------------------------- |
| `BoxFresh`            | 6, 12, 8               | 23.543022052059037   | 23.484368118612267    | 7.1e-15                    |
| `SymmetricBoxEdited`  | 6, 12, 8               | 22.837549328910285   | 22.735439828294098    | 2.1e-14                    |
| `CreasedPlaneFresh`   | 2, 7, 6                | 3.831446875868536    | 3.751922143715863     | 1.3e-15                    |
| `CreasedBoxFresh`     | 6, 13, 9               | 24.286028645961512   | 24.27966734709038     | 1.3e-14                    |
| `Valence5Fresh`       | 15, 35, 22             | 10.579733049533365   | 10.510589959352087    | 3.6e-15                    |
| `Valence6Fresh`       | 18, 42, 26             | 12.540048386693941   | 12.474206238754762    | 3.6e-15                    |
| `Box3Fresh`           | 6, 12, 8               | 28.60001685047017    | 28.481826713359624    | 1.2e-13                    |
| `Valence8Fresh`       | 24, 56, 34             | 13.143629176608274   | 13.134359230274287    | 2.1e-14                    |
| `WarpedPlane2x5`      | 1, 4, 4                | 7.143108592709405    | 7.038433908537573     | 1.8e-15                    |
| `CreasedPlaneBent`    | 2, 7, 6                | 3.929028440510323    | 3.8470292464903597    | 2.2e-16                    |
| `CreasedPlaneSagged`  | 2, 7, 6                | 3.9404048270724457   | 3.823898600209727     | 1.1e-16                    |
| `CreasedPlaneTwisted` | 2, 7, 6                | 3.8702499737628746   | 3.8024908538099353    | 4.4e-16                    |
| `CreasedBoxBent`      | 6, 13, 9               | 23.571026638609418   | 23.405094988123405    | 1.4e-14                    |
| `CreasedBoxSheared`   | 6, 13, 9               | 23.590510721183374   | 23.394285219832177    | 1.3e-14                    |

After the edit, the largest gap was 0 in every case. The Kit bodies equalled the loaded oracles in structure, edge classes and split bounds within 1.2e-13 cm.

The source-free body run gave each research-fed body to `EmitFormDoc` as a typed `FormBody`. `ConvertGrid` supplied the five grid bodies.

| Case               | Faces, edges, vertices | Area as loaded (cm²) | Area after edit (cm²) | Largest gap as loaded (cm) |
| ------------------ | ---------------------- | -------------------- | --------------------- | -------------------------- |
| Plane 1 × 1        | 1, 4, 4                | 3.0                  | 2.85375636404167      | 0                          |
| Plane 3 × 2        | 1, 4, 4                | 6.0                  | 5.900167254284977     | 8.9e-16                    |
| Plane 4 × 4        | 1, 4, 4                | 6.249999999999998    | 6.189896521978717     | 8.9e-16                    |
| Plane 2 × 5        | 1, 4, 4                | 6.9700000000000015   | 6.887988261463161     | 2.7e-15                    |
| Warped plane 4 × 4 | 1, 4, 4                | 6.412367656900344    | 6.405429498637167     | 1.6e-15                    |
| Box                | 6, 12, 8               | 23.560443509000663   | 23.395349005089184    | 0                          |
| Symmetric box      | 6, 12, 8               | 23.560443509000667   | 23.229718749711484    | 0                          |
| Creased box        | 6, 13, 9               | 23.55271091736829    | 23.386849155615973    | 0                          |
| Creased plane      | 2, 7, 6                | 3.8314105666532576   | 3.7597048123427688    | 0                          |

The four flat grids also matched a new plane primitive of the same face counts and size within 2.7e-15 cm.

The stencil swap run put eight fresh cages into native documents of their layouts with `SwapFormCage`. Each Kit body equalled the loaded oracle within 1.2e-13 cm and the edited oracle exactly. The [acceptance check](../../../../re/Fusion/Reconstruction/FormDocuments/Stencil/StencilAcceptCheck.json) converted each cage that Fusion saved after the edit. `ConvertCage` equalled seven saved bodies within 1.2e-13 cm. Fusion split the crease of the edited creased plane, so `SwapFormCage` refuses the saved document as a swap source.

The creased plane swap document predates the crease class rule. Its vendor carrier stores the crease as `tangent`, and the fresh cage bends it to `unknown`. `SwapFormCage` now refuses that swap, so the tests pin the other seven swap documents. The cage document run covers the fresh creased plane with `EmitFormDoc`.

Remote integration cases cover the 32 Form archives, the ACT slack archives, the edited worlds and 66 spline journal members. Grid cases cover 17 native archives, three refusals, two document swaps with their emitted SHA-256, three cage faults, a stale body and a layout change.

Stencil and cage cases in `tests/convert/formats/FusionCodec/Documents/Form/` cover the following.

| Test                                 | Cases                                                                                                                                                                 |
| ------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `TestNativeCage`, `TestCageBody`     | 91 Fusion-saved archives, with `CageBody` equal to the stored body within 1e-12 cm                                                                                    |
| `TestCageDoc`                        | 15 cage documents, each equal to the cage, the stored body, the loaded oracle and a new `EmitFormDoc` read                                                            |
| `TestStencilSwap`                    | 7 swap documents with their emitted SHA-256                                                                                                                           |
| `TestCreaseClass`, `TestCreaseFault` | The carrier and bent crease classes against Fusion, the split fresh creased plane against its Fusion save, the class-change swap refusal and the crease-end cut guard |
| `TestCurveFrame`, `TestSurfaceAxes`  | Exact linear frames at Greville abscissae                                                                                                                             |

No local tests ran. Two scratch scripts repeated the assertions of these tests and of the grid tests with Python 3.14.7. All 214 checks passed.

### Fourth pass verification

Two Fusion 2706.1.17 runs accepted new Form documents that `EmitFormDoc` wrote from the cage alone. Each run followed the stages of the cage document run above. Zero documents were open before and after each run, and every case has status `accepted`.

| Report                                                                                                         | SHA-256                                                            | Cases                                                                            |
| -------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------ | -------------------------------------------------------------------------------- |
| [Fourth pass documents](../../../../re/Fusion/LocalOracle/FormDocuments/FourthDocuments/NativeAcceptance.json) | `d177065b1b2287601ef4bc3e1ab3d4ff94b6557406cc764153675c7329d8577d` | A fresh valence-7 cage and four weighted cages                                   |
| [Interval documents](../../../../re/Fusion/LocalOracle/FormDocuments/IntervalDocuments/NativeAcceptance.json)  | `755d2e35d810186dcb45a7d0eda49d23566f489fbda58e03e6bf7f567d57225c` | Two warped grids with knot intervals 2 and 3                                     |
| [Merged head documents](../../../../re/Fusion/LocalOracle/FormDocuments/MergeDocuments/NativeAcceptance.json)  | `184566db0f35f7ac49e3b3a1e1f127493999a85b59ec9d3653e905a54ae68d48` | The box, creased plane, valence-5 and warped grid cages of the cage document run |

| Case                | Faces, edges, vertices | Area as loaded (cm²) | Area after edit (cm²) | Largest gap as loaded (cm) |
| ------------------- | ---------------------- | -------------------- | --------------------- | -------------------------- |
| `Valence7Fresh`     | 21, 49, 30             | 12.1076641108887     | 12.014609582409966    | 1.6e-14                    |
| `Valence7Weighted`  | 21, 49, 30             | 12.126013678022659   | 12.114258327348793    | 1.9e-14                    |
| `BoxWeightedFresh`  | 6, 12, 8               | 23.640153774345265   | 23.462135431924096    | 7.1e-15                    |
| `Box3Weighted`      | 6, 12, 8               | 28.227654165229573   | 28.131735379756748    | 1.2e-13                    |
| `Valence5Weighted`  | 15, 35, 22             | 10.82315963705559    | 10.803688424609216    | 2.9e-15                    |
| `Plane4x4Interval2` | 1, 4, 4                | 6.417836145942383    | 6.421953618522543     | 1.8e-15                    |
| `Plane2x5Interval3` | 1, 4, 4                | 6.935094773160379    | 6.937615110741065     | 2.7e-15                    |

After the edit, the largest gap was 0 in every case. The weighted cases compared the NURBS weights from the API as well. The fresh valence-7 cage took no part in the fit. `PrepareFourthDocs.py` moved its grips at random.

[`WeightCheck.py`](../../../../re/Fusion/Reconstruction/FormDocuments/Stencil/WeightCheck.json) converted the stored cage of 23 Fusion-saved archives with `ConvertCage`. They are the seven weighted box probes, one Fusion edit with near-unit weights and the 15 fourth-pass archives. Every face form, curve form and jump list was equal, and every point was within 1.2e-13 cm. In `Box3Weighted`, 4 of the 6 faces are rational in both bodies.

[`IntervalCheck.py`](../../../../re/Fusion/Reconstruction/FormDocuments/IntervalCheck.json) converted the stored cage of 17 interval archives with `ConvertForm`. Kit equalled all nine accepted conversions within 6.2e-15 cm, apart from labels. The progenitor windows differed by at most 8.9e-16 from the Fusion values. Kit refused the four other readable archives with the errors of the knot interval gotcha. It could not read the other four.

[`LayoutDrift.py`](../../../../re/Fusion/Reconstruction/FormDocuments/Stencil/LayoutDrift.json) found no layout change in the 55 valence-7 variants. It found four changes in the two band cages, which Kit refuses.

The merged head writes larger class tables than the third pass. The design segment declares 208 classes instead of 204, and the ACT segment declares 16 instead of 15.

| Segment | Classes added                                                                      | Records of these classes |
| ------- | ---------------------------------------------------------------------------------- | ------------------------ |
| Design  | `DcAssemblyFeature`, `DcPlaceComponentInstance`, `DcXRefPCIFeature`, `XRefManager` | 0                        |
| ACT     | `ACTRefdTable`                                                                     | 0                        |

The external link reader added these classes to `DesignClasses.json` and `ActClasses.json`. `AuthorSchemas` joins every design class for a Form, and `BuildAssembly` declares every ACT class. The third pass was built on a base without that reader, so its recorded documents lack the classes. The squash merge resolution did not change the Form branch of `AuthorSchemas`. The third-pass source with only the typed-body port shows the same five added classes. Features round two also gave the XZ origin plane its native frame, as the [revolve frame gotcha](../../../Gotchas/Conversion/Fusion/Features/FeatureRevolveFrame.md) records. With the clock pinned, the BRep, snapshot and cage parts still equal the third-pass documents byte for byte.

[`PrepareMergeDocs.py`](../../../../re/Fusion/LocalOracle/FormDocuments/MergeDocuments/Preparation.json) wrote four accepted third-pass cages again from the merged head. Fusion accepted all four with zero documents open before and after. The [gap report](../../../../re/Fusion/Reconstruction/FormDocuments/Cages/MergeDocumentsGap.json) gives the same largest gaps and areas as the third-pass run. The fourth-pass documents above already carried the larger tables.

The fourth pass adds the three unweighted valence-7 archives to `TestNativeCage` and `TestCageBody`. It adds the valence-7 cage document to `TestCageDoc` and the valence-7 cage to `TestStencilCage`. The weighted archives stay out of these cases. Their stored weights differ from the stencil weights by up to 5.0e-14, and `TestCageBody` compares weights exactly. `TestFormChoice` and `TestCageFault` now expect a weighted stencil cage to convert with rational faces. They expect a stencil cage with knot interval 2 to raise the unit-interval error.

No tests ran locally. The checks above call production code on Fusion-saved archives.

### General conversion verification

The checks in this section ran `ConvertForm` with the general rules. No stencil or shape table existed any more.

[`StencilCensus.py`](../../../../re/Fusion/Reconstruction/FormDocuments/Stencil/StencilCensus.json) compared Kit with every converted body in 279 local Form archives.

| Result    | Archives | Detail                                                                                                           |
| --------- | -------- | ---------------------------------------------------------------------------------------------------------------- |
| Equal     | 259      | Layout, jumps and points within 1e-12 cm                                                                         |
| Different | 7        | Six deliberately stale probe variants, and the first-run Kit swap document of the fresh creased plane            |
| Refused   | 11       | Four face line ties, six grid cages with mixed or fractional intervals, and one capped cage with mixed intervals |
| No body   | 2        | Probe variants without BRep members                                                                              |

[`StencilCheck.py`](../../../../re/Fusion/Reconstruction/FormDocuments/Stencil/StencilCheck.json) converted every probe variant of 16 cages. All variants of the eight old layouts matched, CreasedBox included, within 2.2e-13 cm. So did the warped, limit and weighted variants. The two band cages refuse at a tie.

[`AcceptGeneral.py`](../../../../re/Fusion/LocalOracle/FormDocuments/General/Accept/GeneralAcceptance.json), SHA-256 `4a8b000974e0c6007c7db4849e27954650fbdced4d00536088a60a4ce6b58a83`, has status `accepted` in Fusion 2706.1.17. `PrepareAccept.py` wrote each document with `EmitFormDoc` and `ConvertForm` from the cage alone. The [preparation](../../../../re/Fusion/LocalOracle/FormDocuments/General/Accept/Preparation.json) binds each input to its SHA-256 and lists the refused cages. The run followed the stages of the cage document run. Zero documents were open before and after. All 30 prepared cases matched Fusion's conversion of the same TSM within 1e-8 cm, with zero problems. The documents were prepared and run again after the cap rules moved to `RoundCosine` and `RoundSine`. No measured value moved by more than 1e-12 cm.

- Old: the eight old layouts.
- Probe: nine research probe cages. The cap rule was not fitted on them, but some of them fed the knot rule.
- Held out: thirteen cages that no rule was fitted on. They hold extraordinary points of valence 3, 5, 6 and 7, crease loops and rings, weighted grips, tori and a knot interval of 3.
- Refused: `TPrism`, `Mixed56`, `Mixed78` and `HeldBand67` raise at a face line tie.

| Case                | Group    | Valences                 | Faces, edges, vertices | Area as loaded (cm²) | Area after edit (cm²) | Largest gap (cm) |
| ------------------- | -------- | ------------------------ | ---------------------- | -------------------- | --------------------- | ---------------- |
| `Box`               | Old      | 3, 4                     | 6, 12, 8               | 23.484368118612274   | 23.431704440077617    | 1.0e-13          |
| `Box3`              | Old      | 3, 4                     | 6, 12, 8               | 28.48182671335966    | 28.481160761869866    | 6.9e-14          |
| `CreasedBox`        | Old      | 3, 4 (creased)           | 6, 13, 9               | 24.27966734709037    | 24.10271579706552     | 1.0e-13          |
| `CreasedPlane`      | Old      | 2, 3, 4 (creased)        | 2, 7, 6                | 3.7597048123427688   | 3.691251216723625     | 8.9e-16          |
| `Valence5`          | Old      | 3, 4, 5                  | 15, 35, 22             | 10.510589959352096   | 10.394131636846513    | 4.6e-14          |
| `Valence6`          | Old      | 3, 4, 6                  | 18, 42, 26             | 12.474206238754784   | 12.395947017411098    | 2.6e-14          |
| `Valence7`          | Old      | 3, 4, 7                  | 21, 49, 30             | 12.28897376711801    | 12.217612705283472    | 2.0e-13          |
| `Valence8`          | Old      | 3, 4, 8                  | 24, 56, 34             | 13.134359230274315   | 13.128502445960223    | 2.8e-14          |
| `Box111`            | Probe    | 3                        | 6, 12, 8               | 5.845731683838702    | 5.822240282144422     | 4.6e-14          |
| `Box122`            | Probe    | 3, 4                     | 6, 12, 8               | 12.088906023312536   | 11.93656580645122     | 5.8e-14          |
| `Box234`            | Probe    | 3, 4                     | 6, 12, 8               | 27.58783572712836    | 27.592333172315694    | 8.2e-14          |
| `LPrism`            | Probe    | 3, 4, 5                  | 12, 26, 16             | 7.904129364568432    | 7.8553927380552135    | 5.9e-14          |
| `Step`              | Probe    | 3, 4, 5                  | 12, 26, 16             | 7.910602693620569    | 7.774369611969879     | 5.8e-14          |
| `Valence5Tall`      | Probe    | 3, 4, 5                  | 15, 35, 22             | 13.158356675481109   | 13.075617120115014    | 6.0e-14          |
| `Valence3Prism`     | Probe    | 3, 4                     | 9, 21, 14              | 6.786962654462904    | 6.783372105049515     | 1.5e-14          |
| `Torus86`           | Probe    | 4                        | 1, 2, 1                | 27.044407188979726   | 26.901289663457938    | 7.1e-15          |
| `SharpBox`          | Probe    | 3, 4 (creased)           | 6, 12, 8               | 23.932248919442692   | 23.9060162031994      | 2.7e-15          |
| `HeldBox113`        | Held out | 3, 4                     | 6, 12, 8               | 14.925261606906046   | 14.728107373688193    | 8.6e-14          |
| `HeldCreaseBands`   | Held out | 4 (creased)              | 2, 4, 2                | 23.580751153210173   | 23.385041376123965    | 6.2e-15          |
| `HeldCreaseCross`   | Held out | 4 (creased)              | 1, 4, 3                | 24.435800774434043   | 24.264627401199608    | 7.1e-15          |
| `HeldCreaseLoop`    | Held out | 4 (creased)              | 1, 4, 3                | 22.020133779331953   | 21.882601683942617    | 2.7e-15          |
| `HeldCreaseRing`    | Held out | 4 (creased)              | 1, 2, 1                | 23.258507703051908   | 23.0645913280038      | 3.6e-15          |
| `HeldCreaseSlices`  | Held out | 4 (creased)              | 2, 8, 6                | 23.081858565694176   | 22.91927861234047     | 1.8e-15          |
| `HeldInterval7`     | Held out | 3, 4, 7                  | 21, 49, 30             | 15.54846532616437    | 15.479889629841859    | 1.1e-13          |
| `HeldPrism3`        | Held out | 3, 4                     | 9, 21, 14              | 7.651106391658699    | 7.5996429108623476    | 2.0e-14          |
| `HeldPrism5`        | Held out | 3, 4, 5                  | 15, 35, 22             | 14.693249836881709   | 14.67340314680529     | 5.7e-14          |
| `HeldTorus75`       | Held out | 4                        | 1, 2, 1                | 23.290357011652016   | 23.09376978900068     | 8.9e-16          |
| `HeldWeighted6`     | Held out | 3, 4, 6 (weighted)       | 18, 42, 26             | 11.282823111129135   | 11.22638938811335     | 2.1e-14          |
| `HeldWeightedSharp` | Held out | 3, 4 (creased, weighted) | 6, 15, 11              | 24.7770081833092     | 24.4595888956437      | 3.6e-15          |
| `HeldWeightedTorus` | Held out | 4 (weighted)             | 1, 2, 1                | 24.697474176855074   | 24.744389106308795    | 5.3e-15          |

`CollectAccept.py` kept Fusion's conversion of each accepted case under `General/Accept/Fusion`. The scrubber changed no byte in them. `TestGeneralCase` converts each Kit TSM and compares the result with the kept save. Offline, all 30 matched within 2.0e-13 cm.

[The stencil swap rerun](../../../../re/Fusion/LocalOracle/FormDocuments/StencilAccept/General/NativeAcceptance.json), SHA-256 `d9efa56868d16dd066c29111803fec97c59f554f5147bec061ce5bdd92431fdf`, put the fresh cages into their native documents again with `SwapFormCage`. Fusion accepted all seven swap documents within 1e-8 cm. `SwapFormCage` refused the fresh creased plane, because the fresh cage changes a crease class. The swap bytes changed, so `TestStencilSwap` pins the new SHA-256 values. They were prepared again with `RoundCosine` and `RoundSine`, and the pinned values are equal on macOS and Linux.

[`CreaseRuleCheck.py`](../../../../re/Fusion/Reconstruction/FormDocuments/Crease/CreaseRuleCheck.json) replayed the crease rule over 1484 Fusion-saved Form archives, 44 of them unreadable. Of 41863 shared curve groups, 41811 matched Fusion's pieces and labels, 38 were refused and 14 differed. The 14 are 13 groups in crease-end probe saves and the wide L-turn probe. The replay also converted every cage that the general rules accept. 793 bodies matched Fusion's pieces and labels, 10 were refused, and none differed.

The read gap fix reads the four interval archives that failed before, as the [knot interval gotcha](../../../Gotchas/Conversion/Fusion/TSpline/KnotIntervalConversion.md) records.

The tests follow the general rules. `TestGeneralCase` pins the 30 accepted cases. The fold cases of `CreaseTests` expect the pieces of the one-cut rule, and its fold body now orients faces as the seam pcurve rule does. `TestTeeBlocks` expects the tee cube to raise at its face line tie, and `TestDartRefusal` expects a dart with plain neighbours to raise. `TestEdgeKnots` expects `ConvertForm` to refuse a `KnotSurface` whose edge knots differ from the intervals. No tests ran locally.
