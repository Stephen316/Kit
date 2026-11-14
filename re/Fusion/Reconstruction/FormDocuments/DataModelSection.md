# Draft section for the Fusion data model: Form documents

This draft is for a new section after "T-spline control cages and orientation" in `Documentation/Reference/Research/FusionDataModel.md`.
The section text starts at the next heading.
Links are relative to `Documentation/Reference/Research/`.

## Form documents

A Form document joins one T-spline control cage to one converted BRep body.
The cage is the `.tsm` member in `TSplines.BlobParts`.
The converted body is committed ACIS geometry in `Breps.BlobParts`.
`ReadDocument` reads the complete graph, and `EmitParsed` writes it again.
`DocumentModel.Forms` holds one `DocumentForm(Name, Surface)` for each TSM member.

### Design graph

The Design segment adds these classes to an ordinary body document.

| Class | Fields that join the graph | Target |
| --- | --- | --- |
| `DcTSplineFeature` | `rTSplineToolBody`, `subDInfoMap`, `dcBodies`, `childNodes`, `rProgenitorTable`, `rDirectModelingData` | Tool body, surface node, `DcBody`, progenitor tables |
| `493A89BA-E146-498D-9033-2783FE727AF4` | `rBaseFeature` | The Form feature |
| `DcTSplineToolBody` | `rTSplineFeature`, `toolbodyCaches` | The Form feature, `ETCachedTopology` |
| `TsSurface` | `rSerializer`, `frame`, `rVSurface`, `tess` | Serializer, control frame, surface node, `SurfaceTessellation` |
| `TSplineSerializer` | `partName`, `rSurface` | `TSplines.BlobParts/TSpline.<uuid>.tsm`, `TsSurface` |
| `ControlFrameMesh` | `facets`, `edges`, `vertices`, `grips`, `rSurface` | Frame entities, `TsSurface` |
| `ControlFrameFacet`, `ControlFrameEdge`, `ControlFrameVertex`, `ControlFrameGrip` | `rMesh`, `tsID` | `ControlFrameMesh`, TSM table index |
| `SubDSurfaceNode` | `rDcTSplineFeature`, `rSurface`, `rGroupParent`, named `BASEFEAT_PM_BODIES_REF` | Feature, `TsSurface`, cache `Bodies`, converted `Body` |
| `Body` | named `FORMFEAT_DM_SUBD_REF`, `rGroupParent` | `SubDSurfaceNode`, history `Bodies` |
| `TSplineEntityProgenitor` | `entityType`, `tsEntityProgenitors` | TSM faces and parameter windows |

The `subDInfoMap` maps the surface node to an operation identifier and a `ProgenitorTable`.
That table lists one `TSplineEntityProgenitor` for each named face or boundary edge of the converted body.
Each entry lists TSM face indexes with a `(uLow, uHigh, vLow, vHigh)` window.
Type 0 entries have full windows and name converted faces.
Type 1 entries collapse one parameter and name boundary edges.
The plane control has one type 0 and four type 1 entries.
The box controls have six type 0 entries.

The component has two `Bodies` groups.
The history group owns the converted `Body` and the `BRepHistorySerializer` of the `.smbh` member.
The cache group, `FusionComponent.rCacheBodies`, owns the surface node and the `BRepSerializer` of the `.smb` member.

### Kit joins

`CheckDocForms` runs during read and before emission.

| Join | Rule |
| --- | --- |
| Serializer and part | Each `partName` names one TSM member, and each member has one serializer |
| Serializer and surface | `TsSurface.rSerializer` names the serializer that names the surface |
| Control frame | Facet, edge, vertex and grip `tsID` values are `range(n)` for the TSM table counts |
| Surface node | `TsSurface.rVSurface` names the node, and the node names the surface |
| Converted body | The node vector names each `Body`, and each `Body` names the node back |
| Embedded program | Every T-spline program in the `.smb` and `.smbh` members equals a TSM member |

