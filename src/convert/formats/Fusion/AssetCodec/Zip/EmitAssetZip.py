# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from io import BytesIO
from struct import pack as PackValue

from convert.formats.Fusion.AssetCodec.Zip.PlanZipRows import PlanZipRows
from convert.formats.Fusion.AssetCodec.Zip.ZipAssetRow import ZipAssetRow
from convert.formats.Fusion.AssetCodec.Zip.ZipHeaders import (
    WriteCentralMut,
    WriteLocalMut,
)
from convert.formats.Fusion.AssetCodec.Zip.ZstdRaw import WriteZstdMut


# ordered members form a deterministic single disk zip envelope without native tooling
def EmitAssetZip(Members: tuple[ZipAssetRow, ...]) -> bytes:
    Records = PlanZipRows(Members)
    Output = BytesIO()
    for RowValue in Records:
        WriteLocalMut(Output, RowValue)
        if RowValue.UseZstd:
            WriteZstdMut(Output, RowValue.Data)
        else:
            Output.write(RowValue.Data)
    Central = Output.tell()
    for RowValue in Records:
        WriteCentralMut(Output, RowValue)
    Count = len(Records)
    Output.write(
        PackValue(
            "<I4H2IH",
            0x06054B50,
            0,
            0,
            Count,
            Count,
            Output.tell() - Central,
            Central,
            0,
        )
    )
    return Output.getvalue()
