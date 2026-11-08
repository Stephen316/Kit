<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Fusion native-file research

`Study/` contains the imported experimental Fusion native-file decoder, its
capture generators, saved `.f3d` examples, validation tools and research reports.
The reader recovers observed native records and emits JSON. It is development
and reverse-engineering tooling; it is not wired into Kit's production adapter
registry and does not provide complete editable-file translation or native writing.

The SDK's `convert.formats.Fusion.BulkSpans.ReadBulkSpans` indexes native
version-8 design streams. It accepts decompressed BulkStream and MetaStream
bytes and returns immutable record spans with class and object identities.
It checks each bulk header against its metadata entry and verifies that
continuations belong to ancestors of their primary class. The SDK index
agreed with the study on all 261,141 record boundaries and identities
across the 712 tracked archives.

`convert.formats.Fusion.DesignZip.ReadDesignZip` loads the active design
stream pair directly from `.f3d` bytes and returns the BulkStream with its
verified record spans. It checks archive size and entry limits, rejects
duplicate or encrypted members, and verifies both selected payloads.
Runtimes with standard ZIP Zstandard support can read the archive directly.
Older runtimes can supply a Zstandard decoder that accepts compressed bytes
and an expected output size. The callback must bound decompression to that
size. The archive reader checks the returned size and CRC.

`convert.formats.Fusion.ZipParameters.ReadZipParams` projects indexed
numeric parameters into Kit's neutral `Parameter` records. It retains native
expression text, display units, binding IDs, and source spans. Values use
their stored radians or centimetres where applicable. Feature-bound
parameters retain reference roles while their neutral feature owners are
being mapped. The SDK verifies each native binding's class, parameter
reference, repeated owner ID, and cached value before recording the native
owner and binding span. A rejected binding leaves the numeric value
available and produces a diagnostic. Unsupported registered parameter
records also produce diagnostics. The SDK projection matched the study on
2,607 numeric parameters across the 712 tracked archives and another 51
across the 13 Fusion 2706 captures. All 2,593 feature-bound parameters
matched the study's native owner IDs.

`convert.formats.Fusion.ZipHistory.ReadZipHistory` projects native history
references into ordered Kit feature steps, keeps histories separate by
owner, and retains the original group membership and collapse state.
It links numeric parameters to feature steps through verified bindings.
The SDK matched the study on all 779 history sequences across 725
archives, including 3 groups. It projected 2,524 steps and linked
2,587 parameters to a unique step. A parameter with no unique projected
step retains its native owner ID. Feature names and kinds are currently
projected for the observed Extrude, Revolve, and construction-plane
classes. Other entries retain native identity and provenance. Feature
definitions, geometry, and default adapter integration remain open.

`convert.formats.Fusion.ReadFusionDoc` exposes this history through a
validated `CadDocument`. It accepts a path or archive bytes and uses the
same optional Zstandard callback as `ReadDesignZip`. When more than one
history is present, pass the native `HistoryId` to select one. The resulting
document carries a projection configuration, a partial-coverage diagnostic,
and the original archive as a native document payload. It can round-trip
through the Kit JSON reader and writer. The SDK verified document projection
for all 766 histories in the tracked corpus.

For a verified single-component parameter collection, the document reader
can derive arithmetic dependencies from exact user-parameter names. It
requires an acyclic chain, compatible units, and an evaluated result that
matches the saved numeric record. The supported grammar covers grouping,
unary signs, and addition, subtraction, multiplication, and division.
Ambiguous names and unsupported expressions retain their original text.
The Fusion records store the formula and evaluated value. The dependency
identities come from resolving the formula against the native name registry.
Across 712 tracked archives, eight formulas qualified and all eight wrote as
native spreadsheet cells. Sixteen archives still require explicit history
selection because the assembly projection is incomplete.

FreeCAD spreadsheet export rewrites proven operand names to their exact
parameter aliases. FreeCAD 1.1.3 verified four arithmetic captures against
the saved Fusion API results and recalculated each result after changing an
input. The `expression_depth` capture uses the same spreadsheet bindings
to drive its native circular extrusion.

The selected history now also projects supported offset and angle
construction planes as neutral support frames. The reader verifies the
reciprocal feature and plane references, their shared ordinal, and the
orthonormal axes. Origins convert from centimetres to millimetres and
remain in component coordinates. The projected frames matched 144
tracked planes and 19 planes in newer Fusion captures. Seven tracked
plane records still produce diagnostics for unsupported layouts.
Native support selection links and parametric plane definitions remain open.

