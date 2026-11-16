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

Each binding matches the saved parameter table, literal expression, slot, feature owner and reciprocal dynamic update. The partial reader assigns those parameters the `reference` role and retains their literals. The scoped strict reader projects all four as `driving`, with width and height owned by the reference sketch step and depth and zero taper owned by the Boss. The saved positive blind Fusion New Body and SOLIDWORKS first Join consume the same physical profile and each produces the only solid. The four paired volumes are 8,000, 8,200, 9,200 and 9,600 mm³. The paired center of mass and world displacement agree within the recorded tolerances. [Paired direction and body evidence](../FusionBossDirectionEvidence.md)

All four archives now pass strict source reading. The scoped proof admits the two `FusionSketchLinearDim` and five `SketchGeomConstraint` records on the verified rectangle. The resulting document retains its typed BREP, physical material, complete typed native state, the read-only marker and the separately owned zero taper. The partial route keeps the complete original archive bytes and the history and assembly diagnostics. [Strict source readback](FusionStrictConstrainedPrism.md)

| Observed target entry            | Fusion partial source | Fusion strict source                      |
| -------------------------------- | --------------------- | ----------------------------------------- |
| Public portability check         | `RetainedPayload`     | `UnqualifiedGeometry`                     |
| Public `solidworks.sldprt` write | No registered writer  | No registered writer                      |
| Research `ProjectBoss`           | `RetainedMetadata`    | Standalone feature-history geometry guard |

The public writer requests emit zero bytes. The research contract requires a portable reference sketch with four lines, a fixed origin and explicit corner joins, and three driving lengths without expression or taper records. The strict Fusion records retain their shared endpoints, distinct origin coincidence, typed BREP and material, literal expressions, and fourth parameter. The research guard reaches the geometry boundary with that state intact. SOLIDWORKS target admission and native authoring remain open. [SOLIDWORKS Boss input contract](../../../../../re/solidworks/WriterResearch/BossInput.md)

The earlier replay at `dcad571aba31b521cb37e7ccc919cf0bb9667936` recorded `Unmodeled native Fusion semantic entity class` for all four strict reads and yielded report SHA-256 `f3a41cd2a17c055d9cae1fd5c879bdfbe614b3dea8fdb14083333f79d04f7ef8`. The current Python 3.14 report yields SHA-256 `a966bd30a6d8b58e3794c924ec36b47b83911185451f81c0995a7834afe49eec`. [Read-only evidence command](../../../../../re/solidworks/WriterResearch/FusionBossInputEvidence.py)

```sh
PYTHONPATH=src:re/automation uv run --frozen --no-default-groups --extra dev --python 3.14 python -B \
  re/solidworks/WriterResearch/FusionBossInputEvidence.py
```
