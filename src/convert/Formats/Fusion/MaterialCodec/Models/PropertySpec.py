from dataclasses import dataclass as MakeDataClass
from typing import Literal, TypeAlias

# the property kind shape must stay shared so material reconstruction uses one contract for compatible values
KPropertyKind: TypeAlias = Literal[
    "String",
    "URL",
    "Uuid",
    "Integer",
    "Choice",
    "Boolean",
    "Float",
    "Color",
    "Reference",
    "TextureURI",
    "ui",
    "implementation",
]

# the connect mode shape must stay shared so material reconstruction uses one contract for compatible values
KConnectMode: TypeAlias = Literal["none", "single", "multiple"]


# property specification needs an explicit state contract so typed appearance properties retain their native identifiers
@MakeDataClass(frozen=True, slots=True)
class PropertySpec:
    FieldName: str
    ValueKind: KPropertyKind
    IsDefinition: bool = False
    IsReadOnly: bool = False
    IsMultiple: bool = False
    UnitName: str | None = None
    ConnectMode: KConnectMode = "none"
