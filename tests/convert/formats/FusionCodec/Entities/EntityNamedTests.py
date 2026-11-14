from pytest import raises as ExpectError

from convert.formats.Fusion.EntityCodec.DecodeEntities import DecodeEntities
from convert.formats.Fusion.EntityCodec.EncodeEntities import EncodeEntities
from convert.formats.Fusion.SegmentCodec.EmitSegment import EmitSegment
from tests.convert.formats.FusionCodec.Entities.EditNamed import EditNamed
from tests.convert.formats.FusionCodec.Entities.NamedProfile import NamedProfile
from tests.convert.formats.FusionCodec.Entities.ReadNative import ReadNative
from tests.convert.formats.FusionCodec.Entities.ReadProfile import ReadProfile
from tests.convert.formats.FusionCodec.Entities.ReadRecords import ReadRecords


def TestNamedRefs() -> None:
    Native = ReadNative("extrude_07mm.f3d")
    Profile = NamedProfile(ReadProfile(Native.Targets))
    Before = DecodeEntities(Native.Records, Native.Metadata.Classes, Profile)
    Changed = EditNamed(Before)
    assert Changed != Before
    Written = EncodeEntities(Changed, Native.Metadata.Classes, Profile)
    BulkData, MetaData = EmitSegment(Native.Metadata, Written)
    Reopened = ReadRecords(BulkData, MetaData)
    assert DecodeEntities(Reopened, Native.Metadata.Classes, Profile) == Changed


def TestTargetClass() -> None:
    Native = ReadNative("extrude_07mm.f3d")
    Profile = ReadProfile(Native.Targets)
    Changed = EditNamed(
        DecodeEntities(Native.Records, Native.Metadata.Classes, Profile)
    )
    Incompatible = NamedProfile(Profile, "incompatible-target-class")
    with ExpectError(ValueError, match="target class is incompatible"):
        _ = EncodeEntities(Changed, Native.Metadata.Classes, Incompatible)
