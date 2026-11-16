<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Saved Fusion P03 YZ prism evidence

The replay reads the sealed P03 `plane-yz` archive from
`89c25945f5833ad9c3a1c6c683df510b5702dd54`. Its SHA-256 is
`c14b8c4a791415c5eb356d4c1e4143cb4b76ab856e0f84357c08b4f4da125b3a`.
The original [paired direction replay](../FusionBossDirectionEvidence.md)
verified the feature extent and physical displacement.

The saved CoordinateSystem 204 and DRMatrix 215 map local X to world −Z,
local Y to world +Y, and local Z to world +X. Their owned definition follows
datum reference 211 and recipe 214 to WorkPlane 44 in the component's origin
geometry. Its U axis is +Y and its V axis is +Z. The feature stores +X as the
profile normal and +10 mm as the bound one-sided distance.

| Literal driver        | Sketch endpoints in local mm | Ordered native operands |
| --------------------- | ---------------------------- | ----------------------- |
| `width_mm` = `40 mm`  | `(0, 0, 0)` to `(0, 40, 0)`  | 228, 230                |
| `height_mm` = `20 mm` | `(−20, 0, 0)` to `(0, 0, 0)` | 242, 228                |

Each dimension retains its own sketch binding, local axis, cached length and
ordered endpoints. The neutral evidence uses `distance_y` for width and
`distance_x` for height. The separate feature-owned taper is `0.0 deg`.
The validated neutral geometry has world bounds `(0, 0, 0)..(10, 40, 20)` mm,
centroid `(5, 20, 10)` mm, volume 8,000 mm³, and area 2,800 mm². The original
Fusion and separate-process SOLIDWORKS observations agree on the world
sketch edges, area, volume, and centroid. The generic saved solid has six
faces, twelve edges, and eight vertices. Body key 0, Design body 309,
extrusion 277, operation 301, and secondary tag 7 resolve together.

The generic snapshot has 170 typed records. Its profile section at root 2
stores world YZ geometry with an explicit identity transform. Its sketch
section at root 3 stores sketch-local XY geometry. The Design frame maps the
local section to the selected world cap. Each section has 33 owned records and
four edge and four coedge links to the selected physical curves. The live journal and
the snapshot independently bind the same cap planes and side tags to the saved
operation. Both original geometry parts re-emit byte for byte in memory.

| Retained evidence | SHA-256                                                            |
| ----------------- | ------------------------------------------------------------------ |
| Generic history   | `59ad9f6782fa2e6702e885761863d692bc0e15f5830e713fc1735a4baf4a8cf2` |
| Generic snapshot  | `9102b2fb417b268b0ff1446e1429774b6f4cf634e58c8ab895aafd189977ebb1` |
| Compact V2 state  | `c10329e35264b5862fd031b8023d5189d6ba815b23b25d2e398ca78462c4ecbe` |

Five wire-valid variants exercise disagreement between the matrices, a
different origin datum, the wrong dimension axis, and a changed physical
curve in each section. The public strict read reports
`Unsupported native Fusion FusionSketchLinearDim.constraintType` for the
original YZ archive. Partial reading retains the complete archive. The public
Fusion writer emits zero bytes for the internal research projection, including
after its read-only marker is removed and strict reprojection runs.

Fusion 2706.1.17 supplied the same-process observations. Fresh Fusion process
reopening with explicit load diagnostics, verified live relation participants
and complete dimension targets, and inspected edit and restore results remain
open. The archived SOLIDWORKS receipt additionally records its incomplete
dimension targets. The offline evidence covers this saved metric YZ case.
The hosted archive check pins the process report SHA-256
`941c644135992ecfc2226769e4beae569f60870c0b1af6af739114b12ccd5b49`.

```sh
uv run --frozen --no-default-groups --extra dev --python 3.14 python -B \
  re/automation/FusionDatumPrism/VerifyDatumPrism.py
```
