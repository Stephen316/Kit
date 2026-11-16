<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# A12 SOLIDWORKS preview wrappers

The research writer can now encode both generation-19000 preview members from
caller-owned image data. `EncodeDib` takes a positive width and height,
256 RGB colors and top-down palette indices. It writes a length-prefixed
bottom-up RLE8 DIB. `EncodePng` takes a separate top-down RGBA raster and
pixel density. It writes a standard sRGB PNG datastream.
[Preview constructors](../../../../../../re/solidworks/WriterResearch/PartPreviews.py)

The eight P03 files have 1420 × 710 indexed DIBs and 640 × 480 RGBA images.
The read-only analysis reached EOF in all eight DIB command streams and
verified every PNG chunk CRC and uncompressed scanline extent. The digest
of source archive hashes and paired preview hashes is
`58e800f573b900c94a1fb040778afcd5803485109579a6bae0a24824475040b3`.
The hosted check reads these exact archive members and verifies output
decoding with independent colored rows, a DIB run longer than 255 pixels
and PNG alpha and resolution values. Compression packetization can differ
while preserving the decoded raster. Hosted verification remains pending.
[Native boundaries](../../../../../../re/solidworks/WriterResearch/PreviewStreams.md)
[Hosted archive verification](../../../../../../re/solidworks/WriterResearch/VerifyPartPreviews.py)

The rectangle writer still needs its own rendering and palette assignment
to supply both rasters. Neither preview uses source image data in the
constructors. The measured thumbnail fallback also makes joint preview
omission a candidate for controlled native verification. The existing
generation-19000 licensed campaign retained both previews.
[Licensed omission scope](../SolidWorksArchiveOmissions.md)
