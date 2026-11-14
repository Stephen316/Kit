from dataclasses import replace as ReplaceValue

from convert.formats.Fusion.MaterialCodec.DecodeMaterials import DecodeMaterials
from convert.formats.Fusion.MaterialCodec.EncodeMaterials import EncodeMaterials
from tests.convert.formats.FusionCodec.Materials.CheckStore import CheckStore
from tests.convert.formats.FusionCodec.Materials.FillPadding import FillPadding
from tests.convert.formats.FusionCodec.Materials.ReadNative import ReadNative


def TestNativePad() -> None:
    Native = ReadNative()
    Padded = ReplaceValue(
        Native.Streams,
        InstanceData=FillPadding(Native.Streams.InstanceData),
        DefinitionData=FillPadding(Native.Streams.DefinitionData),
    )
    Before = DecodeMaterials(Native.Streams, Native.Schemas)
    After = DecodeMaterials(Padded, Native.Schemas)
    assert After == Before
    Regenerated = EncodeMaterials(After, Native.Schemas)
    CheckStore(Regenerated.InstanceData)
    CheckStore(Regenerated.DefinitionData)
