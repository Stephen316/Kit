from dataclasses import dataclass as MakeDataClass
from convert.formats.Fusion.GraphicsCodec.Model.Values.ObjectRef import ObjectRef


# vertex data needs an explicit state contract so display geometry retains its entity and scene relationships
@MakeDataClass(frozen=True, slots=True)
class VertexData:
    DynamicFlag: bool
    FormatRef: ObjectRef
    StreamIndex: int
    ByteOffset: int
    Values: tuple[tuple[float, ...], ...]
