from __future__ import annotations
from typing import TYPE_CHECKING
from math import isfinite as IsFinite
from struct import unpack as UnpackValue
from convert.formats.Fusion.GraphicsCodec.Geometry.PackEdge import PackEdge
from convert.formats.Fusion.GraphicsCodec.Model.Values.EnhancedEdge import EnhancedEdge

if TYPE_CHECKING:
    from convert.formats.Fusion.GraphicsCodec.Wire.SceneCodec import SceneCodec


def XferEdgeMut(State: SceneCodec, Value: EnhancedEdge | None) -> EnhancedEdge:
    StreamIndex = State.Integer(Value.StreamIndex if Value else None)
    ByteOffset = State.Integer(Value.ByteOffset if Value else None)
    PointCount = State.Integer(len(Value.Points) * 3 if Value else None)
    NormalCount = State.Integer(len(Value.Normals) * 3 if Value else None)
    if not 0 < PointCount <= 8388608 or PointCount % 3 or NormalCount != PointCount:
        raise ValueError("Unsupported graphics enhanced edge layout")
    Format = "<" + "f" * (PointCount * 2)
    Payload = PackEdge(Value, Format)
    Encoded = State.FusionData.Transfer(
        StreamIndex, ByteOffset, PointCount * 8, Payload
    )
    Numbers = tuple(float(Number) for Number in UnpackValue(Format, Encoded))
    if not all(IsFinite(Number) for Number in Numbers):
        raise ValueError("Nonfinite graphics enhanced edge vertex")
    Points = tuple(Numbers[Index : Index + 3] for Index in range(0, len(Numbers), 6))
    Normals = tuple(
        Numbers[Index + 3 : Index + 6] for Index in range(0, len(Numbers), 6)
    )
    Result = EnhancedEdge(StreamIndex, ByteOffset, Points, Normals)
    State.CheckResult(Value, Result)
    return Result
