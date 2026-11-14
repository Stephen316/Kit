from __future__ import annotations
from typing import TYPE_CHECKING
from math import isfinite as IsFinite
from struct import unpack as UnpackValue
from convert.formats.Fusion.GraphicsCodec.Geometry.VertexStride import VertexStride
from convert.formats.Fusion.GraphicsCodec.Geometry.PackVertices import PackVertices

from convert.formats.Fusion.GraphicsCodec.Model.Values.VertexData import VertexData
from convert.formats.Fusion.GraphicsCodec.Model.Values.VertexFormat import VertexFormat

if TYPE_CHECKING:
    from convert.formats.Fusion.GraphicsCodec.Wire.SceneCodec import SceneCodec


def XferVerticesMut(State: SceneCodec, Value: VertexData | None) -> VertexData:
    DynamicFlag = State.IsFlag(Value.DynamicFlag if Value else None)
    FormatRef = State.LinkedObject("VertexFormat", Value.FormatRef if Value else None)
    if FormatRef is None:
        raise ValueError("Graphics vertices require an explicit vertex format")
    FormatValue = State.ObjectValues[FormatRef]
    if not isinstance(FormatValue, VertexFormat):
        raise ValueError("Graphics vertex format has an incompatible class")
    WidthValue = VertexStride(FormatValue)
    if State.Integer(1, "<i") != 1:
        raise ValueError("Unsupported multiple graphics vertex streams")
    StreamIndex = State.Integer(Value.StreamIndex if Value else None, "<i")
    ByteOffset = State.Integer(Value.ByteOffset if Value else None, "<i")
    ByteLength = State.Integer(
        len(Value.Values) * WidthValue * 4 if Value else None, "<i"
    )
    if not 0 < ByteLength <= 67108864 or ByteLength % (4 * WidthValue):
        raise ValueError("Incomplete graphics vertex buffer")
    Format = "<" + "f" * (ByteLength // 4)
    Payload = PackVertices(Value, WidthValue, Format)
    Encoded = State.MeshData.Transfer(StreamIndex, ByteOffset, ByteLength, Payload)
    Numbers = tuple(float(Number) for Number in UnpackValue(Format, Encoded))
    if not all(IsFinite(Number) for Number in Numbers):
        raise ValueError("Nonfinite graphics vertex")
    Values = tuple(
        Numbers[Index : Index + WidthValue]
        for Index in range(0, len(Numbers), WidthValue)
    )
    return VertexData(DynamicFlag, FormatRef, StreamIndex, ByteOffset, Values)
