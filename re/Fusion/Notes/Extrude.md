<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Extrude

[Fusion feature index](../README.md)

See [SDK Extrude readers](../../../src/convert/formats/Fusion/Extrudes) and [public Extrude tests](../../../tests/convert/api/ApiFusionExtTests.py).

## SDK coverage

For ordinary solid New Body distance Extrudes, Kit preserves an editable
`DistanceExtrude` definition. It binds the verified closed sketch profile to
the native feature's owned distance, start offset, and draft parameters. The
definition preserves signed one-sided lengths, opposing two-sided lengths, both
symmetric conventions, and the verified direction in the sketch's component
frame. The parameter records retain their formulas, and Kit evaluates the
limits from their current values. Across 712 tracked archives, Kit projected
461 definitions. Verification compared 33 saved Fusion API captures and two
assembly controls, including reversed extents, signed offsets, draft, and
the symmetric conventions. Thin and Boolean Extrudes and unresolved occurrence
directions require further decoding.

For a selected Offset construction plane in the same component, Kit preserves
an editable `PlaneExtrude` definition. It retains the selected plane, the
owned offset, and the length when the plane sets the start. The supported
plane is parallel and co-directed with the profile. Kit verifies the native
Offset plane against its origin-plane frame and scalar, then evaluates the
profile-relative start or end from the selected plane. Three saved Fusion
captures verified both roles, including offsets, and matched the reconstructed
cylinders' native topology, volume, area, and bounds. Other entity limits and
chained extents require further decoding.

For a qualified standalone cylindrical create with one full selected circle,
the FreeCAD writer links a native `Part::Extrusion` to the Sketcher profile and
drives its depth from the source dimension in the Parameters spreadsheet. The
extrusion owns the saved solid. This path requires one-sided distance, zero
taper, and no start offset. FreeCAD 1.1.3 verified literal depth edits on
four saved captures, including negative and fractional depths. The 17 mm control
rebuilt at 25 mm, with volume increasing from 5340.7075 to 7853.9816 mm³ and
center of mass moving from 8.5 to 12.5 mm along Z. The signed control rebuilt
from −17 to −25 mm in the opposite direction. Standalone Fusion length and
angle literals can remain native spreadsheet expressions when they match the
stored dimension. Formula-driven definitions with unresolved references and
the opaque source data remain in the Kit carrier.

The formula-driven path requires the depth dependency chain and owned taper
to account for every source parameter. Its drivers are editable literals.
The `expression_depth` capture keeps its independent open-line sketch and
three points alongside the driving circular sketch. FreeCAD verified that
editing the input from 9.125 to 12.5 mm changed the extrusion depth from
19.25 to 26 mm and the solid volume from 8708.4948 to 11762.1229 mm³.
Kit re-imports the edited driver and the evaluated depth while retaining the
original Fusion formula and dependency IDs. After re-export, a second edit
set the driver to −3 mm and rebuilt the solid at a signed depth of −5 mm.
Kit verifies the saved expression, both sketch geometries, and the recomputed
cylinder before accepting the edit.

When FreeCAD saves a supported depth edit, Kit checks the original sketch and
feature identities, the spreadsheet controls, the evaluated length, and the
attached cylinder. It restores the edited depth and recomputes the neutral
B-rep and body measures under the original Fusion identities. The original
Fusion archive remains available as source evidence. Four saved native edits
verified positive, negative, fractional, and sign-changing depths. A second
edit and save verified re-exporting the 25 mm result and re-importing the
30 mm result. Unrecomputed saves, changed directions, broken bindings, stale
shapes, and additional solids report a readback conflict.
Unchanged native saves keep the original neutral document even when FreeCAD
rewrites the B-rep bytes.

New circular profile bindings link the selected circle to its exact Fusion
center point in FreeCAD. The radius and center can be dragged while the
extrusion depth remains editable. Kit compares the saved sketch wire and
solid with the edited profile and signed depth, then rebuilds the neutral
geometry under the original feature and body IDs. FreeCAD 1.1.3 verified a
radius of 11.5 mm at a depth of −23 mm and center of (3.5, −6.25) mm.
The resulting cylinder measured 9555.9395 mm³ and had its centroid at
(3.5, −6.25, −11.5) mm. The formula control passed another edit after
re-export, with a radius of 8.75 mm and a signed depth of −5 mm. This path
covers the single unconstrained circular profile and its center point.

