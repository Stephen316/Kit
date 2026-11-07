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

The selected history now also projects supported offset and angle
construction planes as neutral support frames. The reader verifies the
reciprocal feature and plane references, their shared ordinal, and the
orthonormal axes. Origins convert from centimetres to millimetres and
remain in component coordinates. The projected frames matched 144
tracked planes and 19 planes in newer Fusion captures. Seven tracked
plane records still produce diagnostics for unsupported layouts.
Native support selection links and parametric plane definitions remain open.

The document reader also projects sketch-local points, lines, and circles
with a support frame derived from each sketch's verified component
transform. A sketch frame preserves placement independently of its native
support selection. The SDK matched all 1,005 tracked sketch placements and
6,589 projected primitives against the study. The 13 newer Revolve captures
also project their 13 sketches and 117 primitives. Constraints, additional
curve layouts, and native support links remain open.

For Extrude and Revolve, the document reader follows typed profile
descriptors to their owning feature, sketch, and reciprocal loop record.
It preserves the native member order and direction flags separately from
the neutral traversal order. Single outer loops formed by a whole circle
or a closed convex line ring become linked feature inputs. The SDK matched
501 Extrude and 25 Revolve profiles in the tracked corpus, plus all 13
newer Revolve captures. Trimmed, concave, and multi-loop selections remain
outside this projection.

Revolve steps also retain the native operation, sidedness, projected-axis
flag, and owned angular parameter bindings. Entity-limited steps mark the
stored angle inactive and preserve target order. An owned construction-axis
selection retains its native identity, and each resolved construction-plane
target links to its support frame and feature dependency. The SDK matched
the controls for all 26 tracked Revolves and 13 newer captures, including
23 plane target links. Four tracked axis selections remain unresolved.
These fields are native feature attributes. The editable Revolve definition
and geometry are still open.

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
`--zstd-library` if needed for the saved archives.

The integration audit passed the functional checks on all 712 archives with
default settings. With plane-limited Revolves enabled, the three captures
above gained reconstructions. After removing those three additions and
restoring their prior unresolved rows, all 712 serialized outputs matched the
baseline hashes. The historical comment-style findings remain separate from
the functional result. The original freeze validators pin the import-era
source hashes and must be run against their historical source snapshot.
