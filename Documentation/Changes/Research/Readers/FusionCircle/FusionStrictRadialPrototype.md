<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Fusion radial strict-read prototype

The offline prototype reads the four historical diameter and radius discovery controls in a separate research process. It pins the exact saved archives and original Fusion 2705.1.30 observations and adds two version-zero schema names for its private graph build. Public strict reads at baseline `f601764c407daea48c3c22ba20aee92de6807a25` still refuse the dimension classes. [Historical archive evidence](FusionCircularDimensionEvidence.md), [prototype replay](../../../../../re/automation/FusionStrictRadialPrototype.py)

The graph follows dimension 234 to circle 230 and checks the link back to sketch 202. Model parameter 235, dynamic parameter 236, update record 237 and sketch feature 207 must agree by typed identity. The same parameter must appear under its native name in the owner component's parameter table. The archived dimension and model parameter must agree about driving mode, expression and value. The typed radius, center, layout plane and measurement point also match the circle carrier. The four controls project independent literal dimensions of 17 mm diameter or 14 mm radius with their respective driving or reference roles. [Typed graph replay](../../../../../re/automation/FusionRadialGraph.py)

The existing strict circle and saved ASM sheet checks verify the curve, ownership, profile membership and closure. The prototype refuses seven separate in-memory changes in each case, covering the dimension parent, circle operand, parameter binding, binding owner, update owner, driving flag and binding value. Both existing strict unconstrained controls produce identical neutral JSON before and after the prototype. The new neutral documents round-trip as unqualified research, and the public Fusion writer and export gate refuse them.

The original capture recorded no live profile-loop inventory or native curve evaluator bounds. A separate licensed Fusion 2706.1.17 run later opened and recomputed the same four pinned archives with two healthy controls. It reported one XY profile with one outer loop and one curve before and after recompute. The loop member and dimension resolved to the same owned circle. Both evaluators reported a closed full turn from 0 to 2π. The saved Design interval agrees, and the archived ASM edge uses a seam from −π to π. The licensed report gives measurement SHA-256 `2a32f465175331674542ea64a158083917e8f52002979154031e98279325284e` and receipt SHA-256 `a896b2bff32d8f998af25583d868f967e486a0602db790a4149c6b912df23e64`. The collector and raw receipt remain with that operator. These observations corroborate the narrow circular read shape. Packaged strict admission and target native authoring require their own evidence. [Licensed readback](https://github.com/TryUniCAD/Kit/pull/94#issuecomment-6921804904)

The hosted archive gate checks the prototype report SHA-256 `43587934fae7dd9565c1531a57fc566fd2959137dcd137a4098d772a7eb798c8`. The original historical report has a separate digest. [Archive gate](../../../../../tests/Research/Archives/ArchiveEvidenceTests.py)

```sh
uv run --frozen --python 3.14 python -B re/automation/FusionStrictRadialPrototype.py
```
