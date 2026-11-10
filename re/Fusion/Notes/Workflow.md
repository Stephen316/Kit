<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Saved-file decoding workflow

[Fusion feature index](../README.md)

## Run the reader

From the UniCAD repository root:

```sh
cd re/Fusion/Study
python3 decode_basics.py models-97a5e41e2ba7/revolve_partial.f3d
```

Reading saved files does not launch or require Fusion. Python versions without
ZIP Zstandard support need a generic `libzstd` library; pass its location with
`--zstd-library`. The [study commands](StudyWorkflow.md#run-the-reader) include the library
path recorded on the capture machine.

The main Python entry point is `decode_basics.decode_basics`. The parameter-only
entry point is `decode_parameters.decode_file`. These scripts use the original
flat-module layout, so run them with `Study/` as the working directory or put that
directory on the Python module search path.

## Validate saved examples

Run from `re/Fusion/Study`.

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

## Continuing the decoder

Use one feature family at a time. Use the [feature index](../README.md#feature-index) to find the matching
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
`MemberSuffixes` or select `(".smb", ".smbh")` to inventory the B-rep caches.
Use the unfiltered reader for a full archive integrity check. Filtered reads
validate metadata across the archive and check CRCs for the selected payloads.

For SDK imports, a profile of the saved corpus found that repeated field name
resolution in the shared interchange models accounted for most of the read
time. Kit now builds a bounded alias index for each declared model layout and
resolves unfamiliar input keys without adding them to the cache. Across three
paired fresh Python 3.14 runs against `fd02025b`, median public Fusion read time
fell from 6.39 to 3.26 seconds for 712 tracked archives and a Fusion 2706.1.17
holdout. The 747 projected documents and the expected history selection errors
matched exactly.

## B-rep omission benchmark

On the `c705daf9` SDK baseline, three paired reads of the 712 tracked
archives took a median of **2.834 s** with B-rep and **2.847 s** with
`include_brep=False`. The benchmark used Python 3.14.7 on macOS ARM64,
explicit `source_format="fusion.f3d"`, `strict=False`, and alternated the
order of the two modes. Timings include file reads and exclude SDK imports
and result comparisons.

All 696 successful geometry-omitted reads matched the full document after
applying the same B-rep filter. That comparison includes body identities,
diagnostics, and the original archive payload. The other 16 archives produced
identical history-selection errors. The full reads had 82 root B-reps and five
component B-reps.

A separate `cProfile` pass confirmed that both modes ran the same projection
stages:

| Stage              | Calls with B-rep | Calls without B-rep | Cumulative seconds without B-rep |
| ------------------ | ---------------: | ------------------: | -------------------------------: |
| `ReadDesign`       |              712 |                 712 |                            3.536 |
| `ProjectFusionDoc` |              712 |                 712 |                            6.108 |
| `ProjectBodyList`  |              696 |                 696 |                            0.797 |
| `ProjectRevBody`   |              324 |                 324 |                            0.033 |
| `ReadBody`         |                8 |                   8 |                           <0.001 |
| `FilterDocument`   |              701 |                 701 |                            0.344 |

The profiler adds overhead. Its cumulative times include child calls and
should not be summed. `ProjectBodyList` includes work that determines
retained body identities and diagnostics. `ReadBody` can supply feature
corroboration independently of the final B-rep. The candidate for omission is
final B-rep materialisation after those checks. Measure it separately before
changing the reader. For overall read time, reading and indexing the design streams is the larger measured target.

## Navigate SDK source with Graphify

From the repository root, use the local Graphify CLI to build a graph of the
SDK decoder. The output lives under the repository's ignored `tmp/` directory.

```sh
graphify extract src/convert/formats/Fusion --code-only --force --no-cluster --out tmp/FusionGraph/Extract
graphify query 'where are construction plane control bindings validated' \
  --seed ReadPlaneControls --budget 700 --graph tmp/FusionGraph/Extract/graphify-out/graph.json
```

Rebuild after SDK source changes. Returned source paths are relative to
`src/convert/formats/Fusion`. Start with the feature index
for status and tests. Query the graph when a reader crosses several modules.
Check the returned source and focused tests before recording a finding. The
graph covers SDK source relationships. The notes link to study captures,
validators and reports.
