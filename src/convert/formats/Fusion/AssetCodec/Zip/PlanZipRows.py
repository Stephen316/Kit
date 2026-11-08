# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.formats.Fusion.AssetCodec.Zip.PlanZipRow import PlanZipRow
from convert.formats.Fusion.AssetCodec.Zip.ZipAssetRow import ZipAssetRow
from convert.formats.Fusion.AssetCodec.Zip.ZipLimits import (
    KMaxArchiveSize,
    KMaxCentralSize,
    KMaxZipEntries,
)
from convert.formats.Fusion.AssetCodec.Zip.ZipNames import CheckZipPaths
from convert.formats.Fusion.AssetCodec.Zip.ZipPlanRow import ZipPlanRow


# all bounds and paths are checked before allocating the complete output archive
def PlanZipRows(Members: tuple[ZipAssetRow, ...]) -> tuple[ZipPlanRow, ...]:
    if type(Members) is not tuple or not 0 < len(Members) <= KMaxZipEntries:
        raise ValueError("Fusion ZIP entry count exceeds limit")
    Records: list[ZipPlanRow] = []
    LocalSize = 0
    CentralSize = 0
    for Member in Members:
        RowValue = PlanZipRow(Member, LocalSize)
        LocalSize += 30 + len(RowValue.NameBytes) + RowValue.PackedSize
        CentralSize += 46 + len(RowValue.NameBytes)
        if CentralSize > KMaxCentralSize:
            raise ValueError("Fusion ZIP central directory exceeds limit")
        if LocalSize + CentralSize + 22 > KMaxArchiveSize:
            raise ValueError("Fusion ZIP archive exceeds size limit")
        Records.append(RowValue)
    CheckZipPaths(tuple(Member.Name for Member in Members))
    return tuple(Records)
