from dataclasses import dataclass as MakeDataClass
from typing import TypeAlias

from convert.Formats.Fusion.MaterialCodec.Models.AssetLinks import AssetLinks
from convert.Formats.Fusion.MaterialCodec.Models.ColorValue import ColorValue
from convert.Formats.Fusion.MaterialCodec.Models.UnitValue import UnitValue

# the scalar value variants need one shared contract so material reconstruction cannot omit a supported value shape
KScalarValue: TypeAlias = None | str | bool | int | float | UnitValue | ColorValue

# the material value variants need one shared contract so material reconstruction cannot omit a supported value shape
KMaterialValue: TypeAlias = KScalarValue | tuple[KScalarValue, ...]


# property value needs an explicit state contract so typed appearance properties retain their native identifiers
@MakeDataClass(frozen=True, slots=True)
class PropertyValue:
    FieldName: str
    Value: KMaterialValue
    Connections: AssetLinks | None = None
