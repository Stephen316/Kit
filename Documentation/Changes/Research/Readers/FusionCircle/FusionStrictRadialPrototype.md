<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Fusion radial strict read

The packaged strict Fusion reader reads a sketch-only XY circle with one owned radius or diameter dimension. It uses the two version-zero schemas verified on the four historical discovery controls and their original Fusion 2705.1.30 measurements. The previous strict baseline `f601764c407daea48c3c22ba20aee92de6807a25` refused both dimension classes. [Historical archive evidence](FusionCircularDimensionEvidence.md), [strict disk projection](../../../../../src/convert/adapters/Fusion/Native/Circular/ProjectDisk.py)

The graph follows dimension 234 to circle 230 and checks the link back to sketch 202. Model parameter 235, dynamic parameter 236, update record 237 and sketch feature 207 must agree by typed identity. The parameter table and its name index must point to the same model parameter. The archived dimension and model parameter must agree about driving mode, expression and value. The typed radius, center, layout plane and measurement point also match the circle carrier. The four controls project independent literal dimensions of 17 mm diameter or 14 mm radius with their respective driving or reference roles. [Typed graph reader](../../../../../src/convert/adapters/Fusion/Native/Circular/ReadRadialBinding.py), [radial projection](../../../../../src/convert/adapters/Fusion/Native/Circular/ProjectRadial.py)

The existing strict circle and saved ASM sheet checks verify the curve, ownership, profile membership and closure. The archive replay produces and reads ten temporary in-memory mutations per control. It verifies refusals for the circle operand, dimension parent, parameter and feature links, update owner, driving flag, cached radius, binding value and allocation. Both existing strict unconstrained controls retain their original neutral JSON digests. The new strict neutral documents round-trip through JSON. Native export refuses the radial projection even when the caller supplies native-state metadata.

The original capture recorded no live profile-loop inventory or native curve evaluator bounds. A separate licensed Fusion 2706.1.17 run later opened and recomputed the same four pinned archives with two healthy controls. It reported one XY profile with one outer loop and one curve before and after recompute. The loop member and dimension resolved to the same owned circle. Both evaluators reported a closed full turn from 0 to 2π. The saved Design interval agrees, and the archived ASM edge uses a seam from −π to π. The licensed report gives measurement SHA-256 `2a32f465175331674542ea64a158083917e8f52002979154031e98279325284e` and receipt SHA-256 `a896b2bff32d8f998af25583d868f967e486a0602db790a4149c6b912df23e64`. The collector and raw receipt remain with that operator. Target native authoring still requires its own evidence. [Licensed readback](https://github.com/TryUniCAD/Kit/pull/94#issuecomment-6921804904)

The earlier isolated prototype report had SHA-256 `43587934fae7dd9565c1531a57fc566fd2959137dcd137a4098d772a7eb798c8`. The hosted archive gate now expects the packaged replay SHA-256 `2ccd6f09fa34bd8b04c1f0da349f69610654506998f77166c2a851c4949e476b`. [Archive replay](../../../../../re/automation/FusionStrictRadialPrototype.py), [archive gate](../../../../../tests/Research/Archives/ArchiveEvidenceTests.py)

```sh
uv run --frozen --python 3.14 python -B re/automation/FusionStrictRadialPrototype.py
```
