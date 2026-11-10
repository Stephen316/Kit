<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Revolve

[Fusion feature index](../README.md)

See [SDK Revolve readers](../../../src/convert/formats/Fusion/Revolves) and [Revolve tests](../../../tests/convert/formats/FusionRevolveTests.py).

## SDK coverage

Revolve steps also retain the native operation, sidedness, projected-axis
flag, and owned angular parameter bindings. Entity-limited steps mark the
stored angle inactive and preserve target order. An owned construction-axis
selection retains its native identity, and each resolved construction-plane
target links to its support frame and feature dependency. The SDK matched
the controls for all 26 tracked Revolves and 13 newer captures, including
23 plane target links. Plane targets and sketch-line axes also appear as
Kit selections with native provenance and earlier feature dependencies.
The sketch-line contrasts preserve opposite endpoint orders. The shared
sketch selection reader matched 102 owned selections across ten native
feature classes in the tracked corpus. Construction axes retain native
identity. The two B-rep edge Revolves retain the native recipe, body anchor,
earlier source feature, and directed line cache. Both stored endpoints match
the captured Fusion axes. The shared recipe reader matched 1,763 tracked
records across five recipe kinds. Exact edge identity in Kit topology
remains open.

For solid New Body Revolves with a verified four-line profile, a component
origin axis, and one or two construction planes through that axis, Kit now
projects a typed `PlaneRevolve` definition. It preserves the ordered plane
selections and stores the evaluated start and end angles about the effective
axis. The two-plane sweep can start away from the sketch plane. All 16
tracked and newer captures passed Kit JSON round-trips and matched 64
independently evaluated body arcs.

Kit recovers the authored Rotate Angle and support selections for the
construction planes used by these Revolves. The FreeCAD writer binds those
angles to native plane placements and computes each `Part::Revolution`
sweep from the live plane normals. A two-plane sweep also updates the
solid's angular placement. FreeCAD 1.1.3 opened all 16 transfers and
rebuilt them after edits to the source angles. Use a quantity expression
such as `=-48 deg` to enter a signed angle in the Parameters sheet.
Coincident planes and planes that miss the axis produce an invalid feature.
Kit reads back saved angle and line-profile edits, rebuilds the selected
planes and sweep, and verifies the saved sketch and solid before accepting
the changes. A stale pose or shape produces an explicit read error.

For verified histories with independent active New Body Revolves, Kit
also generates closed analytic B-reps directly from the profile and sweep.
The native creator anchors and reciprocal component collection identify
the result bodies. Kit assigns its own face and edge IDs. All 16
plane-limited captures matched the saved Fusion body topology and analytic
geometry, including volume, area, and bounds.

For unprojected solid New Body Revolves with an origin or sketch-line axis,
Kit also projects an `AngularRevolve` definition from a qualified convex
line profile, whole circle, or full-turn semicircle with its diameter on
the axis. The definition links the owned along and against parameters
and preserves one-sided, two-sided, and symmetric limits. The effective axis
follows the occupied side of the sketch.
Eligible partial polygon sweeps use the same analytic solid builder as
plane-limited sweeps. The SDK verified 15 typed definitions and eight partial
solids across 23 tracked angular features.

Kit transfers a qualified standalone angular New Body Revolve with a line
profile about a component origin axis to a native FreeCAD `Part::Revolution`
linked to its sketch. The Parameters sheet drives signed one-sided, full-turn, symmetric,
and two-sided sweeps. The symmetric limit has one editable half-angle. The
two-sided limits each drive the sweep and its angular placement. FreeCAD
1.1.3 independently verified seven tracked transfers and rebuilt the solids
after parameter changes. A tracked line-profile sketch also rebuilt its solid
after a corner edit. Kit reads saved angle and line-profile edits back into
the original timeline. It verifies the saved sketch and solid against the
live controls before accepting the edit, and it can re-export the rebuilt
shape, including conical sides from a corner edit.

