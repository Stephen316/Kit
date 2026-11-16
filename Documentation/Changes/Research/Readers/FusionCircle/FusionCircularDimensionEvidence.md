<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Fusion circular dimension discovery evidence

The replay reads four independently authored Fusion 2705.1.30 discovery controls from Git revision `38079a7c1da24a3685af0e4c74854a8297006c80`. The Fusion API authoring script records the driving flag, circle geometry, parameter value and expression before exporting each archive. The historical ground truth associates observations with filenames. The replay pins the saved files and ground truth separately in the same historical Git tree. Capture-time digests remain unavailable. [Fusion authoring script](../../../../../re/Fusion/Study/GenerateDimensionControlModes.py), [historical measurements](../../../../../re/Fusion/Study/dimcontrols-2a0d0bdbc8a6/ground_truth.json)

| Control pair | Measured center, mm | Measured radius, mm | Parameter expression | Strict dimension class                 |
| ------------ | ------------------- | ------------------- | -------------------- | -------------------------------------- |
| Diameter     | −13, 26, 0          | 8.5                 | `17.00 mm`           | `664AD49F-207F-4CD5-8555-DD269E9F09EA` |
| Radius       | 12, 23, 0           | 14                  | `14.00 mm`           | `8EDAC24D-35D4-4591-B8E7-B3EA081C9DF0` |

Before packaged support, the strict read stopped at one unrecognized primary dimension class at Design segment 0, object 234. The strict reader now verifies that dimension and emits a closed XY loop with its one circle and owned parameter. The partial reads match the native driving and reference flags, measured geometry and values, display units, and parameter expressions. The neutral relation reaches circle 230 and parameter 235 through binding 236 and sketch feature 207. The partial reader assigns `driving` to the two verified driving parameters after the circular dimension and its owner resolve. The other two controls retain `reference`. The partial reads retain an empty declared profile-loop list.

The initial archive report SHA-256 was `d9c75f49d36ae63e6682b7f8539d9a44caeffc205f608a6a98b5e43281a01c39`. The two driving parameter roles are the only report changes. The full neutral documents likewise differ only at those two role fields. The four neighboring angle and tangent controls retain identical neutral documents after JSON round-trip.

## Saved circular sheet membership

The Design records reciprocate sketch 202 and feature 207. The sketch owns circle 230, center 228, dimension 234 and the separate origin point. Its circle has no endpoints and stores a full angular interval from 0 to 2π radians. The four sketch-only archives have no feature-selected profile descriptor or loop records.

Each archive has one typed ASM sheet snapshot. The existing circular snapshot checker confirms the complete topology, plane and circle geometry, and tag correspondence. Face 4 owns loop 5, whose sole coedge 7 references edge 9. The edge begins and ends at seam vertex 11 and uses −π to +π. The edge and coedge carry the same unsplit Design curve tag 102 with their respective saved directions 1 and 0. The report pins the snapshot member path, size and SHA-256 and retains the Design source spans. [Saved-loop replay](../../../../../re/automation/FusionCircularLoopEvidence.py), [circular snapshot seams](../../../../Gotchas/Conversion/Fusion/Api/FusionCircleSnapshotSeams.md)

The original licensed measurements recorded the circle center, radius and dimension mode. The historical capture has no native API profile-loop inventory or curve evaluator bounds. A later licensed replay measured those properties for the four pinned dimensioned controls. [Dimension capture](../../../../../re/Fusion/Study/GenerateDimensionControlModes.py), [packaged replay and licensed readback](FusionStrictRadialPrototype.md)

The prior role-corrected report SHA-256 was `dfc2e5de9c4aad3a11d03cc59e7da664522cc95d911a5336423985505ff992d7`. Adding the four saved-sheet proofs produced `eead06c25fc45e2078ff34deec8795bfecc43f38453342acaa0c88e6cc303430`. The current replay digest is `5f03d294dcbe6007e384259b4ba9e3d91bb8e2b4da291140564000d049bd7ff6`. Restoring the earlier strict status and qualification fields reproduces the previous report byte for byte. [Replay](../../../../../re/automation/FusionCircularDimensionEvidence.py), [archive gate](../../../../../tests/Research/Archives/ArchiveEvidenceTests.py)

```sh
uv run --frozen --python 3.14 python re/automation/FusionCircularDimensionEvidence.py
```
