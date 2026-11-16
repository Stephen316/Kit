from dataclasses import dataclass as MakeDataClass
from typing import Generic
from convert.Formats.Fusion.GraphicsCodec.Model.Values.FieldValue import FieldValue
from convert.Formats.Fusion.GraphicsCodec.Model.Values.KSetValue import KSetValue


# graphic attribute needs an explicit state contract so display geometry retains its entity and scene relationships
@MakeDataClass(frozen=True, slots=True)
class GraphicAttr(Generic[KSetValue]):
    ClassName: str
    Priority: int
    WinTies: bool
    Fields: tuple[FieldValue[KSetValue], ...]
