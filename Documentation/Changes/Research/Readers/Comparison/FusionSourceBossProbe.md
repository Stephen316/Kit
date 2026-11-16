<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Source-derived positive XY Fusion Boss candidates

The research probe derives the P03 baseline and three independent edit variants from SOLIDWORKS archives at capture revision `89c25945f5833ad9c3a1c6c683df510b5702dd54`. It joins each archive to its separately reopened measurement and uses the saved selected loop, signed depth and typed owner links. The input has one physical Boss operation responsible for the only solid. In that scope the first SOLIDWORKS Join maps to Fusion's New Body operation. The report retains the original source operation, IDs and unresolved native feature definitions. [Neutral source mapping](FusionNeutralRectanglePlan.md), [paired Boss direction evidence](../FusionBossDirectionEvidence.md)

The probe reuses the distinct Origin coincidence and emits a one-sided positive blind cuboid. It allocates `width_mm` and `height_mm` to the sketch in slots 1 and 2. The Boss owns the literal `depth_mm` in slot 3 and zero taper `d4` in slot 4. The parameter table and its name index contain those four entries. The annotation cache stores literal text, values and ordered endpoints derived from the same direct dimensions. The public authoring contracts and the P01 witnesses retain their existing paths.

Readback verifies that the Boss profile proxy and region select the four matched lines on the anchored XY sketch. It checks the complete compute order and reciprocal dependency edges, the saved Boss operation and history, the prism's six faces, twelve edges and eight vertices, and geometry consistency of the volume, centroid and inertial cache. The centroid and volume agree with the independent SOLIDWORKS observations.

| Source variant | Dimensions, mm | Volume, mm³ | Centroid, mm  |
| -------------- | -------------- | ----------- | ------------- |
| Baseline       | 40 × 20 × 10   | 8,000       | (20, 10, 5)   |
| Width edit     | 41 × 20 × 10   | 8,200       | (20.5, 10, 5) |
| Height edit    | 40 × 23 × 10   | 9,200       | (20, 11.5, 5) |
| Depth edit     | 40 × 20 × 12   | 9,600       | (20, 10, 6)   |

Run the command with Python 3.14 and a new private directory outside the checkout. The output manifest pins the source receipt, measurement, archive and source programs. The generated archives have fresh identifiers and timestamps, so the manifest binds the exact output bytes for each run. [Probe](../../../../../re/Fusion/Reconstruction/DimensionAuthoring/SourceBossProbe.py)

```sh
PYTHONPATH=src:re/automation uv run --frozen --python 3.14 python -B \
  re/Fusion/Reconstruction/DimensionAuthoring/SourceBossProbe.py \
  --output /private/P03Candidates
```

A locked Python 3.14 Windows replay at `90bdd0e8` generated and checked all four candidates. Its sealed output manifest SHA-256 is `b030dc8cf99425abd3b523058c2c58ab767ff9096e56d6718966b7504656d5f8`.

The candidate uses the constructor's default material. Physical density and mass parity remain unqualified. Licensed acceptance still requires a native readback of the selected profile identity, the three independently effective driving edits, restoration and rebuild, and fresh-process reopen with healthy controls. [Licensed P03 witness procedure](FusionSourceBossWitness.md)
