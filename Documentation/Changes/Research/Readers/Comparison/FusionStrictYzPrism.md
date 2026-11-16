<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Strict reading of the measured Fusion YZ prism

The strict Fusion reader accepts the sealed P03 metric origin-YZ New Body
archive. The saved `CoordinateSystem` and `DRMatrix` own the same frame through
the original YZ WorkPlane. Local X maps to world −Z, local Y maps to world +Y,
and local Z maps to world +X. Width is a sketch-owned `distance_y` at
`40 mm`, height is a sketch-owned `distance_x` at `20 mm`, and the independent
feature-owned literal `10 mm` drives the one-sided extrusion along +X.
The separate taper is `0.0 deg`.

The positive closed body covers `(0, 0, 0)..(10, 40, 20)` mm. Its centroid is
`(5, 20, 10)` mm, with volume 8,000 mm³ and surface area 2,800 mm². The native
journal and saved solid independently confirm the cap stations, selected
curve tags, typed material, and matching feature and serializer ownership.
The 170-record snapshot has one auxiliary section in world YZ and one in local
XY. The reader checks each section's original placement and reciprocal
edge and coedge attributes, then compares their world positions with the
selected sketch curves. Geometry comparison uses local views. The original
journal, both section frames, identity placement records, and native caches
remain in the complete V2 state. [Saved structure and measurements](FusionDatumPrismEvidence.md)

Wire-valid controls change one matrix, the selected datum, a dimension axis,
each auxiliary section's curve, and a section root placement. The reader also
refuses the translated frame, inch display, negative direction, zero distance,
and nonzero taper mutations of this source. The existing positive metric and
inch XY controls and the measured negative XY control retain their original
physical evidence. The partial reader returns the exact source archive.
Public Fusion writing emits zero bytes for the strict YZ result and for the
same state after removal of its read-only marker.

The independent Fusion 2706.1.17 observations came from a same-process reopen.
The SOLIDWORKS 34.4.1 comparison used a separate-process reopen. Fresh Fusion
reopening, complete live relation and dimension targets, and editable
authoring qualification remain open for this YZ source.

The historical proof-only YZ report and both prior strict reports are pinned at
`9b648ea17ce750c4c556b8f653c2c800adff365a`. The geometry-only signed XY report
retains its exact current checksum.

| Process report        | Current SHA-256                                                    | Prior SHA-256                                                      |
| --------------------- | ------------------------------------------------------------------ | ------------------------------------------------------------------ |
| Constrained prism     | `d7c7ab718de1aaf5f5f6cd6b952849db50d07c56d42c948050b91ca162ee4fab` | `7c2bac73e8a3b6241ccddf0da5bbad20b8d4383fdfb9f43e7e091c438a82cef1` |
| YZ datum prism        | `8fb0b77a5d097c95119649ab550a3718b93f567d9652b8f6b40cc956cd1f65e2` | `941c644135992ecfc2226769e4beae569f60870c0b1af6af739114b12ccd5b49` |
| Generic journal state | `f69f6cb0fc689fea9186c0ca1058ae6aa8212d141c75e87cc655c76f70f828db` | `9cb493ca2f27ba479a0b8bd4dd13d88a54d643535e693e847a6e4259330c6f29` |

```sh
uv run --frozen --no-default-groups --extra dev --python 3.14 python -B \
  re/automation/FusionConstrainedPrismEvidence.py
uv run --frozen --no-default-groups --extra dev --python 3.14 python -B \
  re/automation/FusionDatumPrism/VerifyDatumPrism.py
uv run --frozen --no-default-groups --extra dev --python 3.14 python -B \
  re/automation/FusionSignedPrism/VerifyJournalState.py
```
