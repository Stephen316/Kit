from dataclasses import dataclass as MakeDataClass
from typing import Generic
from convert.formats.Fusion.GraphicsCodec.Model.Values.FieldValue import FieldValue
from convert.formats.Fusion.GraphicsCodec.Model.Values.KSetValue import KSetValue


@MakeDataClass(frozen=True, slots=True)
class GraphicAttr(Generic[KSetValue]):
    ClassName: str
    Priority: int
    WinTies: bool
    Fields: tuple[FieldValue[KSetValue], ...]
