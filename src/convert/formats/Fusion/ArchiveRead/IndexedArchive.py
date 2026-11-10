# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager as ManageContext
from io import BytesIO
from zipfile import BadZipFile, ZipFile, ZipInfo

from convert.formats.Fusion.ArchiveRead.ArchiveBounds import CheckZipTailMut
from convert.formats.Fusion.ArchiveRead.ArchiveMember import ArchiveMember
from convert.formats.Fusion.ArchiveRead.ReadDesignPair import (
    KDesignPrefix as KDesignPrefix,
)
from convert.formats.Fusion.ArchiveRead.ReadDesignPair import ReadDesignPair
from convert.formats.Fusion.BulkSpans import ReadBulkSpans
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.Topology.BodyAsmMap import KAsmName
from convert.formats.Fusion.ZipItems import IndexZipItems
from convert.formats.Fusion.ZipStream import ReadFusionItem

# body maps name exact same asset history members
KHistoryPrefix = (
    KDesignPrefix.removesuffix("FusionDesignSegmentType1/") + "Breps.BlobParts/"
)

# history evidence uses a stricter bound than general archive members
KMaxAsmSize = 8 * 1024 * 1024


# raw method ninety three decoding needs the next local entry even for directories
def IndexZipEnds(Entries: Mapping[str, ZipInfo], CentralOffset: int) -> dict[int, int]:
    Offsets = sorted(Member.header_offset for Member in Entries.values())
    Following = Offsets[1:] + [CentralOffset]
    return {
        Offset: min(Boundary, CentralOffset)
        for Offset, Boundary in zip(Offsets, Following, strict=True)
    }


# all projection readers share one bounded zip index while leaving unrelated members lazy
class IndexedArchive:
    __slots__ = (
        "DataValue",
        "ZipValue",
        "Codec",
        "Entries",
        "Boundaries",
        "Facts",
        "ReadSet",
    )

    # indexed entry facts preserve source evidence without retaining inflated cache bytes
    def __init__(
        self,
        DataValue: bytes,
        ZipValue: ZipFile,
        InflateZstd: Callable[[bytes, int], bytes] | None,
    ) -> None:
        super().__init__()
        self.DataValue, self.ZipValue = DataValue, ZipValue
        self.Codec = InflateZstd
        self.Entries = IndexZipItems(ZipValue.infolist())
        self.Boundaries = (
            IndexZipEnds(self.Entries, ZipValue.start_dir)
            if InflateZstd is not None
            else {}
        )
        self.Facts: tuple[ArchiveMember, ...] | None = None
        self.ReadSet: set[str] = set()

    # ledger callers only receive immutable central directory snapshots
    @property
    def Members(self) -> tuple[ArchiveMember, ...]:
        if self.Facts is None:
            self.Facts = tuple(
                ArchiveMember(
                    Member.filename,
                    Member.header_offset,
                    Member.file_size,
                    Member.compress_size,
                    Member.compress_type,
                    Member.CRC,
                    Member.flag_bits,
                    Member.is_dir(),
                )
                for Member in self.Entries.values()
            )
        return self.Facts

    # structural indexing is separate from successful decompression of individual members
    @property
    def ReadNames(self) -> frozenset[str]:
        return frozenset(self.ReadSet)

    # the internal reader records only successful bounded decompressions
    def ReadEntryMut(self, Member: ZipInfo) -> bytes:
        return LoadZipEntryMut(self, Member)

    # proof readers can examine an exact auxiliary member within their own tighter bound
    def ReadMember(self, Name: str, Maximum: int) -> bytes:
        return ReadZipMember(self, Name, Maximum)

    # design decoding checks both mandatory streams before interpreting record spans
    def ReadDesign(self) -> tuple[bytes, tuple[RecordSpan, ...]]:
        BulkData, MetaData = ReadDesignPair(self.Entries, self.ReadEntryMut)
        return BulkData, ReadBulkSpans(BulkData, MetaData)

    # body lookups keep current mapping validation and recoverable decode errors
    def ReadBody(self, FileName: str) -> bytes:
        return ReadZipBody(self, FileName)


# the read ledger records a member only after bounded decompression succeeds
def LoadZipEntryMut(Archive: IndexedArchive, Member: ZipInfo) -> bytes:
    if Archive.ZipValue.fp is None:
        raise ValueError("Fusion ZIP session is closed")
    Value = ReadFusionItem(
        Archive.DataValue,
        Archive.ZipValue,
        Archive.Entries,
        Member,
        Archive.Codec,
        Boundary=Archive.Boundaries.get(Member.header_offset),
    )
    Archive.ReadSet.add(Member.filename)
    return Value


# proof readers can apply their own upper bound to an exact archive member
def ReadZipMember(Archive: IndexedArchive, NameValue: str, Maximum: int) -> bytes:
    Member = Archive.Entries.get(NameValue)
    if (
        Member is None
        or Member.is_dir()
        or type(Maximum) is not int
        or not 0 <= Member.file_size <= Maximum
    ):
        raise ValueError("Missing or oversized Fusion archive member")
    try:
        return Archive.ReadEntryMut(Member)
    except (BadZipFile, OSError, RuntimeError) as ErrorInfo:
        raise ValueError("Unreadable Fusion archive member") from ErrorInfo


# body lookup accepts only bounded indexed history streams and normalizes read failures
def ReadZipBody(Archive: IndexedArchive, FileName: str) -> bytes:
    if KAsmName.fullmatch(FileName) is None:
        raise ValueError("Invalid Fusion body history reference")
    try:
        Member = Archive.Entries.get(KHistoryPrefix + FileName)
        if Member is None or Member.is_dir() or not 0 < Member.file_size <= KMaxAsmSize:
            raise ValueError("Missing or oversized Fusion body history stream")
        return Archive.ReadEntryMut(Member)
    except (BadZipFile, OSError, NotImplementedError, RuntimeError) as ErrorInfo:
        raise ValueError("Unreadable Fusion body history stream") from ErrorInfo


# source projection owns the zip lifetime across design and lazy body lookups
@ManageContext
def OpenFusionZip(
    DataValue: bytes, InflateZstd: Callable[[bytes, int], bytes] | None = None
) -> Iterator[IndexedArchive]:
    Source = BytesIO(DataValue)
    try:
        DeclaredCount = CheckZipTailMut(Source, 0)
    except ValueError as ErrorInfo:
        raise ValueError(f"Invalid Fusion ZIP archive: {ErrorInfo}") from ErrorInfo
    try:
        Archive = ZipFile(Source)
    except BadZipFile as ErrorInfo:
        raise ValueError("Invalid Fusion ZIP archive") from ErrorInfo
    except NotImplementedError as ErrorInfo:
        raise ValueError(
            "Fusion ZIP Zstandard requires a compatible codec"
        ) from ErrorInfo
    with Archive:
        if len(Archive.infolist()) != DeclaredCount:
            raise ValueError("Fusion ZIP central directory entry count disagrees")
        yield IndexedArchive(DataValue, Archive, InflateZstd)
