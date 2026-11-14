from __future__ import annotations
from typing import TYPE_CHECKING
from typing import cast as CastValue
from struct import pack as PackValue, unpack as UnpackValue

from convert.formats.Fusion.GraphicsCodec.Model.Values.IndexData import IndexData

if TYPE_CHECKING:
    from convert.formats.Fusion.GraphicsCodec.Wire.SceneCodec import SceneCodec


def XferIndicesMut(State: SceneCodec, Value: IndexData | None) -> IndexData:
    DynamicFlag = State.IsFlag(Value.DynamicFlag if Value else None)
    StreamIndex = State.Integer(Value.StreamIndex if Value else None, "<i")
    ByteOffset = State.Integer(Value.ByteOffset if Value else None, "<i")
    ByteLength = State.Integer(
        len(Value.Values) * (2 if Value.IsShort else 4) if Value else None, "<i"
    )
    WidthFlag = State.Integer(int(Value.IsShort) if Value else None, "<i")
    if WidthFlag not in (0, 1):
        raise ValueError("Unsupported graphics index width")
    IsShort = bool(WidthFlag)
    WidthValue = 2 if IsShort else 4
    if not 0 < ByteLength <= 67108864 or ByteLength % WidthValue:
        raise ValueError("Incomplete graphics index buffer")
    Format = "<" + ("H" if IsShort else "I") * (ByteLength // WidthValue)
    if Value is not None and (
        type(CastValue(object, Value.IsShort)) is not bool
        or any(type(Number) is not int for Number in Value.Values)
    ):
        raise ValueError("Expected integer graphics indices")
    Payload = PackValue(Format, *Value.Values) if Value else None
    Encoded = State.MeshData.Transfer(StreamIndex, ByteOffset, ByteLength, Payload)
    return IndexData(
        DynamicFlag,
        StreamIndex,
        ByteOffset,
        IsShort,
        tuple(int(Number) for Number in UnpackValue(Format, Encoded)),
    )
