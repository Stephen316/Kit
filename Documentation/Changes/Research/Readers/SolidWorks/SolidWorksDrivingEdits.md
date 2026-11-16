<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Licensed SOLIDWORKS circle-boss driving edits

This A04c evidence uses the three independent Front Plane discovery archives from SOLIDWORKS `34.4.1.1011`. The private edit harness ran with source checkout `e7022b3764ef363ac0f16dc7fbb4b2220b1ebed8` and acknowledged the original native receipt SHA-256 `057b15e1cd8765d2e84086459e1c45f5e397e399791e69e0b190ddd1c7be243f`. It opened writable scratch copies under the shared Windows oracle lease. The original native files and healthy control passed SHA-256 equality at the end. [Original licensed capture and typed archive replay](SolidWorksRadialDiscovery.md)

Each case independently changed `diameter_mm` by 2 mm at a fixed depth, restored it, changed `depth_mm` from 7 mm to 10 mm at the original diameter, and restored that parameter. SOLIDWORKS rebuilt after every edit. The collector checked that the two native driving dimensions remained attached to the circle and `BlindBoss`, respectively, and that the circle center stayed coincident with the document Origin. Each rebuilt result retained one solid. Its measured volume followed `π × radius² × depth`. The centroid followed the depth along the positive normal.

| Original diameter (mm) | Baseline (mm³) | Diameter edit (mm³) | Depth edit (mm³) |
| ---------------------- | -------------- | ------------------- | ---------------- |
| 13                     | 929.1260273    | 1237.0021074        | 1327.3228961     |
| 19                     | 1984.7011589   | 2424.5241304        | 2835.2873699     |
| 23                     | 2908.3293991   | 3436.1169649        | 4154.7562844     |

The first process saved the restored copies with zero save errors and warnings. The separate fresh process reopened them, recovered each baseline before and after rebuild, and left the saved copies byte-for-byte intact. An offline receipt check independently matched all 21 observations, both exact process identities and normal exits, source and restored hashes, and four passing one-solid controls. The native edit phase SHA-256 is `5771702bdc05c3b4c3afce032fc5c281b2dcb8f9b85f6b6893c50cb0f0dea4d8`. The fresh reopen phase SHA-256 is `ec2f6eacd202f2b74274ada3f118399f02076acf05c275d169dfa698db81a9a3`. The sealed receipt SHA-256 is `2018982d166ee35af1e7dc5b79c842486b3be27a4874bf01c8ec0515811af371`.

The scope is a fixed Front Plane, a single circle with a driving diameter, and a positive blind Boss. The source files and measurements are private. A02d paired qualification and A13 target acceptance remain open. P02 and P05 were outside this experiment. [Automation register](../../../../Reference/Research/AutomationSteps.md)
