# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from io import BytesIO
from struct import pack as Pack
from zipfile import ZIP_DEFLATED, ZIP_STORED, ZipFile

from pytest import raises as Raises

from convert.formats.Fusion.DesignZip import KDesignPrefix, ReadDesignZip
from tests.convert.formats.FusionIndexTests import IndexFixture


# the synthetic archive exercises the same two active stream names as saved files
def DesignFixture(Method: int) -> tuple[bytes, bytes]:
    BulkValue = Pack("<I3sQ", 3, b"257", 42) + b"x" + Pack("<I3sQ", 3, b"256", 42)
    Buffer = BytesIO()
    with ZipFile(Buffer, "w", compression=Method) as Archive:
        Archive.writestr(KDesignPrefix + "BulkStream.dat", BulkValue)
        Archive.writestr(KDesignPrefix + "MetaStream.dat", IndexFixture())
    return Buffer.getvalue(), BulkValue


# public container decoding must carry the verified payload into record indexing
def TestDesignZip() -> None:
    Packed, Expected = DesignFixture(ZIP_DEFLATED)
    DataValue, Spans = ReadDesignZip(Packed)
    assert DataValue == Expected
    assert [(Span.ObjectId, Span.IsPrimary) for Span in Spans] == [
        (42, True),
        (42, False),
    ]


# legacy runtimes must validate fallback data before handing it to the index
def TestCodecEntry() -> None:
    Packed, Expected = DesignFixture(ZIP_STORED)
    Modified = bytearray(Packed)
    Directory = Packed.index(b"PK\x01\x02")
    with ZipFile(BytesIO(Packed)) as Archive:
        for Member in Archive.infolist():
            Offset = Member.header_offset + 8
            Modified[Offset : Offset + 2] = Pack("<H", 93)
            NameBytes = Member.filename.encode("ascii")
            Central = Packed.index(NameBytes, Directory) - 46
            Modified[Central + 10 : Central + 12] = Pack("<H", 93)

    # this test double isolates container validation from zstandard availability
    def StoredCodec(Contents: bytes, SizeValue: int) -> bytes:
        assert len(Contents) == SizeValue
        return Contents

    assert ReadDesignZip(bytes(Modified), StoredCodec)[0] == Expected

    # same length corruption must fail the crc check even when the codec returns bytes
    def CorruptCodec(Contents: bytes, SizeValue: int) -> bytes:
        return bytes(SizeValue)

    with Raises(ValueError, match="size or CRC"):
        ReadDesignZip(bytes(Modified), CorruptCodec)
    Modified[30] ^= 1
    with Raises(ValueError, match="local member name differs"):
        ReadDesignZip(bytes(Modified), StoredCodec)


# archive framing errors must be reported before any feature data is returned
def TestMissingMeta() -> None:
    Buffer = BytesIO()
    with ZipFile(Buffer, "w") as Archive:
        Archive.writestr(KDesignPrefix + "BulkStream.dat", b"")
    with Raises(ValueError, match="Missing active Fusion design MetaStream"):
        ReadDesignZip(Buffer.getvalue())