Qualified one-sided Revolves about a line in a separate Fusion sketch
also export as native FreeCAD Revolves. A hidden guide edge follows the
original construction line and drives the native axis link. Both saved
endpoint orders rebuilt in FreeCAD 1.1.3 after angle, axis, and profile
changes. The live sweep keeps the Fusion angle direction when the
endpoints reverse or the axis moves to the opposite side of the profile.
Kit reads saved angle, axis, and line-profile changes back into the original
timeline, preserving the construction line, separate endpoint identities, and
profile point joins. Edge contact also reads back as a solid when one complete
profile edge touches the axis. The saved sketch wires, signed angle, and solid
must agree with the edited controls. Files with pending or invalid rebuilds
are rejected. Kit can re-export the edited timeline as a live FreeCAD Revolve.

Kit also reads a qualified straight B-rep edge as the axis of an angular
Revolve after a positive, untapered line-profile Extrude. The saved recipe
names the two incident faces and the three faces at each endpoint.
Kit resolves those names in the explicitly mapped ASM history member and
uses the original sketch tags to identify the same edge in the rebuilt
Extrude. The saved line context independently checks the ordered endpoints.
Both tracked captures retain the original Extrude and Revolve, the typed
edge selection, and two rebuilt solids. Qualified linked histories also
export as live FreeCAD Extrude and Revolve features. The generated prism
cache uses the same edge order as FreeCAD's rebuild, so the native axis link
selects the right edge on first open. Both solids rebuild after changes to
the signed depth, angle, either sketch, or a supported rigid placement. Kit
reads those changes back and verifies both saved solids against the sketches,
linked edge, and edited controls. It rejects pending rebuilds, invalid edits,
and mismatched caches. The recovered timeline can be exported again as a live
FreeCAD Extrude and Revolve.

Full-turn polygons, ring tori, and spheres use periodic topology. The
tracked annular solid, cone, torus, and sphere matched their saved body
counts and analytic geometry. The cone retains its degenerate apex edge,
and the torus and sphere each have one untrimmed face. Kit projects all
three solids in the analytic multi-body fixture. Partial profiles that touch
the axis at one point, custom axes and other B-rep axis sources, surface and
Boolean Revolves, projected axes, and native Fusion output require more coverage.

## Plane-limited Revolve

The three `Study/revolveto-b1d196f65c46/` captures resolve the selected
construction planes and the component +Y axis. The selected sketch rectangle
is in XY, with X in [1, 3] cm and Y in [1, 4] cm. All three store zero in the
inactive `AlongAngle` binding. The saved API ground truth covers the inputs.

The table records the observed sweep in each mapped history BODY. Angles use
right-handed rotation about +Y with zero along +X. Unwrap the angles through
the measured midpoint.

| Capture              | Revolve → native BODY → ASM BODY index | ASM circular EDGE indices | Start / midpoint / end | Span |
| -------------------- | -------------------------------------- | ------------------------- | ---------------------- | ---- |
| `negative_plane.f3d` | 272 → 323 → 2                          | 43, 45, 59, 77            | 0° / −17.5° / −35°     | 35°  |
| `positive_plane.f3d` | 272 → 323 → 2                          | 43, 45, 60, 78            | 0° / −67.5° / −135°    | 135° |
| `two_planes.f3d`     | 301 → 363 → 3                          | 51, 53, 68, 86            | −135° / −175° / −215°  | 80°  |

To reproduce, use `decode_basics` for `body_selections.body_anchors` and
`body_asm_identifiers`. Parse the mapping's `history_blob_member` with
`inspect_asm` and select the mapped BODY graph with `decode_topology`. For
each circular EDGE in that graph, evaluate its ellipse carrier at the two
stored EDGE parameters and their midpoint. Subtract the carrier center and
compute `atan2(-z, x)` for each resulting radial vector. The four edges in
each BODY agree. Detached auxiliary roots also contain full circles, so an
archive-wide EDGE scan includes unrelated 360° spans.

The 45° target plane has two radial branches. The single-plane capture uses
the branch at −135°, and the two-plane capture sweeps across −180° with the
source profile at 0° outside the resulting sector. A shortest-angle rule or
an assumption that a two-sided sweep contains the sketch would fail these
controls.