The same editable extrusion path also handles a single simple line ring
with exact native endpoint identities. The FreeCAD sketch links both ends
of each line to their Fusion point records, so a corner moves both adjacent
edges. Kit checks the saved wire, signed depth, and complete planar prism
topology before accepting the edit. Four tracked rectangle archives qualify.
In FreeCAD 1.1.3, moving one corner of the 40 × 30 mm control to (14, 8) mm
and setting a depth of −13.5 mm produced a valid concave prism of 4995 mm³.
After re-export, another edit moved that corner to (31, 24) mm and set a
depth of 12.75 mm. Kit preserved the original Fusion identities and source
archive through both saves. A separate synthetic control verified a
formula-driven signed depth on a translated XZ frame.

For verified part histories with independent active solid creators, Kit also
reconstructs the saved Extrude bodies from the profile and distance controls.
The creator's explicit result anchor must match the body in its current
component collection. Supported geometry includes cylinders, the observed
positive one-sided circular draft, and untapered line-ring prisms. The corpus
check matched 61 solids in 42 parts against their saved native body topology,
volume, area, and bounds. This includes 52 circular solids and nine prisms.
Saved suppression and rollback controls matched the active body inventory.

For qualified trimmed profiles, Kit retains each selected portion and its
native selector on the Extrude feature. It derives line fractions and arc
angles from the source intersections. Two portions can refer to the same
circle. The exact untapered sweep uses the bounded curves in the sketch's
component frame, including offset and tilted frames. Fifteen saved Fusion
captures verified 42 selected portions and 15 reconstructed solids against
native topology and saved API volumes and bounds. Profiles with holes or
general curves and trimmed draft require further coverage. The FreeCAD writer
can serialize these solids as native B-rep geometry. It verifies simple planar
rings of lines and bounded circular arcs, matching cylindrical side faces,
and coherent source shell orientations. FreeCAD 1.1.3 opened and recomputed
the 15 standalone `.FCStd` files. Each contained one valid solid with matching
topology, volume, surface area, bounds, and center of mass. The center of mass
reference uses the saved Fusion profile centroid and extrusion placement.
Fusion's editable Extrude definition and proprietary source data still require
carrier mode in a direct `.f3d` to `.FCStd` transfer.

## Saved study coverage

Saved evidence includes [`plane-extrusion-reconstruction-integration.json`](../Study/plane-extrusion-reconstruction-integration.json).

| Area      | Observed support                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    | Open work                                                                                                                                                                                                                               |
| --------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Extrusion | Join/cut/intersect/new body; one/two-sided and symmetric extents; profile/offset/entity starts; distance/to-entity/through-all ends; taper; native Circle cylinder/frustum and four-Line rectangle construction for qualified ordinary Distance controls, with complete stored-body corroboration; captured +Z Offset-plane ToEntity/FromEntity limit construction; selected Line/Circle portion construction including lenses, crescents, repeated Circle and placed profiles; observed positive sheet extrusion; NewBody distance Thin Extrude wall locations/thicknesses on one/two extent sides, with closed rectangle or open Line sources; observed one-sided Side1 distance Thin Extrude Join/Cut/Intersect with closed four-Line profiles and separate historical target/new-body/current-collection routes | Other construction profiles, selected entities/offset conventions/through-all limits and occurrence frames; other thin wall/operation/extent/profile combinations, general regeneration, full input topology and end-condition variants |

### Saved study findings

Study scripts, reports and capture paths in this section are relative to [the Study directory](../Study/README.md).

`surface-extrude-decoding.json` recovers thirteen existing sheet extrusion definitions: nine closed-circle seeds and four single open-line seeds. The native flag at byte22 is zero for these captured sheet extrusions and one for solid controls. Actual source-body `isSolid` getters corroborate all four open-line cases; the circle generators explicitly requested surface output, but did not save a completed Extrude `isSolid` getter. Twenty-six actual model-parameter comparisons check distance/taper bindings. Counted feature tables, owned profile descriptors and result anchors must agree. Four malformed guards reject unsupported flags/references. The solid-only parser keeps its existing default; the new branch requires an explicit opt-in. Main output exposes `surface_extrudes`, attaches settings/source provenance and recovers the four missing open-profile links. General extents/profiles, persistent topology and surface generation remain unresolved.

