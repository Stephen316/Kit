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
controls. Use the measured arcs as an independent check for future source
decoding. The next differential needs the same target plane and sketch with
only the direction hint changed to isolate how Fusion selects the branch.
Source-only branch selection and plane-limited Revolve reconstruction remain
unresolved.
