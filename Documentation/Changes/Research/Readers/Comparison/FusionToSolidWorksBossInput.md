<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Fusion P03 source evidence for SOLIDWORKS Boss input

The replay checks four original positive XY P03 archives and their paired SOLIDWORKS observations at capture revision `89c25945f5833ad9c3a1c6c683df510b5702dd54`. It uses the recorded Fusion same-process reopen and the independent SOLIDWORKS separate-process reopen. The exact physical source evidence covers the baseline, width and height edits, and the blind-depth edit. [Paired archive evidence](RectangularPairEvidence.md), [Fusion selection evidence](../FusionBossProfileEvidence.md)

The native Fusion Boss selects the sole four-line outer loop from sketch 202. Each adjacent pair of lines refers to the same saved corner ID. The one separately recorded coincidence joins the free perimeter corner 228 to fixed Origin 205. The four native axis relations bind the same physical sides as the paired SOLIDWORKS relations. The two dimensions use the measured ordered source operands, and each maps to the exact selected counterpart edge. The report retains the native and neutral loop orders separately. The height edit agrees with its 23 mm scalar and ordered geometry. Its saved extension anchor still carries the earlier 20 mm coordinate. [Saved sketch and Boss readback](../../../../../re/solidworks/WriterResearch/FusionBossNativeEvidence.py)

| Native parameter | Model parameter and binding | Owner              | Saved mode                 |
| ---------------- | --------------------------- | ------------------ | -------------------------- |
| `width_mm`       | 258 and 259                 | Sketch feature 207 | Independent driving length |
| `height_mm`      | 268 and 269                 | Sketch feature 207 | Independent driving length |
| `depth_mm`       | 285 and 286                 | Boss feature 277   | Independent driving length |
| `d4`             | 288 and 289                 | Boss feature 277   | Owned zero taper           |

Each boundary matches the saved parameter table, literal expression, binding slot, feature owner and reciprocal dynamic update. The current partial neutral reader assigns those parameters the `reference` role and retains their literals. The saved positive blind Fusion New Body and SOLIDWORKS first Join consume the same physical profile and each produces the only solid. The four paired volumes are 8,000, 8,200, 9,200 and 9,600 mm³. The paired center of mass and world displacement agree within the recorded tolerances. [Paired direction and body evidence](../FusionBossDirectionEvidence.md)

All four original Fusion archives still fail strict reading at the unmodeled native class gate. The typed Design graph has two `FusionSketchLinearDim` and five `SketchGeomConstraint` primary records outside that strict allowlist. Public portability refuses the retained archive with `RetainedPayload`. The unchanged SOLIDWORKS research `ProjectBoss` refuses the original partial neutral documents with `RetainedMetadata`. The full source archive is still attached, and partial history and assembly diagnostics remain. The typed source contains prism history and snapshot records and graphics.

The SOLIDWORKS contract requires one portable reference sketch with four lines and a fixed origin, explicit corner joins, and three driving lengths without neutral expressions or an extra taper. Fusion retains a native sketch step, shared corner points, one explicit anchor, literal expressions and the fourth owned parameter `d4`. Those differences and the retained source state remain in the evidence. Target admission and native authoring remain open. [SOLIDWORKS Boss input contract](../../../../../re/solidworks/WriterResearch/BossInput.md)

The Python 3.14 canonical report SHA-256 is `f3a41cd2a17c055d9cae1fd5c879bdfbe614b3dea8fdb14083333f79d04f7ef8`. [Read-only evidence command](../../../../../re/solidworks/WriterResearch/FusionBossInputEvidence.py)

```sh
PYTHONPATH=src:re/automation uv run --frozen --no-default-groups --extra dev --python 3.14 python -B \
  re/solidworks/WriterResearch/FusionBossInputEvidence.py
```
