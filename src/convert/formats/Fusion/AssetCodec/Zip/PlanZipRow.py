# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from typing import cast as CastValue
from zlib import crc32 as CrcValue

from convert.formats.Fusion.AssetCodec.Zip.ZipAssetRow import ZipAssetRow
from convert.formats.Fusion.AssetCodec.Zip.ZipLimits import KMaxMemberBytes
from convert.formats.Fusion.AssetCodec.Zip.ZipNames import EncodeZipName
from convert.formats.Fusion.AssetCodec.Zip.ZipPlanRow import ZipPlanRow
from convert.formats.Fusion.AssetCodec.Zip.ZstdRaw import ZstdFrameSize


# validated entry facts make malformed directory rows and oversized frames impossible
def PlanZipRow(Member: ZipAssetRow, Offset: int) -> ZipPlanRow:
    if (
        not isinstance(CastValue(object, Member), ZipAssetRow)
        or type(Member.Data) is not bytes
        or type(Member.UseZstd) is not bool
    ):
        raise ValueError("Invalid Fusion ZIP member")
    NameBytes = EncodeZipName(Member.Name)
    if NameBytes.endswith(b"/") and (Member.Data or Member.UseZstd):
        raise ValueError("Fusion ZIP directories must be empty and stored")
    DataSize = len(Member.Data)
    if DataSize > KMaxMemberBytes:
        raise ValueError("Fusion ZIP member exceeds size limit")
    PackedSize = ZstdFrameSize(DataSize) if Member.UseZstd else DataSize
    if PackedSize > KMaxMemberBytes:
        raise ValueError("Fusion ZIP encoded member exceeds size limit")
    return ZipPlanRow(
        NameBytes,
        Member.Data,
        Member.UseZstd,
        Offset,
        PackedSize,
        CrcValue(Member.Data),
    )