The document reader also projects sketch-local points, lines, circles,
and supported circular arcs with a support frame derived from each
sketch's verified component transform. The SDK matched all 1,005 tracked
sketch placements and 6,589 projected points, lines, and circles against
the study. All 38 planar arcs matched native trim geometry. A projected
arc outside local XY remains unsupported. The 13 newer Revolve captures
project their 13 sketches and 117 primitives. Constraints, additional
curve layouts, and native support links remain open.

For Extrude and Revolve, the document reader follows typed profile
descriptors to their owning feature, sketch, and reciprocal loop record.
It preserves the native member order and direction flags separately from
the neutral traversal order. Single outer loops formed by a whole circle,
a semicircle with its diameter, or a closed convex line ring become linked
feature inputs. The SDK matched 501 Extrude and 26 Revolve profiles in
the tracked corpus, plus all 13 newer Revolve captures. Trimmed, concave, and multi-loop selections remain
outside this projection.

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
identity. The two BRep-edge Revolves retain the native recipe, body anchor,
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
and preserves one-sided, two-sided, and symmetric limits. The effective axis follows the occupied side of the sketch.
Eligible partial polygon sweeps use the same analytic solid builder as
plane-limited sweeps. The SDK verified 15 typed definitions and eight partial
solids across 23 tracked angular features.

Full-turn polygons, ring tori, and spheres use periodic topology. The
tracked annular solid, cone, torus, and sphere matched their saved body
counts and analytic geometry. The cone retains its degenerate apex edge,
and the torus and sphere each have one untrimmed face. Kit projects all
three solids in the analytic multi-body fixture. Partial profiles that
touch the axis, custom and BRep axis definitions, surface and Boolean
Revolves, projected axes, and native Fusion output require more coverage.

Kit reads local assembly definitions and occurrences from qualified `.f3d`
archives. Repeated instances share one component definition. Nested instances
retain their parent definition, native sibling order, and local rigid placement,
with translations expressed in millimeters. Kit binds the top-level timeline
through native component and history references and retains the empty child
history identities. The SDK validated 32 definitions, 23 native instances,
and 24 expanded paths across 12 tracked archives. Three Fusion 2705.1.30
captures independently verified 11 composed placements. Sixteen archives with
joint, pin, or stale occurrence records required explicit history selection.
Component geometry, external references, and joint-solved assemblies require
further decoding.

The reader also qualifies the saved B-rep body inventory through typed
component links and reciprocal, repeated native collection membership. It
preserves native body IDs, order, and stored custom names, including Unicode.
Removal, consumption, suppression, and rollback can leave historical records
outside the active collection. The inventory uses the saved membership lists
to distinguish those records. Geometry and terminal feature ownership remain
separate. A previously reconstructed solid retains its Kit body ID when the
same native body and collection are proven. The native reader qualified
1,093 body memberships across 766 component collections in 712 tracked
archives. Saved Fusion API controls corroborate interleaved body names,
component ownership, and membership after timeline edits.

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

Standalone Fusion parameter workbooks with a fully supported formula graph
also support saved driver edits. Kit reads the edited literals, recalculates
the dependent values, and retains the original Fusion formulas and parameter
identities. A changed formula, incompatible unit, or added workbook content
fails readback. Standalone archives exported before the workbook binding was
introduced still read as their original snapshots.

FreeCAD 1.1.3 saved and reopened six controls covering four arithmetic
formulas and two equal-value inputs with distinct identities. Kit read back
the changes with the original dependency IDs and Fusion archive bytes. In
the product control, changing the width to 8 mm produced 21 mm. After
re-export, changing the scalar to 3.25 produced 27 mm.

When FreeCAD saves a supported depth edit, Kit checks the original sketch and
feature identities, the spreadsheet controls, the evaluated length, and the
attached cylinder. It restores the edited depth and recomputes the neutral
B-rep and body measures under the original Fusion identities. The original
Fusion archive remains available as source evidence. Four saved native edits
verified positive, negative, fractional, and sign-changing depths. A second
edit and save verified re-exporting the 25 mm result and re-importing the
30 mm result. Unrecomputed saves, changed profiles or directions, broken
bindings, stale shapes, and additional solids report a readback conflict.
Unchanged native saves keep the original neutral document even when FreeCAD
rewrites the B-rep bytes.

