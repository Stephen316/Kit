from dataclasses import dataclass as MakeDataClass
from convert.formats.Fusion.GraphicsCodec.Model.Values.CacheData import CacheData


@MakeDataClass(frozen=True, slots=True)
class TextureCache:
    IsLayered: bool
    Primary: CacheData
    Secondary: CacheData | None
