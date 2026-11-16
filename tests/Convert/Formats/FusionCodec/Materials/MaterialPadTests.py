from dataclasses import replace as ReplaceValue

from convert.Formats.Fusion.MaterialCodec.DecodeMaterials import DecodeMaterials
from convert.Formats.Fusion.MaterialCodec.EncodeMaterials import EncodeMaterials
from tests.Convert.Formats.FusionCodec.Materials.CheckStore import CheckStore
from tests.Convert.Formats.FusionCodec.Materials.FillPadding import FillPadding
from tests.Convert.Formats.FusionCodec.Materials.ReadNative import ReadNative


# the native pad contract needs boundary coverage so stored document relationships remain consistent
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