For verified part histories with independent active solid creators, Kit also
reconstructs the saved Extrude bodies from the profile and distance controls.
The creator's explicit result anchor must match the body in its current
component collection. Supported geometry includes cylinders, the observed
positive one-sided circular draft, and untapered line-ring prisms. The corpus
check matched 61 solids in 42 parts against their saved native body topology,
volume, area, and bounds. This includes 52 circular solids and nine prisms.
Saved suppression and rollback controls matched the active body inventory.

Kit also reconstructs local solids in qualified assemblies. Root bodies stay
on the root document. Other bodies are stored once in their component
definition's embedded document and placed by every occurrence of that
definition. A paired native dependency graph verifies creator and sketch
ownership. For a rotated authoring frame, the creation snapshot and its parent
scope establish the occurrence path at the time of the Extrude. This preserves
the original local geometry when a later copy creates another path. Two saved
assemblies verified seven unique solids, including three reusable component
bodies placed five times in the repeated design. Local topology and measures
matched the saved body records. Unsupported active operations leave the
assembly graph and body inventory available for inspection. Later modeling
operations, joint-driven assemblies, and native writing require further
coverage.

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

## Public SDK reader

The adapter catalog includes `fusion.f3d` with alias `f3d`. The registry
detects the active Fusion design streams in a saved archive. Call
`open_document` with `strict=False` to opt into the partial projection.
The public reader validated 766 histories across 712 tracked archives
with Python 3.14.

```python
from convert import open_document

document = open_document("part.f3d", strict=False)
```

For a qualified local assembly, `open_document("assembly.f3d", strict=False)`
returns the graph in `document.assembly`. Pass a decimal configuration string,
for example `configuration="35"`, to read a single history on its own. An archive
with multiple histories that cannot be bound to a supported assembly requires
an explicit history ID. Setting `include_brep=False` omits the projected B-rep and preserves the original
document payload. The adapter supplies a reader for `.f3d`. Native Fusion
output and strict source translation require further format coverage.

For a qualified body collection, `fusion.body_inventory` is available in
`document.metadata` for a selected history, or in each assembly definition's
`attributes`. It reports the native component ID and ordered B-rep members.
A qualified empty collection has an empty `members` tuple. Each member retains
its native object and collection IDs, the stored name, and the Kit
`design_body_id` when a body has already been reconstructed.

For archives with Zstandard-compressed members, the convenience API uses
Python's ZIP Zstandard support. On an earlier Python version, supply a
Zstandard decompression callback through `ReadOptions.values` when reading
with the registry.

```python
from convert.adapters import AdapterRegistry, ReadOptions

def read_fusion_with_codec(path, inflate_zstd):
    registry = AdapterRegistry()
    registry.introspect()
    return registry.read(
        path,
        format_id="fusion.f3d",
        options=ReadOptions(
            strict=False,
            values={"fusion.inflate_zstd": inflate_zstd},
        ),
    )
```

The callback takes compressed bytes and an expected uncompressed size. Kit
checks the result against the archive's size and CRC.

## Import provenance

- Source commit: `60ebb72ee7b64a0bf22331012b7c737c0e17d43b`.
- Source tree: `9ffe9d2d126ea4d319aa3ed47e969dbca138ea9e`.
- All 2,556 tracked source files retain their original bytes and names.
- The import merge preserves all 186 commits of the original study history.
- `Study/revolveaxes-36bd04ac77e1/ground_truth.json` adds one required saved
  reference file that the source repository's capture-folder ignore rule omitted.
- The original standalone repository remains available as a local backup.

`Study/` preserves an existing research snapshot, including historical reports,
source hashes, generated capture names, recorded machine paths and known style
findings. Its `.gitignore` retains the original capture rules. The parent
`.gitattributes` prevents line-ending conversion from changing archived evidence.
No nested `.git` directory, installed dependencies or Python bytecode is imported.
Existing source files and evidence are not reformatted or renamed by this move.
Three trailing-space diagnostics in two original executed SDK text snapshots are
retained with their recorded bytes and hashes. Newly written import documentation
is formatted separately.

## Run the reader

From the UniCAD repository root:

```sh
cd re/Fusion/Study
python3 decode_basics.py models-97a5e41e2ba7/revolve_partial.f3d
```

Reading saved files does not launch or require Fusion. Python versions without
ZIP Zstandard support need a generic `libzstd` library; pass its location with
`--zstd-library`. The original study README provides the machine-specific library
example used for its captures.

The main Python entrypoint is `decode_basics.decode_basics`. The parameter-only
entrypoint is `decode_parameters.decode_file`. These scripts use the original
flat-module layout, so run them with `Study/` as the working directory or put that
directory on the Python module search path.

## Validate saved examples