### Converted BRep grammar

The converted body uses three ACIS entity kinds that ordinary documents do not use.

| Entity | Subtype scope | Contents |
| --- | --- | --- |
| `spline-surface` | `t_spl_sur` or `ref` | Revision, exact bicubic `nubs` surface, fit tolerance, six jump arrays, four optional ranges, type code, `t_spl_subtrans_object` or `ref`, face index |
| `intcurve-curve` | `exact_int_cur` | Revision, cached `nubs` curve, fit tolerance, null supports, cache bounds, three jump arrays, extension, two ranges, two codes |
| `pcurve` | `exp_par_cur` | Cached 2D `nubs` curve, fit tolerance, `spline` support with a `t_spl_sur` definition or `ref`, four optional bounds, U and V offsets |

The `t_spl_subtrans_object` scope stores the complete TSM program and a patch program.
The patch program has one line for each converted face.
Each line lists TSM faces with a window and an offset.
A `ref N` scope indexes a table of subtype definitions in stream order.
Text uses tag 7 up to 255 bytes and tag 8 above.
The [subtype gotcha](../../../../Documentation/Gotchas/Conversion/Fusion/TSpline/SplineSubtypeTable.md) and the [text width gotcha](../../../../Documentation/Gotchas/Conversion/Fusion/TSpline/SplineTextWidth.md) give the measured values.

### Converted body authority

Fusion 2706.1.17 takes the editable cage from the TSM member.
It takes the body from the stored BRep members.
It did not convert the cage again on open, on `computeAll`, or on an empty edit.
It refused to open a Form document without the BRep members.
It accepted a stale BRep with health 0.
The [authority gotcha](../../../../Documentation/Gotchas/Conversion/Fusion/TSpline/StoredFormBrepAuthority.md) gives the variants.

A `t_spl_sur` record holds a stored B-spline surface.
Fusion used a moved stored surface as the face geometry, and a set `TsSurface.bConversionFailed` flag did not start a conversion.
So the stored surface is the exact face geometry, not an approximation of the program.
Earlier binary inspection also said that `t_spl_sur` derives from `exact_spl_sur` and that the kernel refuses one without the stored surface.
That evidence was removed, and those two claims are not confirmed by a black-box experiment.
The [converted surface gotcha](../../../../Documentation/Gotchas/Conversion/Fusion/TSpline/ConvertedSurfaceIsExact.md) gives the details.
A writer must therefore store the exact converted body.

### Grid cage conversion

`ConvertGrid` converts a qualified open grid cage exactly.
A qualified cage has valence-4 interior vertices, one whole-number knot interval on every edge, unit weights and no interior creases.
Its limit surface is one bicubic B-spline whose poles are the grips in grid order.
The knots, patch cells and progenitor windows are multiples of the knot interval.
The vertex spoke frame and the compound grips decide that order.
Fusion also records each interior knot with a third-derivative jump in the surface and curve discontinuity lists.
`SwapGridCage` puts a new cage of the same grid layout into a Form document.
The [pole order gotcha](../../../../Documentation/Gotchas/Conversion/Fusion/TSpline/GridCagePoleOrder.md) and the [discontinuity gotcha](../../../../Documentation/Gotchas/Conversion/Fusion/TSpline/ConvertedDiscontinuityLists.md) give the rules.

### Stencil cage conversion

