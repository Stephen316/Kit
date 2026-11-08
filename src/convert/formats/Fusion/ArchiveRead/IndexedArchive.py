# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager as ManageContext
from io import BytesIO
from zipfile import BadZipFile, ZipFile, ZipInfo

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

# whole archive inputs have a common byte limit before any central indexing
KMaxZipSize = 128 * 1024 * 1024

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
        self.DataValue = DataValue
        self.ZipValue = ZipValue
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
        if self.ZipValue.fp is None:
            raise ValueError("Fusion ZIP session is closed")
        Value = ReadFusionItem(
            self.DataValue,
            self.ZipValue,
            self.Entries,
            Member,
            self.Codec,
            Boundary=self.Boundaries.get(Member.header_offset),
        )
        self.ReadSet.add(Member.filename)
        return Value

    # proof readers can examine an exact auxiliary member within their own tighter bound
    def ReadMember(self, Name: str, Maximum: int) -> bytes:
        Member = self.Entries.get(Name)
        if (
            Member is None
            or Member.is_dir()
            or type(Maximum) is not int
            or not 0 <= Member.file_size <= Maximum
        ):
            raise ValueError("Missing or oversized Fusion archive member")
        try:
            return self.ReadEntryMut(Member)
        except (BadZipFile, OSError, RuntimeError) as ErrorInfo:
            raise ValueError("Unreadable Fusion archive member") from ErrorInfo

    # design decoding checks both mandatory streams before interpreting record spans
    def ReadDesign(self) -> tuple[bytes, tuple[RecordSpan, ...]]:
        BulkData, MetaData = ReadDesignPair(self)
        return BulkData, ReadBulkSpans(BulkData, MetaData)

    # body lookups keep current mapping validation and recoverable decode errors
    def ReadBody(self, FileName: str) -> bytes:
        if KAsmName.fullmatch(FileName) is None:
            raise ValueError("Invalid Fusion body history reference")
        try:
            Member = self.Entries.get(KHistoryPrefix + FileName)
            if (
                Member is None
                or Member.is_dir()
                or not 0 < Member.file_size <= KMaxAsmSize
            ):
                raise ValueError("Missing or oversized Fusion body history stream")
            return self.ReadEntryMut(Member)
        except (BadZipFile, OSError, NotImplementedError, RuntimeError) as ErrorInfo:
            raise ValueError("Unreadable Fusion body history stream") from ErrorInfo


# source projection owns the zip lifetime across design and lazy body lookups
@ManageContext
def OpenFusionArchive(
    DataValue: bytes, InflateZstd: Callable[[bytes, int], bytes] | None = None
) -> Iterator[IndexedArchive]:
    if len(DataValue) > KMaxZipSize:
        raise ValueError("Fusion ZIP exceeds input size limit")
    try:
        Archive = ZipFile(BytesIO(DataValue))
    except BadZipFile as ErrorInfo:
        raise ValueError("Invalid Fusion ZIP archive") from ErrorInfo
    except NotImplementedError as ErrorInfo:
        raise ValueError(
            "Fusion ZIP Zstandard requires a compatible codec"
        ) from ErrorInfo
    with Archive:
        yield IndexedArchive(DataValue, Archive, InflateZstd)
