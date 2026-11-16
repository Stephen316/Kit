<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Construct the ghost body and attribute type descriptors

The side partition declares 36 active Body fields and seven active attribute-definition fields under `SCH_3701250_37102_13006`. The Body declaration names the base and boundary lattice, mesh, and polyline references, its owner and child links, and the appended scalar and index fields. The attribute-definition declaration introduces 18 logical owner entries. Both declarations include the operation that deletes a base field. [Typed layouts and pinned kernel initializer references](../../../../../../re/solidworks/WriterResearch/Partition/GhostPoint.md#body-definition-and-topology)

The [descriptor writer](../../../../../../re/solidworks/WriterResearch/Partition/GhostSchemas.py) emits the named fields, class references, primitive representations, and declaration boundaries through the existing writer grammar. The [verifier](../../../../../../re/solidworks/WriterResearch/Partition/VerifyGhostSchemas.py) reaches those boundaries through the World, the leading body and the shared `GHOST_REF_BODY_ID_2001` definition. The reconstructed 282-byte Body SHA-256 is `6f9328add817f1bc7e675bbc5acbc33cbdbfd12cbf6b600f46db8f288508bb39`. The 31-byte attribute-definition descriptor SHA-256 is `d2ba400ada2472ff2599b8a469e5a5c0e1214b066aad5115ada2e69ad98be906`.

All five sealed two-pad archives and six independent P01 archives preserve both spans exactly. A different transmit schema is refused. The 3,330-byte report SHA-256 is `1bed1a20827f7231749d6ff9420805244a61f3a1aa656be11f032960f102ea73`. The registered attribute values, list records, and assembly of a complete generated partition remain separate work. [Bound world and body rows](SolidWorksTwoPadGhostBodies.md)
