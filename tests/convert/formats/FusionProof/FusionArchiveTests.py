# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from dataclasses import FrozenInstanceError
from io import BytesIO
from struct import pack as PackData
from zipfile import ZIP_STORED, ZipFile, ZipInfo

import pytest as Pytest
from pytest import MonkeyPatch as PatchContext

from convert.formats.Fusion.ArchiveRead.IndexedArchive import OpenFusionZip
from convert.formats.Fusion.BodyBlob import KHistoryPrefix, ReadBodyBlob
from convert.formats.Fusion.DesignZip import KDesignPrefix, ReadDesignZip
from convert.formats.Fusion.ZipItems import IndexZipItems
from tests.convert.formats.FusionZipTests import DesignFixture

# the body must be resolved from its exact native name within the active asset
KTestBody = "BREP.00000000-0000-0000-0000-000000000001.smbh"

# an opaque member needs to appear in the index without forcing decompression
KOtherMember = "FusionAssetName[Active]/PrivateData.dat"


# reuse the index fixture so central read behavior is tested independently of feature contents
def SharedZip() -> tuple[bytes, bytes]:
    Packed, BulkData = DesignFixture(ZIP_STORED)
    Buffer = BytesIO(Packed)
    with ZipFile(Buffer, "a") as Archive:
        Archive.writestr(KHistoryPrefix + KTestBody, b"body bytes")
        Archive.writestr(KOtherMember, b"unused")
        Archive.writestr("FusionAssetName[Active]/Unused/", b"")
    return Buffer.getvalue(), BulkData


# marking stored entries with method ninety three isolates codec bounds from library availability
def WithCodec(DataValue: bytes) -> bytes:
    Result = bytearray(DataValue)
    with ZipFile(BytesIO(DataValue)) as Archive:
        for Member in Archive.infolist():
            NameData = Member.filename.encode("ascii")
            Central = DataValue.index(NameData, Archive.start_dir) - 46
            Local = Member.header_offset
            Result[Local + 8 : Local + 10] = PackData("<H", 93)
            Result[Central + 10 : Central + 12] = PackData("<H", 93)
    return bytes(Result)


# a single central index serves lazy body reads and immutable member descriptions
def TestSharedIndex(MonkeyPatch: PatchContext) -> None:
    Packed, BulkData = SharedZip()
    Calls: list[int] = []

    # count validation at the real index boundary without replacing its behavior
    def CountIndex(Entries: list[ZipInfo]) -> dict[str, ZipInfo]:
        Calls.append(1)
        return IndexZipItems(Entries)

    MonkeyPatch.setattr(
        "convert.formats.Fusion.ArchiveRead.IndexedArchive.IndexZipItems", CountIndex
    )
    with OpenFusionZip(Packed) as Session:
        assert not Session.ReadNames
        with ZipFile(BytesIO(Packed)) as Archive:
            for FactValue, Entry in zip(
                Session.Members, Archive.infolist(), strict=True
            ):
                assert (
                    FactValue.Name,
                    FactValue.HeaderOffset,
                    FactValue.Size,
                    FactValue.CompressedSize,
                    FactValue.Method,
                    FactValue.Crc,
                    FactValue.Flags,
                    FactValue.IsDirectory,
                ) == (
                    Entry.filename,
                    Entry.header_offset,
                    Entry.file_size,
                    Entry.compress_size,
                    Entry.compress_type,
                    Entry.CRC,
                    Entry.flag_bits,
                    Entry.is_dir(),
                )
        with Pytest.raises(FrozenInstanceError):
            setattr(Session.Members[0], "Name", "changed")
        assert Session.ReadDesign()[0] == BulkData
        assert Session.ReadBody(KTestBody) == b"body bytes"
        with Pytest.raises(ValueError, match="oversized"):
            _ = Session.ReadMember(KOtherMember, 5)
        assert KOtherMember not in Session.ReadNames
        assert Session.ReadMember(KOtherMember, 6) == b"unused"
        assert Session.ReadNames == frozenset(
            (
                KDesignPrefix + "BulkStream.dat",
                KDesignPrefix + "MetaStream.dat",
                KHistoryPrefix + KTestBody,
                KOtherMember,
            )
        )
    assert Calls == [1]
    with Pytest.raises(ValueError, match="session is closed"):
        _ = Session.ReadBody(KTestBody)


