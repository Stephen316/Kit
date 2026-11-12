<!--
This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Construction geometry

[Fusion feature index](../README.md)

See [plane controls](../../../src/convert/formats/Fusion/ConstructionPlane/PlaneControls.py) and [binding tests](../../../tests/convert/formats/FusionProof/FusionPlaneBindingTests.py).

## SDK coverage

The selected history now also projects supported offset and angle
construction planes as neutral support frames. The reader verifies the
reciprocal feature and plane references, their shared ordinal, and the
orthonormal axes. Origins convert from centimetres to millimetres and
remain in component coordinates. The projected frames matched 144
tracked planes and 19 planes in newer Fusion captures. Seven tracked
plane records still produce diagnostics for unsupported layouts.
General support selection links remain open.

The timeline now carries typed construction-plane definitions for verified
origin offsets and angles about a component origin axis. Each definition
retains the zero-control frame, links its owned distance or angle and zero
extra-offset parameters, and independently regenerates the stored datum.
Unknown methods retain their saved support frames when available. The
coverage report verifies the qualified numeric bindings without clearing
unresolved feature and backend bytes. Existing FreeCAD plane-limited
Revolve exports keep their live construction-plane dependencies.

Standalone documents made of independent typed offset and angle planes
with literal controls export as visible FreeCAD datums in the feature
timeline. The Parameters sheet drives each plane's full placement. Kit
reconciles saved scalar edits after checking the native bindings and
recomputed frames. Dependent sketch and solid histories require their
feature-specific routes. Strict Fusion conversion still requires
complete source coverage.

## Saved study coverage

Saved evidence includes [`construction-mode-decoding.json`](../Study/construction-mode-decoding.json).

| Area                  | Observed support                                                                                                                                                                                                                                                                               | Open work                                                                                                             |
| --------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| Construction geometry | Observed plane definitions; two-plane/two-point/sketch-line/B-rep edge/face-defined axes; captured endpoint planes on an explicit spline path; three-plane, sketch-point, edge-plane, two-edge and circle-center points plus owned vertex-source point recipes, with typed supports and caches | Other axis/point definitions, exact face geometry/mapping, general ExtraOffset behavior, occurrences and regeneration |

### Saved study findings

Study scripts, reports and capture paths in this section are relative to [the Study directory](../Study/README.md).

`plane-definition-decoding.json` compares eight exports in `planedefinitions-6cd0820a832e` and decodes nine native definitions including a support offset plane. The owned backend distinguishes eight methods independently of the cached plane mode, including OffsetThroughPoint versus Offset. Ordered typed support roles resolve native axes/planes, sketch point IDs/tags and tangent-face body recipes; explicit scalar bindings and cached geometry match the API. Optional ExtraOffset changes the feature's reference offsets and is parsed rather than skipped. The main reader applies verified plane caches before resolving later selections and tools. Three malformed cases and an earlier offset fixture are checked. General ExtraOffset effects, occurrence transforms, exact tangent face mapping and parametric geometry regeneration remain unresolved.

`construction-definition-decoding.json` adds two-plane axis, three-plane point and sketch-point reference definitions for all five custom axis/point instances found in the current corpus. Typed owned descriptors establish ordered supports. Native axis/point geometry agrees with saved API geometry, and plane equations or independently decoded sketch placement check those supports. Method/role evidence comes from controlled generator calls; older captures did not read definition getters. Four malformed variants/owners/tags are rejected. Definitions are attached to their features and exposed under `construction_definitions`. Other methods, general occurrence contexts and construction regeneration remain unsupported.

`construction-mode-decoding.json` adds eight API getter captures: TwoPoints, Edge, CircularFace, NormalToFaceAtPoint and PerpendicularAtPoint axes, plus EdgePlane, TwoEdges and Center points. Thirteen typed support roles agree with the API; ten resolve exact native/sketch geometry, and three retain explicit body/face recipes without claiming exact face geometry. TwoPoints stores a non-unit direction vector, so the reader preserves it and reports a normalized direction. PerpendicularAtPoint stores a raw Point3D value on the same axis as its differently positioned native anchor; it does not retain an inferred sketch-point dependency. Four malformed cases and five earlier construction features are checked. New definitions appear under `construction_modes` and on their features; prior unresolved entries are removed only for successfully decoded IDs. The initial Point3D getter capture error remains alongside its successful retry. Other methods, exact face geometry, general occurrence contexts and regeneration remain unsupported. This stage brought the class catalog to 344 archives and 338 classes.

`construction-vertex-point-decoding.json` reuses the actual vertex-referenced point capture to decode that ConstructionPoint independently of Loft. `decode_construction_vertex_points.py` runs after other construction-definition passes and attaches only unresolved feature variant 0 / backend method 10 vertex-source candidates. Reciprocal native point/feature ownership, typed owned descriptors and bounded `vertex_recipe_data` establish the source definition; cached coordinates separately agree with API point/source-vertex getters. The main reader exposes `construction_vertex_points`, clears old mode/definition rejections only for successful IDs and retains explicit source-topology uncertainty. One API-backed definition, four malformed-reference guards and two earlier ThreePlanes sources pass. Persistent ASM vertex/body identity, source-geometry evaluation and other context/layout variants remain unresolved. The catalog now indexes 423 reference archives and 340 native class GUIDs.
