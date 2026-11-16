<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Construct the two-pad ghost shells and regions

The [two-pad side partition](SolidWorksTwoPadGhostRows.md) binds ghost ID 10002 to body 3, shell 8, region 10, and vertex 11. Ghost ID 10001 reaches body 7, shell 17, region 19, and vertex 20. Each vertex names its shell. The shell returns the same vertex and region, and the void region points back to the same body and shell.

The first shell uses the ordinary transport marker. The first void region carries its type-19 descriptor. The later shell and region reuse those declarations. The [ghost topology writer](../../../../../../re/solidworks/WriterResearch/Partition/TopologyRows.py) preserves the single-body defaults and takes each occurrence state independently. Its inputs are the two allocated topology records and their caller-owned graph links. [Original region and shell layout](../../../../../../re/solidworks/WriterResearch/Partition/GhostPoint.md#body-definition-and-topology)

The [offline verifier](../../../../../../re/solidworks/WriterResearch/Partition/VerifyTwoPadGhostTopo.py) joins both physical closure pairs to the configured ghost IDs and reconstructs all four intervals in each of five sealed saves. The first shell and region are 25 and 54 bytes. The second are 24 and 23 bytes. Their concatenated SHA-256 is `bb626717963f7f95734a9afe187b8b2605112097571fa3e0c82f0ca9e003cba6`.

A fresh owner with different graph slots, an unmarked shell, and a defined region reads back with SHA-256 `b728ff3b65908af69863b75529809046a5e8b3a792c31a277fbdab4c39cbebc8`. Four invalid controls fail. Six P01 captures preserve the marked single-body output with aggregate SHA-256 `cbefe0237c82a429b7b90d1c303eb2954c7856398315aae3ba67580fef5159fa`.

The 2,396-byte sealed report has SHA-256 `01d272fbb0626c6d6edd5815350767092b2b168298b7b589ea48e1ba77fa7c8c`. The enclosing body and world records, complete generated part, and licensed editable acceptance remain open.