Fusion converts each cage layout with a fixed linear map from the grips to the converted poles and points.
The layout is the topology with its root links, the grip mapping, the creases, the smart grips, the header rules and the grip count.
Single-grip probes recovered the map for eight layouts, and further moves of all grips confirmed it within 2.1e-14 cm.
Regular regions use small dyadic and triadic fractions, and vertex limit points use the Catmull–Clark limit mask.
The G1 cap weights around extraordinary vertices are not small fractions or simple quadratic surds.
They repeat between layouts with the same corner neighbourhood.
Fusion builds them by solving a sparse linear system, as the [cap gotcha](../../../../Documentation/Gotchas/Conversion/Fusion/TSpline/ExtraordinaryCapIsSolved.md) shows.
`ConvertCage` applies the packaged table of the cage layout, and `SwapFormCage` writes the result into a document of that layout.
Fusion records each interior knot in the discontinuity list of the lowest derivative order that jumps there.
The [linearity gotcha](../../../../Documentation/Gotchas/Conversion/Fusion/TSpline/ConversionIsLinear.md) and the [valence gotcha](../../../../Documentation/Gotchas/Conversion/Fusion/TSpline/CageValenceAboveFour.md) give the evidence.

| Layout | Grips | Faces, edges, vertices | Source |
| --- | --- | --- | --- |
| Box primitive and symmetric box | 26 | 6, 12, 8 | Fusion primitive |
| Creased plane | 34 | 2, 7, 6 | Fusion plane with 11 crease edges |
| Creased box | 26 | 6, 13, 9 | Fusion box with one crease edge |
| Box with 3 × 3 faces per side | 56 | 6, 12, 8 | Kit cage |
| Valence-5, valence-6, valence-7 and valence-8 prisms | 32, 38, 44 and 50 | 15, 35, 22; 18, 42, 26; 21, 49, 30; 24, 56, 34 | Kit cages |

Each TSM grip coordinate is x · w, so the table applies to the homogeneous grips.
A converted face or curve is rational only when one of its rows uses a weighted grip.
It then stores the `nurbs` cache with the form `both`, Cartesian poles and their weights.
The [weighted face gotcha](../../../../Documentation/Gotchas/Conversion/Fusion/TSpline/WeightedFaceRationality.md) gives the rule.
Kit refuses every other layout and every stencil layout with knot intervals other than 1.
Bands that join two extraordinary valences change their faces with the grips, as the [layout gotcha](../../../../Documentation/Gotchas/Conversion/Fusion/TSpline/LayoutFollowsGeometry.md) shows.

The geometry follows the map, but the crease edges do not keep one structure.
Fusion stores a crease as `tangent` while its faces meet flat and as `unknown` once they bend.
It split some bent creases into two edges, at a root of the dihedral function or at the start of a flat part.
`ClassifyEdges` measures the crease angle, splits at flat knots and labels each piece `tangent` up to 1° and `unknown` above. It refuses the two split cases that the rule does not cover.
Fusion also refuses a cage whose faces fold back, and `CheckFolds` refuses the same bodies.
The [crease edge class gotcha](../../../../Documentation/Gotchas/Conversion/Fusion/TSpline/CreaseEdgeClass.md) and the [folded cage gotcha](../../../../Documentation/Gotchas/Conversion/Fusion/TSpline/FoldedCageRefusal.md) give the evidence.

### Source-free Form documents

`EmitFormDoc` writes a complete Form document from a typed cage and a typed converted body, without a source archive.
It authors the Design progenitor tables, frame records, Form feature, SubD node, T-spline serializer, body records, timeline and naming with new identities.
`CreateFormBrep` writes the history journal and the snapshot of the converted body, and the document has no graphics segment.
A closed body needs `bodyType` 2, and the cached tool entity needs a top-entity identity, or `computeAll` drops the body.
`ConvertForm` derives the body from the cage alone.
It uses `GridBody` for an open grid and `CageBody` for a stencil layout.
`CageBody` places the stencil result in the packaged body shape of the layout, then classifies the crease edges and checks for folds.
A body shape keeps the edge and face structure, pcurves, fit tolerances, labels, progenitor windows, edge bounds and patch cells of one native carrier.
These fields stay fixed when the grips of a layout move, apart from rounding noise, labels and the crease edge class.

### Form document verification

