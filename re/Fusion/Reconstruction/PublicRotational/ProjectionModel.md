# Native circular public projection

The public version-2 route projects semantic Design references for one unconstrained full-circle sketch, optionally followed by one ordinary solid distance extrusion. Source entity numbering is not eligibility evidence. The implementation follows actual references and retains the complete decoded model rather than comparing the records with an authored template.

## Controlled inputs

| Role | Input | SHA-256 | Persisted geometry |
| --- | --- | --- | --- |
| Circle | `re/Fusion/LocalOracle/PublicAdapter/vendor_circleEdited.f3d` | `699c12b242a416a6ae761b6186759246df9b09a5b6501cd58c04dc4a340db14e` | Full circle, radius 14 mm, one unused `publicHeight` user parameter at 21 mm |
| Cylinder | `re/Fusion/LocalOracle/PublicAdapter/vendor_extrusionEdited.f3d` | `33e7b098ddb6677b3bd9816b3c6133ccc850aea9d5d58fcd65b445c796ecc3a5` | Radius 12 mm, height 21 mm, taper zero |
| Frustum | `re/Fusion/LocalOracle/PublicAdapter/vendor_frustumEdited.f3d` | `bc85b3edc96328a0c906cd413f7dac75e83b1e35104d8c21a2d711b5bfb473b2` | Bottom radius 12 mm, height 21 mm, taper −3 degrees, top radius 10.899436635056134 mm |

These are vendor saves from the six-profile public acceptance study. Their existing IDs include circle entity 1096, sketch 1089, sketch feature 1097, extrusion 1112 and body 1125. The tests preserve those IDs; the projector has no constants for them.

## Design joins

The root component points to its design fragment. The creation-order controller enumerates the complete timeline, which must equal the complete set of feature-derived graph entities. The sketch-only route has one `DcSketch`; the solid route additionally has one `DcExtrudeFeature`. `MSketch.rDcNode`, `DcSketch.rSketch`, parent sketch links and the point `CurveUses` incidence are reciprocal.

`CircArc3D.arcCurve` has XY center, positive radius, +Z normal, +X reference vector and angular interval 0..2π. Its center point is a distinct non-origin point, although its coordinates may coincide with the origin. There are no start/end points. The circle is unconstrained and unfixed; the origin alone is fixed. The active sketch has no dimensions, constraints, offsets or projected dependencies.

The parameter table is projected completely. The solid's distance and taper bindings are active, reciprocal and owned by the extrusion. The distance is positive centimetres in native storage; the public graph uses millimetres. Taper is native/public radians. Named direct user-parameter references preserve their dependencies and literal expressions retain their values and units.

`profileDataRefs` resolves through `ModelDataRef`, `SketchRegionRef` and `SketchRegionRecipe` to one positive circular loop. Its sketch tag has primary identity from the circle metadata, secondary zero, direction zero, split ordinal/total 1/1 and role flags zero. The side progenitor's curve recipe uses the same tag with direction one and empty adjacent-primary-tag sets.

The extrusion progenitor table contains one side-curve and one body progenitor. The history body's secondary ID equals the body's table value; its operation resolves to the extrusion in both operation maps. The body UUID matches Design and `DcBody`. The body progenitor's face occurrence contains the side face's ASCII primary identity and its derived byte offsets. The circular snapshot/history tag model preserves the side face, top/bottom faces, top/bottom edges and sketch identity.

The sketch-only save has a populated `featureIdMap` but an empty `enetityIdMap` reverse cache. The route admits this explicit absence, and checks exact reciprocity if a reverse entry is present. It does not invent an entry or change emitted state.

The empty legacy `Features` container stores `m_curFeatureId = 1` in all three controls. This value is not the zero-based timeline cursor: the circle has one timeline entry and the solids have two. The qualified route retains this observed legacy state while deriving timeline completeness from actual feature references and states.

## Snapshot topology

The durable inventory is [SnapshotInventory.json](SnapshotInventory.json). Source storage uses ASM binary 23200, centimetre geometric coordinates and root counts including `asmheader`.

Circle-only: 14 records, two roots including the header. One body/lump/shell/face/loop/coedge/edge/vertex/ellipse/point plus a planar carrier and two sketch attributes. The coedge is a valid open-sheet boundary with no partner. Its direction attribute is zero; the edge sketch direction is one.