In the sketch-normal-directed frame (axis −Y, radial +X, tangent +Z), each
target plane has two radial intersections separated by 180°. A one-plane
Revolve runs from the sketch to the first forward intersection. A two-plane
Revolve starts at the later of the first forward intersections and ends at
the opposite branch of the earlier one. This makes the two-plane interval
independent of target order. The decoder derives this interval from the
source sketch, axis and plane records, then requires the complete analytic
FACE/LOOP/EDGE bundle to agree with the independently mapped BODY.

A Fusion 2706.1.17 oracle run varied target angles, target order, and the
optional one-sided direction hint. All four body-owned circular edges in each
of 13 captures agreed with the source prediction. The angle convention below
is sketch-normal-directed. Autodesk exposes the direction hint in the API.
The observed hint invariance applies to these controlled through-axis planes.
[Autodesk Revolve input reference](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/fusion_RevolveFeatureInput_setOneSideToExtent.htm)

| Requested plane angle(s) | Contrast              | Observed sector |
| ------------------------ | --------------------- | --------------- |
| +45°                     | omitted, +Z, −Z hints | 0°–135°         |
| −35°                     | omitted and −Z hints  | 0°–35°          |
| +45°, −35°               | both target orders    | 135°–215°       |
| +20°, +45°               | two positive angles   | 160°–315°       |
| −35°, −70°               | two negative angles   | 70°–215°        |
| +15°, −65°               | mixed angles          | 165°–245°       |
| +80°, −20°               | mixed angles          | 100°–200°       |
| +15°                     | omitted hint          | 0°–165°         |
| −65°                     | omitted hint          | 0°–65°          |

All 13 Fusion 2706.1.17 controls now decode through the full Revolve
reconstruction path. Their bound numeric parameters use eleven zero bytes
between the expression and role, compared with ten metadata bytes in the
older layout. The reader preserves the extra byte and the original source
offsets. Across the 13 captures, all 51 decoded parameter names, roles and
numeric values matched the Fusion API, and each source-derived Revolve
matched its bounded body. The coverage report now verifies all 51 numeric
records and their reciprocal feature bindings. The tracked 2705.1.30
fixtures still exercise the legacy layout.

From `Study/`, enable this experimental path with:

```sh
python3 decode_basics.py --plane-limited-revolves revolveto-b1d196f65c46/two_planes.f3d
```

The Python entry point accepts `AllowPlaneLimits=True`. The opt-in preserves
the existing angular-only default. Plane reconstruction requires an
unprojected solid NewBody, a four-Line sketch profile, a native origin axis,
and owned construction-plane targets through that axis. The output retains
the original inactive angle and separately identifies the source-derived
interval and its bounded BODY verification.

Reproduce the three Revolve checks and the focused Shell and Extrude checks
from `Study/` with `python3 -m Verification.FocusedRevolves`. Pass
`--zstd-library` if needed for the saved archives. From `Study/`, run
`PYTHONPATH=../../../src python3 -m Verification.FocusedRevolves --kit` to
also check Kit JSON, projected intervals, body topology counts, and
measurements against the tracked geometry.

The integration audit passed the functional checks on all 712 archives with
default settings. With plane-limited Revolves enabled, the three captures
above gained reconstructions. After removing those three additions and
restoring their prior unresolved rows, all 712 serialized outputs matched the
baseline hashes. The historical comment-style findings remain separate from
the functional result. The original freeze validators pin the import-era
source hashes and must be run against their historical source snapshot.

## Saved study coverage

Saved evidence includes [`revolve-reconstruction-integration.json`](../Study/revolve-reconstruction-integration.json).

| Area    | Observed support                                                                                                                                                                                                                                                                                                                                                                                                                                      | Open work                                                                                                                                                            |
| ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Revolve | Observed join/cut/intersect/new body, signed one-sided/symmetric/two-sided angles, one/two construction-plane entity extents, solid/surface and projected-axis flags; native/custom construction axes, directed sketch-line axes and typed cached B-rep source axis lines; native-profile angular rectangle construction and full sphere/torus/cone construction, with qualified source-relative orientation and complete bounded cache corroboration | Other target entities, entity-limit direction hints, projected selected axes, other context frames, Boolean/general profile regeneration and persistent edge mapping |