`thin-extrude-decoding.json` adds six actual Thin Extrude definitions: five closed-rectangle cases covering Side1/Center/Side2 wall placement and two independent extrusion extent sides, plus one open-Line case. A matching ordinary solid control retains its actual false flag and unchanged runtime output. The shared extrusion reader supplies the common-controls boundary without duplicating its schema. Eight wall thickness bindings are independently re-read through typed numeric parameters and reciprocal owner/value copies; location enums and thicknesses agree with actual getters. Explicit profile proxies and owned BODY anchors establish source/result provenance before six keyed result-geometry comparisons. Eight malformed guards and two legacy controls pass. The first open attempt failed on a null optional profile owner; its successful isolated retry preserves that failure. The completed open feature's actual `profile` getter returns Path, while its original selected Line and native lineage are recorded separately. `thin_extrudes`, feature `thin_extrusion` and `thin_extrusion_source` retain these bounded controls; no wall geometry or Boolean operation is regenerated.

`GenerateThinExtrudeOperationContrasts.py` produced three actual exports in `thinextrudeoperations-edb76642a509`. A fixed thin rectangular ring overlaps an owned block and extends above it. All three Join/Cut/Intersect features are healthy; Cut yields two current bodies, Join and Intersect one each. Cut/Intersect use an explicitly captured participant, while the inapplicable Join participant getter is not accessed. Native target-selection records still exist for Join, independently of that API applicability. Exact source/helper/SDK snapshots, active controls, actual participants/results, export hashes and successful owned-document cleanup are retained.

`thin-extrude-operation-decoding.json` qualifies the three one-sided, untapered, Side1 Thin Extrude Join/Cut/Intersect definitions. The existing common extrusion parser supplies operation/start/extent fields unchanged. A bounded optional body-list resolver extends the shared Thin inspector; its default NewBody behavior stays exact. Six actual wall getter checks, three extent getter checks, three byte replays and eight malformed guards pass. All six prior Thin summaries and the ordinary false-flag control remain exact. Other wall/extent/profile combinations remain unsupported, and no thin-wall Boolean geometry algorithm is implemented.

`thin-extrude-body-route-decoding.json` independently qualifies three historical target selections, one separately owned new Cut body and four current BODY-to-ASM stored-identifier associations. Sixty-eight checks and five malformed guards pass. Complete result geometry bundles agree collectively with the API; no per-body API/native or source/result pairing is inferred. In particular, Cut handle 103 maps to ASM record 3, while record 2 is an unassigned auxiliary body. Current native collection membership, historical targets and newly owned anchors remain separate facts. These proofs do not establish persistent topology, final visibility or general lifecycle replay.

`thin-extrude-operation-integration.json` compares 58 pinned saved outputs against `2d06620`, using one cached baseline/current pair. It qualifies exactly three Thin definitions and three separate body-route proofs. All 55 prior complete outputs remain exact; existing common Extrude fields, kinds, tools, other warnings, ASM geometry and placement are unchanged. The catalog reuses the three new cached outputs and preserves prior evidence: 679 archives, 403 GUIDs and 76 classes with observed semantic labels. Metadata audits find 1,104 ASM blobs and 33,979 initial custom attributes without framing/ownership/classification diagnostics. All 733 naming registries replay exactly (555 populated, 79 empty, 99 reverse-only), and the original 561-file manifest remains unchanged. These inventories describe observed files rather than complete format coverage; native writing, general regeneration and reliable CAD translation remain unfinished.

## Native ordinary Extrude geometry construction

`decode_extrusion_source_operands.py` freshly qualifies the owned profile descriptor and loop, native Sketch curves and POINT references, rigid Sketch-to-component frame, reciprocal feature/component/BODY ownership and explicit same-asset stored BODY identifier. It recovers inputs for complete single-Circle or four-Line profiles. Caller geometry annotations and ordinal BODY candidates do not supply source truth. Optional profile-to-cache COEDGE correspondence is retained separately: its absence in symmetric and two-sided examples does not erase the independently qualified native profile. Creator ownership does not establish that a stored body still has its creator's shape.

`decode_circular_extrusion_geometry.py` constructs finite cylinders and expanding frusta from those native inputs, without taking cached coordinates as operands. Signed distance determines the end displacement while the stored direction remains positive in the captured negative-distance example. Offset starts translate both ends. Symmetric FullLength uses half the stored distance on each side; HalfLength uses the full stored distance on each side. TwoSided uses independent positive and negative axial lengths. The captured positive one-sided ProfilePlane taper expands the radius by `distance*tan(taper)`, corroborated by the 7-degree and 5-degree examples. Other taper/start/sign combinations remain unsupported. The pure helper supplies complete cap Plane/Circle equations, lateral carrier coefficients, finite axial domains, exact bounds, surface areas and volume. Its radius-free station helper also supports the observed untapered native rectangle, whose constructed prism uses the existing validated prism geometry helper.

