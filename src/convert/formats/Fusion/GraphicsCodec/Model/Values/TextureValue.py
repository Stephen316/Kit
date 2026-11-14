from dataclasses import dataclass as MakeDataClass
from convert.formats.Fusion.GraphicsCodec.Model.Values.EntityRef import EntityRef
from convert.formats.Fusion.GraphicsCodec.Model.Values.TextureCache import TextureCache


@MakeDataClass(frozen=True, slots=True)
class TextureValue:
    AssetName: str
    Reference: EntityRef
    Cache: TextureCache
