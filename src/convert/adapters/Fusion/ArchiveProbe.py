# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt


from io import BytesIO
from pathlib import Path as FilePath
from struct import error as StructError
from typing import BinaryIO, cast as CastType
from zipfile import BadZipFile, ZipFile

from convert.adapters.base.ContractTypes import KSourceType
from convert.adapters.base.ProbeResult import ProbeResult
from convert.adapters.Fusion.AdapterInfo import KReaderInfo
from convert.formats.Fusion.ArchiveRead.ArchiveBounds import (
    CheckZipTailMut,
    KArchiveLimit,
)
from convert.adapters.staging.SourceReplay import ReplaySource
from convert.formats.Fusion.DesignZip import KDesignPrefix
from convert.formats.Fusion.ZipItems import IndexZipItems


# discovery validates owned design names without inflating archive members
def CheckDesignMut(Handle: BinaryIO) -> None:
    StartOffset = Handle.tell()
    try:
        DeclaredCount = CheckZipTailMut(Handle, StartOffset)
        with ZipFile(Handle) as Archive:
            Entries = IndexZipItems(Archive.infolist())
            if len(Entries) != DeclaredCount:
                raise ValueError("Fusion ZIP central directory entry count disagrees")
            CentralOffset = Archive.start_dir
            if any(
                not StartOffset <= Entry.header_offset < CentralOffset
                for Entry in Entries.values()
            ):
                raise ValueError("Fusion ZIP member lies outside the source archive")
            for NameValue in ("BulkStream.dat", "MetaStream.dat"):
                Entry = Entries.get(KDesignPrefix + NameValue)
                if Entry is None or Entry.is_dir():
                    raise ValueError(f"Missing active Fusion design {NameValue}")
    finally:
        _ = Handle.seek(StartOffset)


# stream probing only borrows sources that can restore the original position
def ProbeFusion(SourceData: KSourceType) -> ProbeResult:
    FormatId = KReaderInfo.format_id
    try:
        if isinstance(SourceData, (str, FilePath)):
            with FilePath(SourceData).expanduser().open("rb") as Handle:
                CheckDesignMut(Handle)
        elif isinstance(SourceData, (bytes, bytearray)):
            if len(SourceData) > KArchiveLimit:
                raise ValueError("Fusion ZIP exceeds input size limit")
            with BytesIO(SourceData) as Handle:
                CheckDesignMut(Handle)
        elif isinstance(SourceData, ReplaySource):
            CheckDesignMut(CastType(BinaryIO, SourceData))
        else:
            raise ValueError("Fusion probing requires a seekable binary stream")
    except (BadZipFile, OSError, StructError, TypeError, ValueError) as ErrorInfo:
        return ProbeResult(FormatId, 0.0, str(ErrorInfo))
    return ProbeResult(FormatId, 1.0, "Active Fusion design streams in ZIP archive")
