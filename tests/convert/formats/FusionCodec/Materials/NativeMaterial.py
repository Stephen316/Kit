from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.MaterialCodec.Models.MaterialData import MaterialData
from convert.formats.Fusion.MaterialCodec.Models.MaterialSchema import MaterialSchema


@MakeDataClass(frozen=True, slots=True)
class NativeMaterial:
    Streams: MaterialData
    Schemas: tuple[MaterialSchema, ...]