`decode_extrusion_reconstruction.py` joins the independently qualified native BODY before comparing geometry. Complete closed topology must have reciprocal partners, incident heads, exhaustive FACE/LOOP chains and closed coedge cycles. Circular results require two whole circular EDGE domains, singleton cap loops, two Plane caps and one analytic Cylinder/Cone carrier. Cap circles, axis line, radial slope and intercept are checked as complete coefficients. Rectangles require all eight POINTs, twelve straight bounded EDGEs and six cyclic planar boundaries to agree collectively. No numerical matching assigns a mathematical cap or side role to a native ENTITY, and native UV, FACE sense and current/final/history identity stay unresolved.

The fixed twenty-three-file study includes thirteen reconstructed Extrudes: twelve Circle examples and one four-Line rectangle. Fourteen other Extrudes retain explicit diagnostics: nine unsupported source/control/profile cases, three symmetric seed bodies changed by later cuts, and two assembly cases whose stored direction is in an unresolved occurrence frame. A component-local Sketch normal is not silently substituted for that stored assembly direction. Two archives contain no Extrude. The optional `extrusion_reconstruction` stream and successful receiving-feature attachment add this evidence without changing previous feature classifications, settings or warnings.

`circular-extrusion-geometry-decoding.json` checks nine analytic control configurations in two rigid frames, independent cross-section integration, exact disk-support bounds, complete carrier equations, cap normals and eighteen malformed or unsupported operand guards. `extrusion-source-operand-decoding.json` records eighteen qualified input owners, nine explicit unsupported sources, 172 focused checks, nine guards and an annotation-independence control. Source qualification alone is not counted as reconstructed geometry.

`extrusion-reconstruction-decoding.json` independently rereads raw native profile/POINT/frame coefficients and serialized ASM tokens for all thirteen reconstructed owners. Twenty-four whole circular boundaries, twenty-four Plane caps, twelve analytic side carriers and the rectangle's complete twelve-segment/six-quad boundary agree. Ten actual-byte guards cover changed cone slope/intercept, cap radius and Plane coefficients, coedge partners, EDGE heads/domains, nonfinite input and native direction/frame disagreement; two positive controls retain uninterpreted UV flags and ignore caller annotations. The report's 72 grouped checks do not represent overall format coverage.

`extrusion-reconstruction-integration.json` compares all twenty-three main-reader outputs against `b8a24f1`, using one baseline and one current acquisition. Ten cylinders, two frusta and one rectangular prism gain reconstruction evidence; fourteen unresolved Extrudes gain explicit summary diagnostics, and the two non-Extrude controls remain wholly unchanged. Removing only the new stream and thirteen successful feature attachments restores every prior complete output exactly. Independent native operand and BODY joins precede complete bounded geometry checks. Six saved numerical API bound sets and the rectangle's volume agree; API coordinates never choose native identity. The comparator makes zero additional main-reader or live API calls.

`extrusion-placement-holdout-decoding.json` separately checks two unchanged Circle Extrudes in an existing Loft capture, outside the fixed integration manifest. One native Sketch matrix translates its source by four centimetres. Raw native Circle/POINT coefficients and the explicit matrix independently reproduce both cylinders' bounds and volumes; the two saved API body bounds and volumes agree collectively. This direct-helper check makes no main-reader or live API call and assigns no API entity identity. These bounded mathematical constructions and cache corroborations do not provide native file writing, full feature-history replay or reliable CAD translation.

## Selected construction-plane Extrude limits

`decode_extrusion_plane_limits.py` qualifies the complete owned receiver/proxy/descriptor/native-leaf chain selecting a construction plane. Typed helpers, counted support lists, repeated backlinks, the explicit selection-context frame and its second native plane identity are checked separately. The native plane's creator, collection, dependency scope and origin support share the source Sketch and Extrude component. Fresh Offset-plane definition inputs independently derive its origin from the native origin plane and AlongDistance scalar; the stored plane geometry and selection-context frame must corroborate that result. UUID strings and opaque numeric trailers remain literal, without serving as identity shortcuts.

