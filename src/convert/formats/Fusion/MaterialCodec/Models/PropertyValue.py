from dataclasses import dataclass as MakeDataClass
from typing import TypeAlias

from convert.formats.Fusion.MaterialCodec.Models.AssetLinks import AssetLinks
from convert.formats.Fusion.MaterialCodec.Models.ColorValue import ColorValue
from convert.formats.Fusion.MaterialCodec.Models.UnitValue import UnitValue

KScalarValue: TypeAlias = None | str | bool | int | float | UnitValue | ColorValue
KMaterialValue: TypeAlias = KScalarValue | tuple[KScalarValue, ...]


@MakeDataClass(frozen=True, slots=True)
class PropertyValue:
    FieldName: str
    Value: KMaterialValue
    Connections: AssetLinks | None = None
