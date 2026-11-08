# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import FrozenInstanceError
from io import BytesIO
from struct import pack as Pack
from zipfile import ZIP_STORED, ZipFile

import pytest as Pytest
from pytest import MonkeyPatch as PatchContext

from convert.formats.Fusion.ArchiveRead.IndexedArchive import OpenFusionArchive
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
            Result[Local + 8 : Local + 10] = Pack("<H", 93)
            Result[Central + 10 : Central + 12] = Pack("<H", 93)
    return bytes(Result)


# a single central index serves lazy body reads and immutable member descriptions
def TestSharedIndex(MonkeyPatch: PatchContext) -> None:
    Packed, BulkData = SharedZip()
    Calls = []

    # count validation at the real index boundary without replacing its behavior
    def CountIndex(Entries):
        Calls.append(1)
        return IndexZipItems(Entries)

    MonkeyPatch.setattr(
        "convert.formats.Fusion.ArchiveRead.IndexedArchive.IndexZipItems", CountIndex
    )
    with OpenFusionArchive(Packed) as Session:
        assert not Session.ReadNames
        with ZipFile(BytesIO(Packed)) as Archive:
            for Fact, Entry in zip(Session.Members, Archive.infolist(), strict=True):
                assert (
                    Fact.Name,
                    Fact.HeaderOffset,
                    Fact.Size,
                    Fact.CompressedSize,
                    Fact.Method,
                    Fact.Crc,
                    Fact.Flags,
                    Fact.IsDirectory,
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
            Session.Members[0].Name = "changed"
        assert Session.ReadDesign()[0] == BulkData
        assert Session.ReadBody(KTestBody) == b"body bytes"
        with Pytest.raises(ValueError, match="oversized"):
            Session.ReadMember(KOtherMember, 5)
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
        Session.ReadBody(KTestBody)


# a supplied codec remains lazy and repeated requests retain no inflated body cache
def TestLazyCodec() -> None:
    Packed, BulkData = SharedZip()
    Reads = []

    # stored bytes let the test identify exactly which compressed input reached the callback
    def Inflate(Contents: bytes, SizeValue: int) -> bytes:
        assert len(Contents) == SizeValue
        Reads.append(Contents)
        return Contents

    with OpenFusionArchive(WithCodec(Packed), Inflate) as Session:
        assert not Reads
        assert Session.ReadDesign()[0] == BulkData
        assert len(Reads) == 2
        assert (
            Session.ReadBody(KTestBody) == Session.ReadBody(KTestBody) == b"body bytes"
        )
        assert Reads[2:] == [b"body bytes", b"body bytes"]
        assert KOtherMember not in Session.ReadNames


# body corruption remains recoverable and never enters the successful member set
def TestCodecFailure() -> None:
    Packed, BulkData = SharedZip()

    # corruption is isolated to the body so prior design reads should remain usable
    def Corrupt(Contents: bytes, SizeValue: int) -> bytes:
        return bytes(SizeValue) if Contents == b"body bytes" else Contents

    with OpenFusionArchive(WithCodec(Packed), Corrupt) as Session:
        assert Session.ReadDesign()[0] == BulkData
        with Pytest.raises(ValueError, match="size or CRC"):
            Session.ReadBody(KTestBody)
        assert KHistoryPrefix + KTestBody not in Session.ReadNames


# auxiliary codec failures are reported as recoverable proof errors
def TestAuxFailure() -> None:
    Packed, _ = SharedZip()

    # a caller supplied codec may fail before returning any member bytes
    def FailCodec(Contents: bytes, SizeValue: int) -> bytes:
        raise OSError("auxiliary codec failure")

    with OpenFusionArchive(WithCodec(Packed), FailCodec) as Session:
        with Pytest.raises(ValueError, match="Unreadable Fusion archive member"):
            Session.ReadMember(KOtherMember, 6)
        assert not Session.ReadNames


# standalone callers keep distinct error contracts and the tighter body limit
def TestArchiveErrors() -> None:
    with Pytest.raises(ValueError, match="Invalid Fusion ZIP archive"):
        ReadDesignZip(b"broken")
    with Pytest.raises(ValueError, match="Unreadable Fusion body history stream"):
        ReadBodyBlob(b"broken", KTestBody, None)
    with Pytest.raises(ValueError, match="Invalid Fusion body history reference"):
        ReadBodyBlob(b"broken", f"../{KTestBody}", None)
    Packed, _ = SharedZip()
    Modified = bytearray(Packed)
    with ZipFile(BytesIO(Packed)) as Archive:
        NameData = (KHistoryPrefix + KTestBody).encode("ascii")
        Central = Packed.index(NameData, Archive.start_dir) - 46
        Modified[Central + 24 : Central + 28] = Pack("<I", 8 * 1024 * 1024 + 1)
    with Pytest.raises(
        ValueError, match="Missing or oversized Fusion body history stream"
    ):
        ReadBodyBlob(bytes(Modified), KTestBody, None)
