from sys import version_info as PythonVersion

from pytest import mark as TestMarks

from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.formats.Fusion.DocumentCodec.Records.EmitDocSegment import EmitDocSegment
from convert.formats.Fusion.DocumentCodec.Records.MakeDocProfile import MakeDocProfile
from convert.formats.Fusion.DocumentCodec.Records.ReadDocSchemas import ReadDocSchemas
from convert.formats.Fusion.DocumentCodec.Records.ReadDocSegment import ReadDocSegment
from tests.convert.formats.FusionCodec.Documents.Reading.NativeDocSource import (
    KNativeSource,
    ReadNativeCore,
)


@TestMarks.skipif(
    PythonVersion < (3, 14), reason="native Fusion fixture requires ZIP Zstandard"
)
def TestNativeGraph() -> None:
    Streams, Metadata = ReadNativeCore()
    Design = Streams[0]
    Profile = MakeDocProfile(ReadDocSchemas(), Metadata, Design.SegmentId)
    Value = ReadDocSegment(Design, Metadata[0], Profile)
    assert len(Value.Records) == 303
    assert sum(Entry.IsPrimary for Entry in Value.Records) == 269
    LineGuid = "DCA267ED-D615-4934-B64F-AD805E8003E2"
    assert (
        sum(
            Group.ClassGuid.upper() == LineGuid
            for Record in Value.Records
            if Record.IsPrimary
            for Group in Record.Groups
        )
        == 4
    )
    assert EmitDocSegment(Value) == Design


@TestMarks.skipif(
    PythonVersion < (3, 14), reason="native Fusion fixture requires ZIP Zstandard"
)
def TestNativeParts() -> None:
    Value = ReadDocument(KNativeSource.read_bytes())
    assert Value.Graphics is not None
    assert len(Value.Graphics.Objects) == 39
    assert len(Value.Segments) == 3