### Saved study findings

Study scripts, reports and capture paths in this section are relative to [the Study directory](../Study/README.md).

`revolve-mode-decoding.json` checks ten angular revolve examples against API values. Symmetric extents store equal along/against angle bindings; asymmetric two-sided extents store different angles. These are reported separately rather than silently treating one as the complete sweep. Full-turn classification currently applies only to observed one-sided extents. Axis selection follows the decoded variable-length reference fields, including records with optional attribute headers.

`revolve-to-decoding.json` checks one/two-sided construction-plane extents against three API input definitions. Target planes resolve through explicit selection chains. An inactive `AlongAngle` parameter remains cached data and is not reported as an active angle. Direction hints, the resulting sweep angle and general B-rep-face targets remain unresolved.

`revolve-axis-decoding.json` adds one completed custom two-point construction-axis holdout in `revolveaxes-36bd04ac77e1`. Its explicit selection chain, axis name/origin/direction and angular/operation/solid/project settings match eight API comparisons through the existing reader. The initial four-case capture produced no files because an unsupported feature-level parameter getter was used; it was corrected to component `modelParameters`. On retry, the first export completed, then Fusion entered a native signal/crash handler while creating the next document. The process remained live inside its crash handler at the stack observation; it later exited without a completion marker, and Fusion was relaunched in the background. The report preserves the successful sample's complete getter evidence; At that capture stage sketch-line/reversed-line/B-rep edge cases remained uncaptured; the selected-axis stage below adds completed captures and decoding. The generator now journals document-creation progress and supports selecting remaining cases. The relaunch was requested only after the old process exited; no overlapping capture was dispatched.

`revolve-selected-axis-decoding.json` adds four successful exports across `revolveaxes-a83b542c4a07` and `revolveaxes-14700158dba9`: directed/reversed SketchLine inputs and Y-directed/offset X-directed B-rep edge axes. Forty-two API comparisons and three malformed guards pass. Sketch sources resolve through owned proxies, descriptors, explicit sketch IDs/tags and rigid source placement. B-rep descriptors instead reference typed `50AEE8B4` contexts: a 55-byte record carries a source point and non-unit direction vector, independently matched by both edge contrasts. The main reader attaches normalized source directions, preserves raw cached vectors, and reports the linked edge recipe and historical body anchor. Persistent recipe-to-ASM edge identity and effective feature rotation are separate unresolved questions. Projected selected-axis transforms reject; occurrence frames, other cached context layouts and solid regeneration remain unverified. `validate_revolve_axis_modes.py` reproduces focused checks.

`brep-edge-axis-decoding.json` makes the captured B-rep edge axis a decoded construction feature, in addition to its prior Silhouette input role. Variant4/method8 has an owned typed edge recipe and a separate native line cache. Its finite raw vector is normalized to the actual API unit direction while the original vector remains explicit; preview values never supply the axis geometry or a trimmed edge length. Reciprocal native geometry/feature links, repeated axis-collection membership and the typed component owner agree. Eight actual API comparisons, five malformed guards, a cache-separation control and two prior no-op controls pass. Main output exposes `brep_edge_axes`, removes only its former construction failures and preserves the richer Silhouette source provenance. Other axis variants/collection counts, exact source-edge geometry and regeneration remain unresolved.

## Native angular Revolve construction

`decode_revolve_source_operands.py` freshly qualifies the owned whole-profile descriptor, native Line/Circle/Arc records and POINT references, rigid Sketch frame, creator-owned BODY, same-asset stored identifier and reciprocal component ownership. Origin axes retain their native container route; custom TwoPoints axes are independently derived from their typed defining POINTs. SketchLine axes retain original endpoint direction and frame. Selected B-rep axes reuse the existing complete recipe/name/incidence proof to fix a native source EDGE before its Line coefficients, finite domain and explicit axis-context endpoints are corroborated. These source records do not establish current or historical material state.

