# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from collections.abc import Callable
from io import BytesIO
from zipfile import BadZipFile, ZipFile

from convert.formats.Fusion.BulkSpans import ReadBulkSpans
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.ZipItems import IndexZipItems
from convert.formats.Fusion.ZipStream import ReadFusionItem

# active design names distinguish the model from browser and auxiliary data
KDesignPrefix = "FusionAssetName[Active]/FusionDesignSegmentType1/"


# expose the verified active model without expanding unrelated archive members
def ReadDesignZip(
    DataValue: bytes, InflateZstd: Callable[[bytes, int], bytes] | None = None
) -> tuple[bytes, tuple[RecordSpan, ...]]:
    if len(DataValue) > 128 * 1024 * 1024:
        raise ValueError("Fusion ZIP exceeds input size limit")
    try:
        with ZipFile(BytesIO(DataValue)) as Archive:
            Members = IndexZipItems(Archive.infolist())
            Streams: list[bytes] = []
            for MemberName in ("BulkStream.dat", "MetaStream.dat"):
                Member = Members.get(KDesignPrefix + MemberName)
                if Member is None or Member.is_dir():
                    raise ValueError(f"Missing active Fusion design {MemberName}")
                Streams.append(
                    ReadFusionItem(DataValue, Archive, Members, Member, InflateZstd)
                )
    except BadZipFile as ErrorInfo:
        raise ValueError("Invalid Fusion ZIP archive") from ErrorInfo
    except NotImplementedError as ErrorInfo:
        raise ValueError(
            "Fusion ZIP Zstandard requires a compatible codec"
        ) from ErrorInfo
    BulkData, MetaData = Streams
    return BulkData, ReadBulkSpans(BulkData, MetaData)
