from dataclasses import replace as ReplaceValue

from pytest import raises as ExpectError

from convert.formats.Fusion.EntityCodec.DecodeEntities import DecodeEntities
from tests.convert.formats.FusionCodec.Entities.ReadNative import ReadNative
from tests.convert.formats.FusionCodec.Entities.ReadProfile import ReadProfile


# the bad version contract needs boundary coverage so stored document relationships remain consistent
def TestBadVersion() -> None:
    Native = ReadNative("extrude_07mm.f3d")
    Profile = ReadProfile(Native.Targets)
    First, *Others = Native.Metadata.Classes
    Classes = (ReplaceValue(First, SchemaVersion=First.SchemaVersion + 1), *Others)
    with ExpectError(ValueError, match="class/version/base"):
        _ = DecodeEntities(Native.Records, Classes, Profile)


# the extra bytes contract needs boundary coverage so stored document relationships remain consistent
def TestExtraBytes() -> None:
    Native = ReadNative("extrude_07mm.f3d")
    Profile = ReadProfile(Native.Targets)
    First, *Others = Native.Records
    Records = (ReplaceValue(First, Payload=First.Payload + b"\0"), *Others)
    with ExpectError(ValueError, match="trailing"):
        _ = DecodeEntities(Records, Native.Metadata.Classes, Profile)
