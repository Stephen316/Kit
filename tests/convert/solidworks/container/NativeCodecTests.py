# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from io import BytesIO
from pathlib import Path as FilePath
from struct import pack as PackBytes, pack_into as PackInto, unpack_from as UnpackFrom
from pytest import mark as TestMark, raises as RaisesError
from convert.adapters.solidworks.core.Adapter import ReadSldprt, WriteSldprt
from convert.adapters.solidworks.container.Container import BuildSldprt, SldprtArchive
from convert.adapters.solidworks.container.SldprtFormat import SldprtFormat
from tests.convert.solidworks.container.CodecFixture import CodecFixture

KSample = FilePath(__file__).parents[4] / "examples" / ".SLDPRT" / "example.SLDPRT"


@TestMark.parametrize("Version", (3, 4))
def TestVersionRead(Version: int) -> None:
    Original = ReadSldprt(KSample)
    Streams = SldprtArchive.open(KSample).streams
    Fixture = CodecFixture(Streams, Version)
    Document = ReadSldprt(Fixture)
    assert Document.feature_timeline == Original.feature_timeline
    assert Document.sketches == Original.sketches
    assert Document.parameters == Original.parameters
    assert Document.brep_payloads == Original.brep_payloads
    Output = BytesIO()
    _ = WriteSldprt(Document, Output)
    assert Output.getvalue() == Fixture
    assert ReadSldprt(Output.getvalue()).feature_timeline == Original.feature_timeline


@TestMark.parametrize("Version", (3, 4))
def TestVersionSave(Version: int) -> None:
    Streams = SldprtArchive.open(KSample).streams
    Streams["ThirdPty/Codec"] = b"preserved application data"
    Template = CodecFixture(Streams, Version)
    Generated = BuildSldprt(Streams, template=Template)
    assert Generated[4:8] == PackBytes(">I", Version)
    FirstName = next(iter(Streams)).encode("utf-8")
    Expected = bytes(
        ((Value >> Version) | (Value << (8 - Version))) & 255 for Value in FirstName
    )
    assert Generated[38 : 38 + len(Expected)] == Expected
    FolderOffset = UnpackFrom("<I", Generated, len(Generated) - 6)[0] + 8
    assert Generated[FolderOffset + 46 : FolderOffset + 46 + len(Expected)] == Expected
    Document = ReadSldprt(Generated)
    assert Document.feature_timeline == ReadSldprt(KSample).feature_timeline
    assert SldprtArchive.from_bytes(Generated).streams == Streams
    Override = BuildSldprt(Streams, template=Template, format_version=7 - Version)
    assert Override[7] == 7 - Version
    assert ReadSldprt(Override).parameters == Document.parameters


def TestNestedFrame() -> None:
    Streams = SldprtArchive.open(KSample).streams
    Nested = CodecFixture({"swXmlContents/KeyWords": b"not the document history"})
    Streams["ThirdPty/Embedded"] = Nested
    Fixture = CodecFixture(Streams)
    Document = ReadSldprt(Fixture)
    assert Document.feature_timeline == ReadSldprt(KSample).feature_timeline
    assert SldprtArchive.from_bytes(Fixture).streams == Streams
    Output = BytesIO()
    _ = WriteSldprt(Document, Output)
    assert Output.getvalue() == Fixture


@TestMark.parametrize("Damage", ("checksum", "size", "trailing", "truncated"))
def TestDamageRead(Damage: str) -> None:
    Streams = SldprtArchive.open(KSample).streams
    Fixture = bytearray(CodecFixture(Streams))
    Archive = SldprtArchive.from_bytes(Fixture)
    Record = Archive.records[0]
    if Damage == "checksum":
        Fixture[Record.payload_offset + 8] ^= 1
    elif Damage == "size":
        PackInto("<I", Fixture, Record.offset + 18, 0)
    elif Damage == "trailing":
        PackInto("<I", Fixture, Record.offset + 14, Record.compressed_size + 4)
    else:
        del Fixture[Record.payload_offset + Record.compressed_size - 1 :]
    with RaisesError(SldprtFormat):
        _ = ReadSldprt(bytes(Fixture))