```sh
python3 validate_numeric_conversions.py --output /private/tmp/fusion-numeric-check.json
python3 validate_rational_numerics.py --output /private/tmp/fusion-rational-check.json
python3 audit_decoder_health.py --output /private/tmp/fusion-health-check.json
```

Add `--zstd-library` when the selected Python runtime cannot otherwise read the
captured archives. The health audit reports functional and comment-style results
separately, and exits nonzero while either fails. Its historical committed report
records 712 passing saved files, 156 focused suites, and the remaining legacy
comment migration. Recorded absolute paths and temporary baseline locations
refer to the original research environment; they are provenance, not portable
runtime requirements or newly acquired evidence.

Fusion API imports in the `Generate*.py` and capture scripts belong to explicitly
invoked oracle tooling. They are not imported by the saved-file decoder and are
not production conversion dependencies. The SDK package configuration remains
unchanged and does not package this research tree.

## Relocation verification

The imported files were checked byte for byte against the source snapshot.
All 729 Python modules compile. All 712 saved archives decode from `Study/` and
their complete outputs match the previous committed audit after replacing only
the relocated directory prefix. No geometry or metadata field is removed from
that comparison. The numeric suites pass 33 actual-byte conversion cases and
100 rational-evaluation checks, including five rejection guards and three
native Sweep weight-rescaling controls. The history-dependent Stitch validator also
passes from the imported tree using the preserved original commit objects. These
checks use saved files and make no live Fusion calls. The import does not resolve the decoder's recorded
unsupported features or legacy style findings.

## Continuing the decoder

Use one feature family at a time. Start with the study README's matching
capture, its `ground_truth.json`, and its focused validator. Decode the saved
archives before generating new captures. Use MetaStream to bound records and
resolve document-local object IDs. Trace the feature's owned profile, placement,
parameters and selectors before deriving geometry. Then join its creator-owned
BODY to the ASM history blob by stored entity ID and verify the resulting
bounded topology. Keep detached auxiliary roots out of the BODY comparison.
Change one input at a time when the saved cases cannot distinguish competing
interpretations. Run the focused checks before the full saved-file audit.

For focused checks, `fusion_archive.read_members` can load only the relevant
payloads. From `Study/`, use the same reader for any feature family with indexed
design records:

```python
from fusion_archive import read_members

members = read_members(
    "models-97a5e41e2ba7/revolve_partial.f3d",
    MemberSuffixes=(
        "/FusionDesignSegmentType1/BulkStream.dat",
        "/FusionDesignSegmentType1/MetaStream.dat",
    ),
)
```

Pass the matching BulkStream and MetaStream to `fusion_metadata.design_records`.
For a geometry check, include the identified cache member's full path in
`MemberSuffixes` or select `(".smb", ".smbh")` to inventory the BRep caches.
Use the unfiltered reader for a full archive integrity check. Filtered reads
validate metadata across the archive and check CRCs for the selected payloads.

### Saved corpus baseline

The baseline at `8496fc8b` decoded all 712 saved archives and emitted 2,557
feature rows. Counting `kind` across every stream gives 64 named kinds plus
`UnsupportedFeature`. The largest groups are Sketch (1,005), Extrude (526),
ConstructionPlane (151), SurfacePatch (58), and CreateComponent (54).

The 147 unsupported rows span 80 archives. Grouped by `native_kind_label`, they
are Base Feature (54), unlabeled (51), JointOrigin (16), Base Mesh Feature (14),
and Pin, MirrorComponent, Derived Base Feature, and DerivedInstance (3 each).
These counts measure recognition in this capture corpus. A named row can
still contain unresolved selectors, controls, or geometry.

Counting successful feature-level reconstruction attachments separately gives
238 ordinary extrusions, 15 trimmed extrusions, 3 plane-limited extrusions,
15 angular revolves, 14 shells, and 7 scales. There are 26 recognized Revolve
rows overall, including the three plane-limited cases below.

The focused workflow was checked against the fixed `FILES` inventories in
`validate_shell_reconstruction_integration.py` and
`validate_plane_extrusion_reconstruction_integration.py`. Load only the
design BulkStream and MetaStream plus `.smb` and `.smbh` members, then build
feature and parameter records from the selected design stream. With the same
body-blob bindings from the full decode, the focused reconstruction matched
the full result on all 15 Shell fixtures and all 8 plane-extrusion fixtures,
including two and five empty controls respectively.

### Plane-limited Revolve

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
matched its bounded body. The tracked 2705.1.30 fixtures still exercise
the legacy layout.

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