# a supplied codec remains lazy and repeated requests retain no inflated body cache
def TestLazyCodec() -> None:
    Packed, BulkData = SharedZip()
    Reads: list[bytes] = []

    # stored bytes let the test identify exactly which compressed input reached the callback
    def Inflate(Contents: bytes, SizeValue: int) -> bytes:
        assert len(Contents) == SizeValue
        Reads.append(Contents)
        return Contents

    with OpenFusionZip(WithCodec(Packed), Inflate) as Session:
        assert not Reads
        assert Session.ReadDesign()[0] == BulkData
        assert len(Reads) == 2
        assert (
            Session.ReadBody(KTestBody) == Session.ReadBody(KTestBody) == b"body bytes"
        )
        assert Reads[2:] == [b"body bytes", b"body bytes"]
        assert KOtherMember not in Session.ReadNames


# body corruption remains recoverable and never enters the successful member set
def TestCodecError() -> None:
    Packed, BulkData = SharedZip()

    # corruption is isolated to the body so prior design reads should remain usable
    def Corrupt(Contents: bytes, SizeValue: int) -> bytes:
        return bytes(SizeValue) if Contents == b"body bytes" else Contents

    with OpenFusionZip(WithCodec(Packed), Corrupt) as Session:
        assert Session.ReadDesign()[0] == BulkData
        with Pytest.raises(ValueError, match="size or CRC"):
            _ = Session.ReadBody(KTestBody)
        assert KHistoryPrefix + KTestBody not in Session.ReadNames


# auxiliary codec failures are reported as recoverable proof errors
def TestAuxFailure() -> None:
    Packed, _ = SharedZip()

    # a caller supplied codec may fail before returning any member bytes
    def FailCodec(Contents: bytes, SizeValue: int) -> bytes:
        raise OSError("auxiliary codec failure")

    with OpenFusionZip(WithCodec(Packed), FailCodec) as Session:
        with Pytest.raises(ValueError, match="Unreadable Fusion archive member"):
            _ = Session.ReadMember(KOtherMember, 6)
        assert not Session.ReadNames


# standalone callers keep distinct error contracts and the tighter body limit
def TestArchiveErr() -> None:
    with Pytest.raises(ValueError, match="Invalid Fusion ZIP archive"):
        _ = ReadDesignZip(b"broken")
    with Pytest.raises(ValueError, match="Unreadable Fusion body history stream"):
        _ = ReadBodyBlob(b"broken", KTestBody, None)
    with Pytest.raises(ValueError, match="Invalid Fusion body history reference"):
        _ = ReadBodyBlob(b"broken", f"../{KTestBody}", None)
    Packed, _ = SharedZip()
    Modified = bytearray(Packed)
    with ZipFile(BytesIO(Packed)) as Archive:
        NameData = (KHistoryPrefix + KTestBody).encode("ascii")
        Central = Packed.index(NameData, Archive.start_dir) - 46
        Modified[Central + 24 : Central + 28] = PackData("<I", 8 * 1024 * 1024 + 1)
    with Pytest.raises(
        ValueError, match="Missing or oversized Fusion body history stream"
    ):
        _ = ReadBodyBlob(bytes(Modified), KTestBody, None)


# forged directory counts must be rejected before the zip library builds entry objects
def TestZipBounds(MonkeyPatch: PatchContext) -> None:
    Packed, _ = SharedZip()
    Modified = bytearray(Packed)
    Footer = Modified.rindex(b"PK\x05\x06")
    Modified[Footer + 8 : Footer + 12] = PackData("<2H", 1, 1)

    # construction is forbidden here because the raw directory already proves the input invalid
    def RejectOpen(*Values: object, **Keywords: object) -> None:
        raise AssertionError(
            "ZIP construction must follow central directory validation"
        )

    MonkeyPatch.setattr(
        "convert.formats.Fusion.ArchiveRead.IndexedArchive.ZipFile", RejectOpen
    )
    with Pytest.raises(ValueError, match="entry count disagrees"):
        _ = ReadDesignZip(bytes(Modified))