The production round trip read 32 local Form archives.
All 32 gave an equal model after emission and byte-equal members, except for canonical `.protein` packages.
The three edited archives store graphics world kind 2, which Kit reads with the BRep level-of-detail layout.
The [edited world gotcha](../../../../Documentation/Gotchas/Conversion/Fusion/TSpline/EditedFormGraphicsWorld.md) gives the layout.
Archives saved by current Fusion can have bytes after the final ACT record.
Kit keeps those bytes as `ParsedSegment.BulkSlack`, and the [ACT slack gotcha](../../../../Documentation/Gotchas/Conversion/Fusion/Records/FusionActBulkSlack.md) gives the evidence.
[Native acceptance](../../LocalOracle/FormDocuments/Acceptance/NativeAcceptance.json), SHA-256 `b018171b82ad933a65611f5e56b54f0b48b6660bae06bc936267544f876fa552`, accepted four re-emitted controls in Fusion 2706.1.17.

| Case | Faces, edges, vertices | Area after edit (cm²) | Volume after edit (cm³) |
| --- | --- | --- | --- |
| Plane | 1, 4, 4 | 3.75882224444742 | None |
| Creased plane | 2, 7, 6 | 3.7597048123427688 | None |
| Box | 6, 12, 8 | 23.229292504382165 | 9.339333654763482 |
| Symmetric box | 6, 12, 8 | 22.896262895240067 | 9.137857029717933 |

Each re-emitted document equalled its native control within 1e-7 after open, edit, save, and reopen.
The Form health stayed 0, and zero documents remained open.
[Grid acceptance](../../LocalOracle/FormDocuments/Grid/NativeAcceptance.json), SHA-256 `ba7536f4cfed4b6cc60a50aed672d62bbcb96168571c3050527f4fd024266769`, accepted two Kit-converted plane documents in Fusion 2706.1.17.
Each document equalled Fusion's own conversion of the same cage within 1e-8 after open, edit, conversion, save and reopen.

| Case | Area as loaded (cm²) | Area after edit (cm²) |
| --- | --- | --- |
| Affine | 3.981294020792737 | 3.9230459543150173 |
| Warped | 4.005512887961321 | 3.9455217633195576 |

Three further runs in Fusion 2706.1.17 accepted documents that Kit wrote without a source archive or a native carrier.
Each run compared the Kit document with Fusion's conversion of the same TSM within 1e-8 cm after open, edit, conversion, save and reopen.

| Report | SHA-256 | Kit documents |
| --- | --- | --- |
| [Source-free bodies](../../LocalOracle/FormDocuments/Sourceless/NativeAcceptance.json) | `acc43da40fa16f28a3441f719c43cf6608b0b56081e1606495e2a986fd646ee4` | 9 cages with typed bodies |
| [Cage documents](../../LocalOracle/FormDocuments/CageDocuments/NativeAcceptance.json) | `76d2a6a35c902f6776270584b1db9363b0f6ecb9c4c2e85c3e68e26822a7ad8f` | 14 cages with `ConvertForm` bodies |
| [Stencil swaps](../../LocalOracle/FormDocuments/StencilAccept/NativeAcceptance.json) | `f7455953a99fb482fa03054aa73e165a40cbf0d683c87a8139f6dae84e25a95d` | 8 cages swapped into native documents |

The cage documents cover a warped plane grid, the box, the symmetric box, the creased box and the creased plane.
They also cover the 3 × 3 box and the valence-5, valence-6 and valence-8 prisms.
Their fresh, bent, sagged, twisted and sheared cages took no part in any fit.
Every Kit body equalled the loaded Fusion conversion in structure and edge classes, and the largest point gap was 1.2e-13 cm.

Two fourth-pass runs accepted seven more Kit documents with zero documents open afterwards.
They cover a fresh valence-7 cage, four weighted cages and two grids with knot intervals 2 and 3.
Every Kit body equalled the loaded Fusion conversion within 1.2e-13 cm, and every edited body matched exactly.

The [Form document change entry](../../../../Documentation/Changes/Fusion/TSpline/FusionFormDocuments.md) gives the complete procedure.
