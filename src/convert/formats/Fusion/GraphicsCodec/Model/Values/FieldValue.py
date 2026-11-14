from dataclasses import dataclass as MakeDataClass
from typing import Generic
from convert.formats.Fusion.GraphicsCodec.Model.Values.ObjectRef import ObjectRef
from convert.formats.Fusion.GraphicsCodec.Model.Values.TextureValue import TextureValue
from convert.formats.Fusion.GraphicsCodec.Model.Values.NodeTarget import NodeTarget
from convert.formats.Fusion.GraphicsCodec.Model.Values.OverrideSet import OverrideSet
from convert.formats.Fusion.GraphicsCodec.Model.Values.KSetValue import KSetValue


@MakeDataClass(frozen=True, slots=True)
class FieldValue(Generic[KSetValue]):
    FieldName: str
    DataValue: (
        bool
        | int
        | float
        | str
        | None
        | tuple[float, ...]
        | TextureValue
        | ObjectRef
        | NodeTarget
        | tuple[OverrideSet[KSetValue], ...]
    )
