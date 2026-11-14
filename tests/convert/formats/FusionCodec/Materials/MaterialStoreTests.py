from dataclasses import replace as ReplaceValue

from pytest import mark as TestMarks
from pytest import raises as ExpectError

from convert.formats.Fusion.MaterialCodec.DecodeMaterials import DecodeMaterials
from tests.convert.formats.FusionCodec.Materials.CorruptStore import CorruptStore
from tests.convert.formats.FusionCodec.Materials.ReadNative import ReadNative


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
