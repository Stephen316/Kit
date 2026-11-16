from pytest import mark as TestMarks

from convert.Formats.Fusion.EntityCodec.DecodeEntities import DecodeEntities
from convert.Formats.Fusion.EntityCodec.EncodeEntities import EncodeEntities
from convert.Formats.Fusion.SegmentCodec.EmitSegment import EmitSegment
from tests.Convert.Formats.FusionCodec.Entities.ReadNative import ReadNative
from tests.Convert.Formats.FusionCodec.Entities.ReadProfile import ReadProfile


# the native graph contract needs boundary coverage so stored document relationships remain consistent
@TestMarks.parametrize(
    "FileName,ExpectedCount",
    (("circle_sketch.f3d", 246), ("extrude_07mm.f3d", 289), ("extrude_13mm.f3d", 289)),
)
def TestNativeGraph(FileName: str, ExpectedCount: int) -> None:
    Native = ReadNative(FileName)
    Profile = ReadProfile(Native.Targets)
    Values = DecodeEntities(Native.Records, Native.Metadata.Classes, Profile)
    assert len(Values) == ExpectedCount
    assert any(Record.Frame.Metadata for Record in Values)
    assert any(not Record.IsPrimary for Record in Values)
    assert any(Record.Frame.RootId for Record in Values if Record.IsPrimary)
    Rebuilt = EncodeEntities(Values, Native.Metadata.Classes, Profile)
    BulkData, MetaData = EmitSegment(Native.Metadata, Rebuilt)
    assert BulkData == Native.BulkData
    assert MetaData == Native.MetaData
