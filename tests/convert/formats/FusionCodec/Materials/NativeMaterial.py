from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.MaterialCodec.Models.MaterialData import MaterialData
from convert.formats.Fusion.MaterialCodec.Models.MaterialSchema import MaterialSchema


# the native material boundary needs grouped coverage so repository automation cannot silently change its observable contract
@MakeDataClass(frozen=True, slots=True)
class NativeMaterial:
    Streams: MaterialData
    Schemas: tuple[MaterialSchema, ...]
