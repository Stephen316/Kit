from dataclasses import dataclass as MakeDataClass
from convert.formats.Fusion.GraphicsCodec.Model.Values.VertexField import VertexField


@MakeDataClass(frozen=True, slots=True)
class VertexFormat:
    Fields: tuple[VertexField, ...]
