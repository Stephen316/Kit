from dataclasses import dataclass as MakeDataClass
from convert.formats.Fusion.GraphicsCodec.Model.Values.ObjectRef import ObjectRef


@MakeDataClass(frozen=True, slots=True)
class VertexData:
    DynamicFlag: bool
    FormatRef: ObjectRef
    StreamIndex: int
    ByteOffset: int
    Values: tuple[tuple[float, ...], ...]
