<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# SOLIDWORKS P02 circle binding readback

The [readback launcher](../../../../../re/automation/PairedCaptures/SolidWorksAuthoring/ReadP04SolidWorks.ps1) accepts a standalone P02 scope. It reads all five archives in the original [P02 receipt](../../../../../re/automation/PairedCaptures/P02/solidworks-4a9e35f34a39/receipt.json) from read-only scratch copies. The launcher checks the original and scratch hashes before and after the run. The [circle collector](../../../../../re/automation/PairedCaptures/SolidWorksAuthoring/P02Readback.cs) measures the pinned healthy control at both ends of one fresh, owned SOLIDWORKS session.

## Run the collector

Use a complete checkout of the reviewed revision and a dedicated Windows desktop with licensed SOLIDWORKS build 34.4.1.1011. Close all SOLIDWORKS sessions before the run. Use a new output folder under an existing private directory outside the checkout.

```powershell
powershell.exe -NoProfile -STA -File re/automation/PairedCaptures/SolidWorksAuthoring/ReadP04SolidWorks.ps1 -ReadbackScope P02 -OutputDirectory 'C:/CadResearch/P02Readback01' -InteropAssembly 'C:/Program Files/SOLIDWORKS Corp/SOLIDWORKS (3)/api/redist/SolidWorks.Interop.sldworks.dll'
```

Keep the plan, measurements and receipt together. The plan binds the collector sources, build and capture hashes. The measurements record load diagnostics, datum, sketch transform, constraints, dimensions, native owner and target identities, circle geometry and the return from rebuild. The two control measurements and the owned application exit form part of the receipt.

The collector checks the driving diameter's sketch owner and the sketch segment attached to its display annotation. It also checks the diameter relation's definition operand and the coincidence of the circle center with the document origin. Native sketch ownership and the entity ID together distinguish points whose IDs repeat in different sketches. [Sketch relation operands](../../../../Gotchas/Conversion/SolidWorksSketchRelationOperands.md)

P02 is in the circular-sketch qualification split. This run supplies SOLIDWORKS source evidence for A02d. Pair admission, reader qualification, frozen-rule evaluation and target application acceptance remain governed by the [step register](../../../../Reference/Research/AutomationSteps.md).

## Licensed observation

On November 16, 2026, SOLIDWORKS 2026 build 34.4.1.1011 opened all five read-only scratch copies at collector revision `76f2b6195d51fda108f0767807b1390fd89d99d1`. All files returned zero open errors and warnings. Both controls measured one solid body and 881,814.3482038013 mm³. The launcher verified the input hashes after readback, and the owned process exited.

All ten observations before and after rebuild identify one fully defined circle owned by `CircleSketch`, attached to its driving `diameter_mm` through the native annotation and the diameter relation. The coincidence definition identifies the document `Origin` point and the circle center as separate native points. Their world coordinates are both (0, 0, 0) mm. All five sketches have one region and zero solid bodies.

| Archive       | Native support | Native units | Diameter (mm) | Radius (mm) | Measured area (mm²) |
| ------------- | -------------- | ------------ | ------------: | ----------: | ------------------: |
| Baseline A    | Front Plane    | MMGS         |            10 |           5 |   78.53981633974484 |
| Baseline B    | Front Plane    | MMGS         |            10 |           5 |   78.53981633974484 |
| Diameter edit | Front Plane    | MMGS         |            16 |           8 |  201.06192982974675 |
| Inch display  | Front Plane    | IPS          |            10 |           5 |   78.53981633974484 |
| YZ sketch     | Right Plane    | MMGS         |            10 |           5 |   78.53981633974484 |

The private plan SHA-256 is `c2ca2b9a526b3a00ddd24a76081b0cf945c1e367f4c2f264ff070a0167e12e49`, the measurements SHA-256 is `114ac4b28716d43930cb33796420301d53eb4baff394064c86e597003a36ec42`, and the receipt SHA-256 is `0e6229e3f4df23e9d3c3ee6d1d0dc628cc6b699d29b75092ee76009365dbadb5`. The receipt reports five verified circle bindings. The original [authoring measurements](../../../../../re/automation/PairedCaptures/P02/solidworks-4a9e35f34a39/measurements.json) preserve the driving edit and restoration. This readback keeps the archive bytes unchanged. P05 remains reserved for the frozen-rule holdout.
