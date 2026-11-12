# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from collections.abc import Callable
from contextlib import ExitStack

from convert.formats.Fusion.ArchiveRead.ArchiveBounds import KArchiveLimit
from convert.formats.Fusion.ArchiveRead.IndexedArchive import OpenFusionZip
from convert.formats.Fusion.ArchiveRead.IndexedArchive import (
    KHistoryPrefix as HistoryPrefix,
)
from convert.formats.Fusion.ArchiveRead.IndexedArchive import KMaxAsmSize as KMaxAsmSize
from convert.formats.Fusion.Topology.BodyAsmMap import KAsmName

KHistoryPrefix = HistoryPrefix


# standalone body lookups retain their own error mapping for bad archive framing
def ReadBodyBlob(
    DataValue: bytes,
    FileName: str,
    InflateZstd: Callable[[bytes, int], bytes] | None,
) -> bytes:
    if KAsmName.fullmatch(FileName) is None or len(DataValue) > KArchiveLimit:
        raise ValueError("Invalid Fusion body history reference")
    with ExitStack() as Session:
        try:
            Archive = Session.enter_context(OpenFusionZip(DataValue, InflateZstd))
        except (OSError, RuntimeError, ValueError) as ErrorInfo:
            raise ValueError("Unreadable Fusion body history stream") from ErrorInfo
        return Archive.ReadBody(FileName)
