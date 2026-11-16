<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# SOLIDWORKS object exchange database

The ordinary standalone object exchange holds six live records. Its selection-set folder and three principal planes use the same names, tree IDs and update stamps as the generated resolved features. The plane transform transposes the typed native basis into its exchange order and preserves signed zero. The document record carries the observed standalone desktop flags. The table of contents points to the generated UUIDs of the selection folder and three planes. Thirteen saves index Front, Top and Right. The reverse-depth P03 capture indexes Right, Front and Top while the physical datum records retain their original order. [Object writer](../../../../../../re/solidworks/WriterResearch/PartObjectExchange.py)

The MessagePack writer preserves duplicate property keys and each compact scalar, including the separate integer and Boolean fields with the same name. The fresh UnQLite bucket contains all six entries and a zero-filled free tail. The saved capture databases contain a second free block with residual bytes from their allocator state. [MessagePack values](../../../../../../re/solidworks/WriterResearch/ExchangePack.py), [UnQLite allocation](https://github.com/symisc/unqlite/blob/ddb1687036d207bbfc67b98cb470fe52ddf22f62/unqlite.c)

All 84 live key/value records matched byte-for-byte across six P01 and eight P03 captures. The full generated package independently unpacked its exchange member and recovered the same records. The replay SHA-256 is `2a3a7e30bc31defa0f341ac9256856b17c1095baab7a3c0ad97cf5520b793799`. [Receipt-pinned replay](../../../../../../re/solidworks/WriterResearch/VerifyObjectExchangeDb.py), [package construction](SolidWorksPartAssembly.md)

The pinned UnQLite 1.1.9 library independently reopened all 14 generated databases, then a fresh database with new UUIDs. It preserved every record and left each file unchanged. Two contradictory inputs, a repeated datum reference and a reused document UUID, were refused. The independent report SHA-256 is `64717de04fa90f424cbe90863074ffe42c68e345e4acf08659e98d408eb5faca`. Whole-file acceptance still needs a licensed SOLIDWORKS run. [UnQLite cursor API](https://unqlite.symisc.net/c_api_func.html)
