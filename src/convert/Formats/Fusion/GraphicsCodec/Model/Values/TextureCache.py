from dataclasses import dataclass as MakeDataClass
from convert.Formats.Fusion.GraphicsCodec.Model.Values.CacheData import CacheData


# texture cache needs an explicit state contract so display geometry retains its entity and scene relationships
@MakeDataClass(frozen=True, slots=True)
class TextureCache:
    IsLayered: bool
    Primary: CacheData
    Secondary: CacheData | None
