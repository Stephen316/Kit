from __future__ import annotations
from typing import TYPE_CHECKING
from convert.formats.Fusion.GraphicsCodec.Geometry.VertexStride import VertexStride

from convert.formats.Fusion.GraphicsCodec.Model.Values.VertexFormat import VertexFormat
from convert.formats.Fusion.GraphicsCodec.Model.Values.VertexField import VertexField

if TYPE_CHECKING:
    from convert.formats.Fusion.GraphicsCodec.Wire.SceneCodec import SceneCodec


def XferFormatMut(State: SceneCodec, Value: VertexFormat | None) -> VertexFormat:
    Count = State.CountValue(len(Value.Fields) if Value else None, "<i")
    Fields: list[VertexField] = []
    for Index in range(Count):
        Current = Value.Fields[Index] if Value else None
        Fields.append(
            VertexField(
                State.Integer(Current.TypeCode if Current else None, "<i"),
                State.Integer(Current.UsageCode if Current else None, "<i"),
                State.Integer(Current.WordOffset if Current else None, "<i"),
                State.Integer(Current.StreamIndex if Current else None, "<i"),
                State.Integer(Current.UsageIndex if Current else None, "<i"),
                State.Integer(Current.InstanceMode if Current else None, "<i"),
            )
        )
    Result = VertexFormat(tuple(Fields))
    _ = VertexStride(Result)
    return Result