The existing source factory gains a keyword-only `allow_plane_limits=False` opt-in. Its default output remains unchanged. Successful opt-ins attach `plane_limit_provenance` while retaining the original ToEntity/FromEntity kinds, parameter bindings and raw flags. Only the observed zero-taper one-sided solid NewBody combinations qualify: ProfilePlane to a co-directed forward Offset plane with nonnegative end offset, or FromEntity with nonnegative start offset followed by positive Distance. The captured component direction is +Z; arbitrary selected faces, reversed normals, oblique planes, negative offsets and other combinations remain unsupported. Raw ToEntity side flags are not relabelled as chain or direction semantics.

`decode_plane_extrusion_geometry.py` intersects the source extrusion axis with the derived plane equation, then applies the qualified selected offset. It exposes `plane_limit_derivation` and separate `mathematical_equivalent_distance_controls` used by the established primitive builder. These mathematical operands are explicitly marked as derived, rather than substituted into native controls. The actual examples derive axial intervals `[0,3]`, `[0,3.4]` and `[3.5,5.2]` cm. The pure check also moves the stored plane origin within its plane and rotates the whole mathematical frame, so origin distance cannot accidentally stand in for line/plane intersection.

`decode_plane_extrusion_reconstruction.py` corroborates the resulting whole cylinder against the independently mapped native BODY using the existing complete topology, circular-boundary, cap-Plane and lateral-carrier proofs. The shared circular proof now compares parallel normal and axis vectors component by component, in addition to its unit/dot checks; a dot product close to one alone can hide a small tilt. No mathematical cap role is assigned to a native ENTITY. The optional `plane_extrusion_reconstruction` stream and successful feature attachment preserve the original controls, earlier diagnostics and feature classifications. Ordinary Distance/ThroughAll and other feature families do not gain outcomes in this selected-plane stream.

`extrusion-plane-limit-source-decoding.json` records three qualified input owners, 99 focused checks and eight malformed guards. It also compares all twenty-three previous source-factory outputs and failure dictionaries exactly with their committed evidence. `plane-extrusion-geometry-decoding.json` checks six analytic cylinders in two frames, including in-plane movement of the plane origin, and fifteen unsupported or malformed operand cases. `plane-extrusion-reconstruction-decoding.json` independently rereads the native selector routes, origin-plane axes, owned Offset binding and extrusion offsets before constructing each axial interval. Six complete circular boundaries, six cap Planes and three lateral carriers agree with the native-derived cylinders; all three saved API bound sets corroborate them. Eight actual-byte guards include a coherent `1e-5`-radian cap rotation whose dot error is only about `5e-11`, and a finite plane-parameter change that contradicts the stored plane frame. The eight previous ordinary reconstruction summaries remain exact.

`plane-extrusion-reconstruction-integration.json` compares eight fixed main-reader outputs against `f33f478`, using one baseline and one current pass. Only three new summaries and three successful feature attachments appear. Removing those additions restores every old complete output, including the earlier ordinary-extrusion failures and original settings/warnings. The five other controls stay wholly unchanged. They include ordinary and mixed/ThroughAll Extrudes, a Hole with a BRepFace end limit and a no-Extrude placement file; the Hole is an outside-feature control, not evidence for an Extrude B-rep target. Native selector/Sketch/anchor/BODY identities precede all numerical comparison. The three saved API bound sets agree with the independent native derivations. The comparator makes zero additional main-reader or live API calls; the previous twenty-three-file main acquisition is not rerun.

Only these three saved native Extrude plane-limit examples have been qualified; an independent native plane-limit holdout has not been captured. Mathematical rigid-frame checks do not establish additional native occurrence contexts or arbitrary selected entity types. Native writing and complete history replay remain unfinished.

## Straight extrusion of selected Line/Circle portions

`decode_trimmed_extrusion_sources.py` reuses the established strict Circle/Circle, Line/Line and mixed Line/Circle selector grammars and native intersection algorithms. The source factory's keyword-only `allow_trimmed_profiles=False` opt-in qualifies the complete underlying cutting context, native POINT references, owned full profile tuples, rigid Sketch frame and creator/BODY/component mapping. A selected portion is never substituted with its whole underlying curve. Each distinct full tuple supplies a mathematical role, including separate roles when the same Circle appears twice in the selected boundary. `mathematical_inputs` contains only native-derived primitives and angle/fraction windows; complete cached naming and earlier sampling evidence remain isolated in `profile_portion_cache_corroboration`.

