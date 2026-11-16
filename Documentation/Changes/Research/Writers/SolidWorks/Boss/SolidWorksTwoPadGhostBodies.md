<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Construct the two-pad ghost world and body records

The [sealed side partition](SolidWorksTwoPadGhostRows.md) uses one World and two faceless body records. The World reaches body 3 and the shared ghost definition. Body 3 points forward to body 7, and body 7 points back to body 3. Each body reaches its own attribute, list, [shell, region and vertex](SolidWorksTwoPadGhostTopology.md). Those topology records, the point and the owned attribute independently account for the saved highest local node ID.

The [body row writer](../../../../../../re/solidworks/WriterResearch/Partition/GhostBodyRows.py) builds the two reciprocal records from distinct allocated graph slots, a caller-supplied node limit and two caller-supplied finite resolution values per body. The existing World writer files the first body link and its independent counters. The verified layout supplies fixed ordinary fields for the witnessed ghost subtype. The surrounding body class descriptor, attribute list contents and partition wrapper remain separate.

The [offline verifier](../../../../../../re/solidworks/WriterResearch/Partition/VerifyTwoPadGhostBodies.py) matches all 201 World bytes and both 89-byte body rows in each of five sealed archives. The 379 reconstructed bytes have SHA-256 `882a20bda3c3bb8b04128161f2bb518680ab33a1ea3e4d6a69a58351e2f062f5`. A fresh World, different graph slots, different node limits and separate resolution values read back with SHA-256 `e5fad6a33a776d399f2afddc724e127cd6e86e4404540eafc5f5ee6796664e2b`. Six invalid allocations, settings and schema inputs fail.

The 2,049-byte sealed report has SHA-256 `459901543c728f55d57f940b5e48d556c9690d5bde28eea385023d02a52050e1`. A complete generated two-pad part and fresh licensed editable acceptance remain open.
