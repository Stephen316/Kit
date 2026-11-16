<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Construct the two-pad side-partition ghost rows

All five [sealed two-pad saves](../../SolidWorksTwoPadDiscovery.md) carry the same 790-byte `Config-0-GhostPartition` SHA-256 `0009a2da396f871aed29569aa909950677403e4cc28f3abbc6fedba2edd45781`. The existing partition reader reaches one 1,513-byte member in schema `SCH_3701250_37102_13006`. It contains two faceless, isolated points at the origin. Body 3 and shell 8 reach point 9 and vertex 11, then integer slot 13 supplies ghost ID 10002. Body 7 and shell 17 reach point 18 and vertex 20, then slot 21 supplies ID 10001. The two attached attributes share the `GHOST_REF_BODY_ID_2001` definition and bind to the [configured ghost records](SolidWorksTwoPadGhosts.md).

The first point, vertex, and attached attribute in this partition each carry the transport marker. The integer values file in the opposite body order, so the value for ID 10001 carries the first integer marker. The [point, vertex, and integer writer](../../../../../../re/solidworks/WriterResearch/Partition/PointRows.py) accepts the surrounding typed occurrence flags independently. The [attribute writer](../../../../../../re/solidworks/WriterResearch/Partition/AttrRows.py) files the one shared name and each instance separately. The existing single-ghost calls keep the marked defaults.

The [verifier](../../../../../../re/solidworks/WriterResearch/Partition/VerifyTwoPadGhostRows.py) binds the rows through the reciprocal body, vertex, and attribute references. It reproduces all eight owned rows and the shared name in every sealed save. A fresh `(125, −250, 500)` mm point with different slots, owner and ghost ID 10123 yields the four-row SHA-256 `5e7c1e5b4a29e43cb4989b011bc65893e904fd0e0ccbd6b87ad15ed0f495e5d5`. Five invalid controls fail. Six legacy P01 saves reproduce the marked point, vertex, integer and name/attribute fields with aggregate SHA-256 `1ce5f0f0a60dbafde92341ecb0d38a1e38882f9b72cd4a40aae6e9b7f541bf97`.

The 4,632-byte report SHA-256 is `4c9aa602a691916176252b0eb68ee863c597aa3fa754948de88e4c3e016f21db`. Replay requires the original discovery directory and its source, report, authoring and reopen pins. The enclosing partition, remaining typed body and region records, complete generated part and licensed editable acceptance remain separate work.