Cylinder and frustum: 59 records, four roots including the header. Three bodies represent the solid, profile sheet and sketch sheet. The solid has three faces, two circular edges, two seam vertices, two caps and one cylindrical/conical side carrier. The profile is double-sided with contained=false; the sketch sheet is single-sided. The snapshot has five generic topology tags and six sketch tags. Bottom-rim coedges retain sketch direction zero on both the side and bottom face; sheet edges use direction one. The top rim carries the top-edge generic tag and no sketch tag.

The full-circle edge interval is −π..+π. The corresponding vertex is at the negative-X seam, with small floating-point Y residuals. The top solid ellipse normal is −Z; bottom and sheet ellipses use +Z. The side face's coedges are forward, the cap coedges reversed. Cap surface normals are +Z, with the bottom face reversed. Every edge endpoint is evaluated from its actual parameter and carrier. Native endpoint indices and parameterization remain unchanged in typed state.

The generic `GeometryState` snapshot route preserves all known entity fields. The public projector independently checks the exact supported inventory, body decomposition, carriers, sheet/solid orientation, rims, seam coordinates and attribute ownership. Unsupported geometry or attributes fail rather than being carried as an opaque block.

## Numerical cache evidence

The cylinder cache stores volume 9.500176184455942 cm³ and area 24.88141381643116 cm². Its center X is 1.2548138984028572e−10 cm. Transverse inertias 17.385321755015763 and 17.38532263840058 differ by about 8.83e−7. The source-reported inertia/volume integration precision is approximately 0.00048340252544976824.

The frustum cache stores volume 8.655517248010467 cm³ and area 23.384314014759717 cm². Center Z is 1.016383380368247 cm. Its transverse inertias 14.962207958674432 and 14.962208559905179 show the same numerical asymmetry.

The public circular checker uses independent analytic volume, area, centroid and full global inertia tensors, including parallel-axis terms. Cache comparison is bounded to relative 1e−6 and absolute 1e−8. Geometric comparisons retain relative 1e−10 and absolute 1e−9. Cache values are preserved, not normalized. Prism checks retain their earlier tolerance.

## Boundary and verification

The strict public graph contains real neutral geometry, actual source identities, parameters, feature definitions and typed materials. Its version-2 state preserves full Design/ACT/Browser schemas and values, typed history/snapshot/material/configuration/graphics content, and manifests. There is no source archive, payload/template copy, runtime CAD call or dynamic input-directed import in this path.

`GeneratePublic.py` prepares public API → neutral JSON → F3D outputs for serialized native acceptance by the parent agent. Huge neutral JSON and raw exploratory field dumps remain local-only. New remote tests execute at archive/public serialization boundaries; no local tests are used.

General multi-state history, arbitrary arcs/constraints, transformations, extra features, nonempty meshes and unsupported graphics remain explicit rejections. Existing source-free constructor authoring and legacy partial reading retain their distinct contracts.

## Public/native acceptance

The public route prepared all three archives through actual `open_document`, neutral JSON serialization and `write_document(..., allow_carrier=False)`. The [preparation report](../../LocalOracle/NativeRotationalPublic/Preparation.json) records exact source/output/neutral hashes, real parameter IDs and material values. Public outputs exactly match the lower-codec candidates in [RotationalDocuments/Preparation.json](../../LocalOracle/RotationalDocuments/Preparation.json).

[Native acceptance](../../LocalOracle/RotationalDocuments/NativeAcceptance.json), report SHA-256 `5950746b0d3601bcf3cb7bf798288aa5a894e2d410e875018ab67f0d95a62d1f`, passed source/re-emission comparison, rollback/rebuild, height 21→26 mm, circle radius 14→16 mm, frustum taper −3→4 degrees and save/reopen, with zero remaining documents. These accepted bytes therefore cover the public outputs without claiming another native run.

The final semantic-state registry contains 140 explicit record/enum types, including three new graphics records (`PrimitiveLod`, `RenderMesh`, `CircleArcValue`). It deliberately excludes general `JournalModel`, mesh models and sphere/torus geometry. The two newly optional SketchWorld link collections receive only their historical empty defaults when absent.
