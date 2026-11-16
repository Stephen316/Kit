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

| Control pair | Measured center, mm | Measured radius, mm | Parameter expression | Unrecognized strict dimension class    |
| ------------ | ------------------- | ------------------- | -------------------- | -------------------------------------- |
| Diameter     | −13, 26, 0          | 8.5                 | `17.00 mm`           | `664AD49F-207F-4CD5-8555-DD269E9F09EA` |
| Radius       | 12, 23, 0           | 14                  | `14.00 mm`           | `8EDAC24D-35D4-4591-B8E7-B3EA081C9DF0` |

Each strict read stops at one unrecognized primary dimension class at Design segment 0, object 234. The partial reads match the native driving and reference flags, measured geometry and values, display units, and parameter expressions. The neutral relation reaches circle 230 and parameter 235 through binding 236 and sketch feature 207. The partial reader now assigns `driving` to the two verified driving parameters after the circular dimension and its owner resolve. The other two controls retain `reference`. The partial reads retain an empty declared profile-loop list. A05c qualification still requires fresh native evidence and portable semantics within the claimed scope.

The initial archive report SHA-256 was `d9c75f49d36ae63e6682b7f8539d9a44caeffc205f608a6a98b5e43281a01c39`. The two driving parameter roles are the only report changes. The full neutral documents likewise differ only at those two role fields. The four neighboring angle and tangent controls retain identical neutral documents after JSON round-trip.

Run the evidence command from the repository with Python 3.14. It prints a canonical JSON report with SHA-256 `dfc2e5de9c4aad3a11d03cc59e7da664522cc95d911a5336423985505ff992d7`. The archive gate runs the same command through a fresh Python process and checks the digest. [Replay](../../../../../re/automation/FusionCircularDimensionEvidence.py), [archive gate](../../../../../tests/Research/Archives/ArchiveEvidenceTests.py)

```sh
uv run --frozen --python 3.14 python re/automation/FusionCircularDimensionEvidence.py
```
