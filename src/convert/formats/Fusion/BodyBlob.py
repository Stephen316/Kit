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

from convert.formats.Fusion.ArchiveRead.IndexedArchive import (
    IndexedArchive,
    KMaxZipSize,
)
from convert.formats.Fusion.ArchiveRead.IndexedArchive import (
    KHistoryPrefix as KHistoryPrefix,
)
from convert.formats.Fusion.ArchiveRead.IndexedArchive import KMaxAsmSize as KMaxAsmSize
from convert.formats.Fusion.Topology.BodyAsmMap import KAsmName


# standalone body lookups retain their own error mapping for bad archive framing
def ReadBodyBlob(
    DataValue: bytes,
    FileName: str,
    InflateZstd: Callable[[bytes, int], bytes] | None,
) -> bytes:
    if KAsmName.fullmatch(FileName) is None or len(DataValue) > KMaxZipSize:
        raise ValueError("Invalid Fusion body history reference")
    try:
        with ZipFile(BytesIO(DataValue)) as Archive:
            return IndexedArchive(DataValue, Archive, InflateZstd).ReadBody(FileName)
    except (BadZipFile, OSError, NotImplementedError, RuntimeError) as ErrorInfo:
        raise ValueError("Unreadable Fusion body history stream") from ErrorInfo
