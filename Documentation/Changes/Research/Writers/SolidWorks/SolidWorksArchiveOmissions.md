<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Measure P03 archive stream omissions

A licensed SOLIDWORKS 2026 build 34.4.1.1011 opened the
[receipt-pinned P03 rectangular blind boss](../../../../../re/automation/PairedCaptures/P03/solidworks-db1390476325/P03-solidworks-baseline-a.SLDPRT)
and a complete repack of its 37 saved archive members. The source archive
SHA-256 was `db1390476325f5817e6f80fb4067a3c6df5cc063315604c133ccbeaafdeac357`.
The repack SHA-256 was `42015a44feda1560712fd9244c2d47783e0df354c9f8c0898a2f9bad71d4ee77`.
Three derivative archives omitted only the listed members and retained the
remaining expanded stream bytes and verified ZIP metadata.

| Case                      | Omitted members                                                                         | Entries | Archive SHA-256                                                    |
| ------------------------- | --------------------------------------------------------------------------------------- | ------: | ------------------------------------------------------------------ |
| Partition                 | `Contents/Config-0-Partition`                                                           |      36 | `408fadf5b767dd1fa450426be9829291774ec3122ce42c0c407f72a9338f5aba` |
| Display and ghost members | `Contents/Config-0-LWDATA`, `Contents/DisplayLists`, `Contents/Config-0-GhostPartition` |      34 | `fd8449bcfacf2a1c360c1afb4d365652df772bc36bf9ab2a3e29536bdf5ec6d5` |
| Combined                  | All four members from the preceding cases                                               |      33 | `82370e91433d762dd28adc7cb2ca9b2544e5714c3d4f5a16736837f723d55969` |

Each original, repacked and omitted archive opened read-only with zero errors
and warnings in a fresh owned application process. One solid existed before
the explicit rebuild. The `RectangleSketch` → `BlindBoss` history remained live
and linked to the owned depth dimension. Editing 10 → 12 → 10 mm changed volume
from 8,000 → 9,600 → 8,000 mm³ and center of mass from
(20, 10, 5) → (20, 10, 6) → (20, 10, 5) mm.

Stock controls opened and rebuilt before and after each candidate. Each measured
one solid with volume 881,814.3482038013 mm³. All seven owned application processes
in the two accepted diagnostics exited with native code zero and drained.
The harness checked the source, stock and candidate hashes after closure.
The [COM launch observation](../../../../Gotchas/Research/Workers/SolidWorks/SolidWorksStockExitMode.md)
records the earlier rejected control.

The independent omission report SHA-256 is
`5cf84203f63da59ac8301c5087448c85d175210cb1a92abf8c163d0031ec5e52`.
The combined report SHA-256 is
`9431a699a5c0ceb701a7271f25c3f8f7133ce2a783203c01d7227c7cc51fdd0b`, and its
native measurements SHA-256 is
`536c608dab710242679ddb8aef16479b6d836986b3760b35974a44ae636c2a6c`.

The observation establishes that the four members can be omitted together in
this generation-19000 P03 source archive on this application build. It informs
the [configuration index and framing research](SolidWorksPartConfigurationIndex.md).
The [A12 exit](../../../../Reference/Research/AutomationSteps.md#a12-solidworks-writer-research)
still requires a complete archive synthesized from portable inputs,
independent range and holdout controls, and editable target acceptance
through save and reopen.
