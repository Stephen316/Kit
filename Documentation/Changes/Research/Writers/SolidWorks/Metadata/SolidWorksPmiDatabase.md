<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# SOLIDWORKS PMI dimension database

The ordinary rectangle contributes two records for its driving width and height. A one-sided blind Boss adds its own depth record. PMI stores each unrounded physical magnitude in metres. The actual extrusion retains the reversal direction independently. The PMI object reference follows the display visual index. The sketch displays use 10 and 11 in dimension-slot order, and the Boss display uses 0. The sketch's driving distance objects carry their own native IDs. [PMI constructor](../../../../../../re/solidworks/WriterResearch/PartPmiDatabase.py), [sketch display writer](../../../../../../re/solidworks/WriterResearch/RectDimDisplay.py), [feature display opening](../../../../../../re/solidworks/WriterResearch/Display/Opening.py)

Five observed initial saves use the full reference with the document title, configuration and standard. Their sketch dimensions carry a two-decimal presentation string. Nine later saves use a local reference and store empty display strings. Both forms retain the same typed driver ownership. Replays include the width, height and depth edits, an inch display control and reversed depth. [Receipt-pinned replay](../../../../../../re/solidworks/WriterResearch/VerifyPmiDatabase.py)

All 14 generated databases and their 36 annotation records match the independently measured source archives byte-for-byte. The replay SHA-256 is `15b6da57b7f543e005f4120c3e5dc0f35c6010479e09f3c778e6497385fe4ae0`. The pinned UnQLite library reopened each generated result and a fresh case with a different title and annotation UUIDs. It also confirmed the distinct driver values in the reopened records. Two malformed inputs were refused. The independent report SHA-256 is `bb0a4b6b79f896aa1a5e659529fbecf1b9d3c10a5bfae4bd0c7b72e11fc96d9c`. [UnQLite cursor API](https://unqlite.symisc.net/c_api_func.html)