The fifteen source examples cover seven Circle/Circle profiles, four Line/Line profiles and four mixed profiles, with forty-two selected portions. They include reverse creation order, unequal/shifted circles, a crescent complement, four-arc repeated-Circle boundaries, unequal/reversed rectangles and translated/XZ/angled Sketch frames. `trimmed-extrusion-source-decoding.json` retains 425 grouped checks, eight malformed guards and an annotation-independence control. All twenty-three previous default source outputs and the three previous plane-limit source proofs remain exactly equal to their committed evidence. These source checks alone do not claim a reconstructed result body.

`decode_trimmed_extrusion_geometry.py` constructs an abstract simple closed boundary from the native-derived portion endpoints after source/tuple identity is established. It checks degree-two incidence, connected closure, overlapping bounded primitives and interior crossings. Stored membership order and direction flags are not interpreted as native traversal. Green's integral gives the exact bounded Line/Arc area, including concave complements; arc lengths give perimeter and extruded side area. The rigid Sketch frame and native zero-taper axial stations then supply complete lower/upper curves, connector segments, Plane/Cylinder side carriers, mathematically oriented cap loops, volume and analytic component bounds. Arc extrema are restricted to each selected angular window. Mathematical endpoint joins never assign a native VERTEX identity.

`trimmed-extrusion-geometry-decoding.json` checks lens, repeated-source four-piece lens, crescent, mixed circular segment and rectangle constructions in two rigid frames. Independent analytic areas, perimeters, volumes and bounds agree; source membership permutation preserves the shape. Eleven malformed guards include a self-crossing loop, disconnected cycles, an open boundary, inconsistent repeated source geometry, nonfinite operands, nonrigid placement and unsupported taper. General spline/intersection profiles, holes, arbitrary selector layouts, native UV/traversal, writing and feature-history replay remain unfinished.

`decode_trimmed_extrusion_reconstruction.py` uses each complete six-literal COEDGE naming tuple to fix the two native uses of its source boundary EDGE. Reciprocal incidence then fixes the common source cap, distinct side FACEs, the other cap and each opposite EDGE before any numerical comparison. The complete stored body must exhaust its FACE/LOOP chains, coedge cycles, reciprocal partner uses, incident heads and connector routes. Native identities are established through names and topology; coordinates do not choose them.

Each fixed circular boundary must match the full source-derived Circle coefficients and its entire angular window. A mathematical sign/phase relation between the two ellipse bases, exact span and midpoint phase determine the whole bounded arc; this relation is not labelled as native UV or API traversal. Straight boundaries require complete Line locus/direction and finite endpoint domains. Plane/Cylinder side carriers, both cap Planes and the complete connector bundle must agree. The two-portion lens and mixed examples share both native endpoint VERTEXs between their boundary EDGEs; mathematical endpoint roles remain unassigned to those VERTEXs. The optional `trimmed_extrusion_reconstruction` stream and successful feature field retain the full source, construction and corroboration evidence without changing existing portion summaries or warnings.

`trimmed-extrusion-reconstruction-decoding.json` qualifies all fifteen saved owners: twenty-two Arc and twenty Line portions, 126 complete bounded EDGEs, 72 FACEs and 252 native endpoint evaluations. Independent native-source Green integrals and bounded extrema agree with all fifteen saved API body volumes and bound sets. The report retains 113 grouped checks, ten actual-byte malformed guards and two literal/caller-independence controls. Top-boundary mutations exercise the new full-window proof separately from the old source-cap sampling: changed span, shifted phase, a complementary arc with the same endpoint set, changed circular radius and a huge finite centre are rejected. Other guards cover Cylinder radius, a small coherent cap tilt, a displaced connector carrier and validly typed bad partner/head links. Four outside controls produce no trimmed reconstruction outcome.

`trimmed-extrusion-reconstruction-integration.json` compares nineteen fixed outputs against an isolated committed `d5f29a9` Python snapshot, using exactly one baseline and one current main-reader pass. Only fifteen new summaries and fifteen successful owner fields appear. Removing them restores every previous complete output exactly, including native portion proofs, ordinary and plane-limited reconstruction evidence, settings and warnings. Four whole-Circle/rectangle/plane-limit/no-Extrude controls remain wholly unchanged. Independent native source/tuple/BODY joins, 206 literal native-record checks, complete bounded topology and carrier checks precede all fifteen saved API volume/bound comparisons. No numerical API match selects a native entity. The cached comparator makes zero additional main-reader or live API calls. The report distinguishes the original isolated acquisition from retrospectively recorded reproducible baseline Python archive/module hashes.
