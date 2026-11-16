<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# SOLIDWORKS two-pad same-length relation

The A09 research constructor emits the active logical relation of the upper rectangular sketch in the observed generation-19000 two-pad shape. It takes the caller's four directed perimeter lines, the two ordered line identities, and the current sketch's archive allocations. The two operands must be the vertical and horizontal sides of the same square, in that order. Each perimeter line must have its own active axis handle in the current sketch. Projected support and helper members are excluded from this relation.

The constructor shares the existing logical dimension preamble and compact archive allocator. Type 14 has no scalar and owns two local `sgLineHandle` allocations. The writer emits the active collection, both handles, their common relation return, and the six empty logical collections that precede presentation and region records. The existing reader consumes all 125 bytes and reaches the identical post-relation allocation state.

The offline verifier first rechecks the sealed SOLIDWORKS 34.4.1.1011 discovery receipt with its four healthy stock controls and 18 licensed observations. Each input's typed resolved history identifies the upper sketch. The ordered operand identities are independently joined to that sketch in the authored, reopened-before-rebuild, and reopened-after-rebuild snapshots. All five archives match the fresh 125-byte record exactly, with SHA-256 `22d67619cc7b1e71001c1fbdce94a91cdc95ca9fa584804e5a0b73d598b387bd`.

A new 23 mm square with different coordinates, line IDs `22` and `21`, and two fresh archive slots reads back with SHA-256 `8772e8237b672f22d9b1bc2c91dabe755bbaa2612df3a9420436fcd4a2a86241`. The verifier refuses twelve contradictory controls covering duplicate, reversed, parallel, helper, and foreign targets, a duplicate perimeter edge, unequal lengths, forged and prior-sketch handles, a stale sketch, an unsupported generation, and an altered logical return.

Run the verifier with an existing qualified Python environment and the retained private discovery directory.

```powershell
python -B re/solidworks/WriterResearch/TwoPadRelations/VerifyPadEqual.py --run-directory $SealedTwoPadRun
```

The generated record has offline readback evidence. Full two-pad authoring still needs to integrate the [two-atom manager](SolidWorksTwoPadConfigAtoms.md), the source cap's persistent boundary identities, the upper profile's presentation and region records, and the joined result's kernel ownership. Licensed load, rebuild and edit evidence is still required for a generated whole part.
