<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Construct the two-pad ghost and relation managers

All five [sealed two-pad SOLIDWORKS saves](../../SolidWorksTwoPadDiscovery.md) record two inline sketch-point ghosts after the [configured atom manager](SolidWorksTwoPadConfigAtoms.md). The header stores counter 10002 and populated-partition mode 2. The records file IDs 10002 and 10001 in that order. Each uses the ordinary type-20 point header, one unset source ID, and empty inline geometry and points. Neither record allocates an archive object. The following empty relation manager allocates one class and one object before saved detail. [Native serializer ownership](../../../../../../re/solidworks/WriterResearch/ConfigGhostRelation.md)

The [manager writer](../../../../../../re/solidworks/WriterResearch/ConfigGhostRelation.py) keeps the one-point default and takes an explicit count of two for this solved scope. It reuses the same point fields and equation-manager rules for both cases. The [offline verifier](../../../../../../re/solidworks/WriterResearch/TwoPadAtoms/VerifyPadGhosts.py) reconstructs all five 122-byte intervals, including 72 ghost bytes and the 50-byte relation record. The ghost interval SHA-256 is `7750b0bfc03851424dfc6cb8da79068db0d44fb5712358a8d2514b88afd890e2`. The full interval SHA-256 is `7736013093e1077972dc9f88e14e5b18bd03a53038fb0c06d5b2c0b23f965724`.

The independently parsed relation reaches occurrence 61 and the saved detail starts at offset 3384 in all five captures. A fresh map produces the same interval at occurrence 4, and 13 count, partition mode, ownership and payload mutations fail. The sealed run report SHA-256 is `d9623826d1022e748a4c04ae9dee93b81fd2565692266528cd6b35c423431e51`. The unchanged one-point replay covers fourteen P01/P03 saves with SHA-256 `0ba2e2768dbbe1c6bba1e669fdde413b75edba4e4819b4a7f0e17e77ba8fba23`.

The separate ghost-partition stream, complete two-pad package, and licensed editable acceptance remain open.
