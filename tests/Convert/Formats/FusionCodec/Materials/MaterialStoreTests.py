from dataclasses import replace as ReplaceValue

from pytest import mark as TestMarks
from pytest import raises as ExpectError

from convert.Formats.Fusion.MaterialCodec.DecodeMaterials import DecodeMaterials
from tests.Convert.Formats.FusionCodec.Materials.CorruptStore import CorruptStore
from tests.Convert.Formats.FusionCodec.Materials.ReadNative import ReadNative


# the broken store contract needs boundary coverage so stored document relationships remain consistent
@TestMarks.parametrize(
    "Failure", ("cycle", "length", "flags", "root", "outside", "partial", "unattached")
)
def TestBrokenStore(Failure: str) -> None:
    Native = ReadNative()
    Broken = ReplaceValue(
        Native.Streams, InstanceData=CorruptStore(Native.Streams.InstanceData, Failure)
    )
    with ExpectError(ValueError):
        _ = DecodeMaterials(Broken, Native.Schemas)
