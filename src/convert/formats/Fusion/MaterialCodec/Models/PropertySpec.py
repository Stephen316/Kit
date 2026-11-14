from dataclasses import dataclass as MakeDataClass
from typing import Literal, TypeAlias

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
KConnectMode: TypeAlias = Literal["none", "single", "multiple"]


@MakeDataClass(frozen=True, slots=True)
class PropertySpec:
    FieldName: str
    ValueKind: KPropertyKind
    IsDefinition: bool = False
    IsReadOnly: bool = False
    IsMultiple: bool = False
    UnitName: str | None = None
    ConnectMode: KConnectMode = "none"
