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

from convert.formats.Fusion.DesignZip import KDesignPrefix
from convert.formats.Fusion.Topology.BodyAsmMap import KAsmName
from convert.formats.Fusion.ZipItems import IndexZipItems
from convert.formats.Fusion.ZipStream import ReadFusionItem

# initial history evidence must be from the same active asset as the native design
KHistoryPrefix = (
    KDesignPrefix.removesuffix("FusionDesignSegmentType1/") + "Breps.BlobParts/"
)

# only the bounded initial analytic evidence required by named edge picks is read here
KMaxAsmSize = 8 * 1024 * 1024


# the explicit native map names one validated stream rather than a guessed archive ordinal
def ReadBodyBlob(
    DataValue: bytes,
    FileName: str,
    InflateZstd: Callable[[bytes, int], bytes] | None,
) -> bytes:
    if KAsmName.fullmatch(FileName) is None or len(DataValue) > 128 * 1024 * 1024:
        raise ValueError("Invalid Fusion body history reference")
    try:
        with ZipFile(BytesIO(DataValue)) as Archive:
            Members = IndexZipItems(Archive.infolist())
            Member = Members.get(KHistoryPrefix + FileName)
            if (
                Member is None
                or Member.is_dir()
                or not 0 < Member.file_size <= KMaxAsmSize
            ):
                raise ValueError("Missing or oversized Fusion body history stream")
            return ReadFusionItem(DataValue, Archive, Members, Member, InflateZstd)
    except (BadZipFile, OSError, NotImplementedError, RuntimeError) as ErrorInfo:
        raise ValueError("Unreadable Fusion body history stream") from ErrorInfo
