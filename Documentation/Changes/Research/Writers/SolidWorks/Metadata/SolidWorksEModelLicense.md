<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# SOLIDWORKS eModel saved package metadata

In SOLIDWORKS `34.4.1.1011`, `SolidStorage_c::SaveEModelsNode` opens
`Contents/eModelLic` at `0x18002817e`, queries
`SldUtils::Licensing::getLicensedPackageType` at `0x1800281cc`, and emits the
selected code through the `su_CArchive` unsigned-long operator at
`0x180028207`. For file generations below 18000 the native writer maps code 8
to 4 before serialization. The research constructor accepts an explicit
caller-owned package code for the measured generation 19000 and code 4.
[Constructor](../../../../../../re/solidworks/WriterResearch/PartEModelLicense.py)

The separate `uiModelDoc_c::saveDocument` calls the same getter at
`0x49734952`, applies the same version condition, and assigns the result to
`moHeader_c::setLicenseFlag` at `0x49734998`. The typed `Header2` license
flag therefore provides an independent input to the archive replay. The
distinct header license type was 2 in those same saves.
[Header2 field ownership](../../../../../../re/solidworks/WriterResearch/ModelHeader.md)

The licensed `doccplu.dll` SHA-256 is
`120e1d5c359f5895d9785325995ebfaafc790ef7d74fe4fb0e242303f933939b`.
The `slduiu.dll` SHA-256 is
`88a8d1bff1e8d7b5cad7e456096c4e32c8d84d4046fc5c09ce26f2563ee8e2a6`.

All six P01 and eight P03 archives reproduced the complete four-byte member
from their independent header flags. The aggregate replay SHA-256 is
`a37825fa376f5180478bb8d8735d9d13d4fc917a55bf87481eec6fb1ae975824`.
Four unsupported contexts were refused. This evidence covers the member
constructor. Whole-file native acceptance remains separate.
[Archive replay](../../../../../../re/solidworks/WriterResearch/VerifyEModelLicense.py)
