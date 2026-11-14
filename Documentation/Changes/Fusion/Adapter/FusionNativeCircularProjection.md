# Reference-driven native circular projection

Strict public Fusion reading now projects qualified native full-circle sketches, cylindrical extrusions and positive-radius circular frustum extrusions. It follows actual sketch, parameter, feature, material and BRep references. Native entity numbers and a regenerated authoring template do not determine eligibility.

## Usage and scope

Use `open_document("NativeCircle.f3d")` with the default strict mode. The returned `CadDocument` contains the actual circle, center and origin points, user parameters, feature identities and names. Extruded profiles also contain their actual height and taper parameter references, analytic solid topology and effective material density/color. The complete decoded native model remains in the version-2 semantic state contract.

Neutral JSON serialization followed by `write_document(..., allow_carrier=False)` reconstructs the native archive from that typed state. The writer requires the complete neutral projection to agree before destination mutation. Editing only a neutral radius, parameter or material does not silently change the retained native graph; it is rejected. Source-free changes remain available through `MakeFusionDoc` and a new `DocumentSpec`.

The native route requires one identity-placed root component, one unconstrained full circle on XY, and either no modeled solid or one additive positive-Z distance extrusion. Bottom and top radii must be positive. Taper is native radians and satisfies `top_radius = bottom_radius + height * tan(taper)`. Zero taper selects cylindrical history; nonzero taper selects the explicit conical model. It rejects arcs, additional sketch curves, populated constraints/dimensions, unsupported features, thin/two-sided/subtractive extrusions, external components, general journals and nonempty meshes.

The existing constructor-shaped version-1 route, native rectangular route and explicit `strict=False` partial reader retain their contracts.

## Semantic checks

The timeline must account for every feature entity. The [legacy Features field](../../../Gotchas/Conversion/Fusion/Api/FusionLegacyFeatureState.md) is checked separately and is not treated as its cursor. The parameter table is projected completely, with actual user and model names, expressions, units and owners. The curve, center point, point-use collections, parent sketch and circle carrier must agree. A sketch-only forward operation map may have an absent reverse cache; if a reverse entry exists, its feature and operation must agree.

Extruded profiles validate profile scopes, region recipes, curve/body progenitors, UUID joins, body keys, operation IDs, secondary IDs and history boundaries. The side/top/bottom face and edge tags must match those Design identities. Cached volume, area, center and all inertia components are checked independently against analytic circular geometry. Geometric comparisons retain the existing tight tolerance; the native numeric mass cache uses a separate bounded tolerance described in the [precision gotcha](../../../Gotchas/Conversion/Fusion/Api/FusionCircularMassPrecision.md).

Circular-only snapshots contain one open planar sheet. Extruded snapshots contain the solid and two planar profile/sketch sheets. The checker follows body, lump, shell, face, loop and edge references; it checks every carrier, rim, endpoint and topology attribute. The kernel's full-circle seam can use −π/+π and the negative-X vertex, independently of the sketch carrier's 0/2π interval. The [snapshot seam note](../../../Gotchas/Conversion/Fusion/Api/FusionCircleSnapshotSeams.md) records this distinction.

Graphics retain their complete decoded semantic state and entity references. Unsupported graphics still fail; they are not stripped to admit a document. The static allowlist now contains 140 record/enum types, including the typed mixed-snapshot geometry closure. General journal histories and mesh models remain outside the adapter contract. Native archive bytes, opaque segment payloads, dynamic imports and pickle are not state encodings.

## Evidence

The three native-saved controls are the circle, extrusion and frustum outputs from [earlier public native acceptance](../../../../re/Fusion/LocalOracle/PublicAdapter/NativeAcceptance.json). Their actual persisted dimensions are radius 14 mm for the sketch, and radius 12 mm and height 21 mm for the cylinder. For the frustum, the actual persisted dimensions are bottom radius 12 mm, height 21 mm and taper −3 degrees. These are post-edit vendor saves, not constructor-shaped inputs.

The [research model](../../../../re/Fusion/Reconstruction/PublicRotational/ProjectionModel.md) records source hashes, snapshot inventories and semantic qualification. The [public preparation script](../../../../re/Fusion/Reconstruction/PublicRotational/GeneratePublic.py) exercises public discovery, neutral JSON and native emission for parent-controlled Fusion acceptance. The [public preparation report](../../../../re/Fusion/LocalOracle/NativeRotationalPublic/Preparation.json) records byte-identical outputs to the independently prepared lower-codec files:

| Profile | Public output SHA-256 |
| --- | --- |
| Circle | `1b2a7c2d57ca750030c75514ccb977c0cf8bb9dcfea7c0018de08716ef161610` |
| Cylinder | `29b666aa7afc20267e273bbd4d29f98143d3c2157af3ca2e353785724f2e4176` |
| Frustum | `fa018c7ec54ae00ebbb0da84312eafb5915a3ce3ed90e57149cf78c8caa39e81` |

[Native Fusion acceptance](../../../../re/Fusion/LocalOracle/RotationalDocuments/NativeAcceptance.json), report SHA-256 `5950746b0d3601bcf3cb7bf798288aa5a894e2d410e875018ab67f0d95a62d1f`, passed all three source/re-emission pairs. Fusion verified initial geometry, rollback/rebuild, height 21→26 mm, circle radius 14→16 mm and frustum taper −3→4 degrees, followed by native save/reopen. Zero documents remained open. The actual solid material density is 2870 kg/m³ with RGBA 0.2/0.4/0.6/1. No separate native run is claimed for identical public output bytes.

Twelve new remote integration cases cover complete native and neutral round trips, real parameter/material/geometry projection, and snapshot/tag/body-identity corruption at the public archive boundary. The cases also cover destination preservation after inconsistent writes and the two narrowly defaulted historical `SketchWorld` link collections. Local tests were not run. Black, Ruff, mypy, strict Pyright and repository steering checks passed. Remote CI remains separate evidence.

See the [public Fusion adapter guide](FusionPublicAdapter.md) and [native rectangle route](FusionNativeRectangleProjection.md).