The native selected-axis direction and original signed angle controls remain unchanged. In the captured partial cases, direct right-hand rotation about that stored direction is insufficient: positive Y-axis and X-axis cases differ, and reversing a selected SketchLine leaves the actual material unchanged. `decode_revolve_geometry.py` instead derives the effective axis solely from the occupied source radial half-plane and Sketch normal, so `effective_axis × radial = Sketch_normal`. It never chooses a sign from result coordinates. This observed source-relative convention is qualified for the captured coplanar, unprojected, one-side-of-axis profiles; it is not a universal direction rule for arbitrary selected or projected axes. Symmetric stored angles of 65 degrees describe ±65 degrees, while positive Along/Against values of 60/25 degrees describe `[-25,60]` about the effective axis.

Three/four-Line sections use their source meridian area and radial first moment to derive volume, with complete Plane/Cylinder/Cone sweep carriers, finite circular/straight boundaries and angular cap loops. Component bounds use bounded angular extrema of the source vertices. Full Circle and semicircle/diameter inputs derive the captured ring torus and sphere; the full triangle derives a cone and disk cap. Five custom/selected-axis profiles retain eight distinct native POINT IDs at four coincident mathematical corners. Source-only mathematical endpoint joins close their sections without merging or assigning those native POINT identities.

`decode_revolve_reconstruction.py` qualifies the complete stored BODY topology before comparing nested FACE→LOOP→curve geometric bundles. Full periodic circles keep their actual seam vertices separate from model corner roles. Sphere and torus retain one FACE and no loops, edges or vertices. The cone retains its actual null-curve apex EDGE, singleton unpartnered coedge and degenerate loop; complete cone coefficients and the zero-radius apex condition qualify that singularity. Complete circular carrier/span/midpoint-phase signatures reject complementary arc windows despite equal endpoint sets. Geometric bundle correspondence assigns no mathematical face or corner role to a native ENTITY, and native UV, FACE sense and API traversal stay unresolved.

`revolve-source-operand-decoding.json` qualifies the fifteen requested owners plus three legitimate NewBody seed inputs in Boolean captures, with 511 grouped checks, eight malformed guards and an annotation-independence control. Eight receiving Boolean/surface/projected/entity-limit features remain unsupported. `revolve-geometry-decoding.json` independently checks ten analytic solids, source-axis reversal, negative full turns and rigid-frame placement, with sixteen malformed/unsupported operand guards. The new optional `revolve_reconstruction` stream and successful feature field preserve prior controls and diagnostics. Reliable native writing and general feature-history regeneration remain unfinished.

`revolve-reconstruction-decoding.json` qualifies twelve rectangle solids across origin, custom, SketchLine/reversed-SketchLine and B-rep edge axes, plus the three full analytic solids. Complete geometry covers 74 FACEs, 138 EDGEs, 94 VERTEXs and 274 finite endpoint evaluations, with the cone's additional null-curve apex handled separately. Eleven explicit failures include the eight unsupported receivers and three seed bodies whose stored caches were modified by later Boolean operations. Two unrelated controls have no Revolve. The 106 grouped checks include ten actual-byte guards for complementary arc windows, whole Cylinder/Plane/Line coefficients, Sphere/Torus radii, cone radial slope/apex consistency, singular apex partner rules and typed bad heads/partners. Full-circle seam reparameterization is retained as a geometric invariance, without assigning a model seam vertex.

Saved numerical API evidence corroborates the sphere, torus and cone carrier coefficients and topology counts, plus the cone's two vertex positions. The twelve rectangle captures provide saved API axis and angle controls but no public API result bounds, volumes or vertex sets. Their complete constructed geometry is corroborated against the independently identified native body; it is not described as a captured API shape comparison.

`revolve-reconstruction-integration.json` compares twenty-three fixed files against an isolated committed `676607d` Python snapshot, with one baseline and one current main-reader acquisition. Only twenty-one new summaries and fifteen successful owner fields appear; removing these additions restores every prior complete output exactly, including the two whole-file controls. Independent source qualification, 349 literal native-record checks and complete bounded topology precede geometry comparisons. The report retains thirty-five saved API axis/angle checks and three analytic body bundles, while explicitly recording that API result bounds and volumes were not captured. The cached comparator makes zero additional main-reader or live API calls.
