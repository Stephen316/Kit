from __future__ import annotations
from typing import TYPE_CHECKING
from math import isfinite as IsFinite
from struct import unpack as UnpackValue
from convert.formats.Fusion.GraphicsCodec.Geometry.PackFace import PackFace
from convert.formats.Fusion.GraphicsCodec.Model.Values.EnhancedFace import EnhancedFace

if TYPE_CHECKING:
    from convert.formats.Fusion.GraphicsCodec.Wire.SceneCodec import SceneCodec


def XferFaceMut(State: SceneCodec, Value: EnhancedFace | None) -> EnhancedFace:
    StreamIndex = State.Integer(Value.StreamIndex if Value else None)
    ByteOffset = State.Integer(Value.ByteOffset if Value else None)
    PointCount = State.Integer(len(Value.Points) * 3 if Value else None)
    NormalCount = State.Integer(len(Value.Normals) * 3 if Value else None)
    CoordCount = State.Integer(len(Value.Coords) * 2 if Value else None)
    IndexCount = State.Integer(len(Value.Indices) if Value else None)
    VertexCount = PointCount // 3
    if (
        not 0 < PointCount <= 6291456
        or PointCount % 3
        or NormalCount != PointCount
        or CoordCount != VertexCount * 2
        or not 0 < IndexCount <= 16777216
        or IndexCount % 3
    ):
        raise ValueError("Unsupported graphics enhanced face layout")
    FloatFormat = "<" + "f" * (VertexCount * 8)
    IndexFormat = "<" + "I" * IndexCount
    Payload = PackFace(Value, FloatFormat, IndexFormat)
    Encoded = State.FusionData.Transfer(
        StreamIndex, ByteOffset, VertexCount * 32 + IndexCount * 4, Payload
    )
    Numbers = tuple(
        float(Number)
        for Number in UnpackValue(FloatFormat, Encoded[: VertexCount * 32])
    )
    Indices = tuple(
        int(Number) for Number in UnpackValue(IndexFormat, Encoded[VertexCount * 32 :])
    )
    if not all(IsFinite(Number) for Number in Numbers):
        raise ValueError("Nonfinite graphics enhanced face vertex")
    if any(Number >= VertexCount for Number in Indices):
        raise ValueError("Graphics enhanced face index exceeds its vertices")
    Starts = range(0, len(Numbers), 8)
    Points = tuple(Numbers[Index : Index + 3] for Index in Starts)
    Normals = tuple(Numbers[Index + 3 : Index + 6] for Index in Starts)
    Coords = tuple(Numbers[Index + 6 : Index + 8] for Index in Starts)
    EdgeCount = State.CountValue(len(Value.EdgeIds) if Value else None)
    EdgeIds = tuple(
        State.Integer(Value.EdgeIds[Index] if Value else None)
        for Index in range(EdgeCount)
    )
    Result = EnhancedFace(
        StreamIndex, ByteOffset, Points, Normals, Coords, Indices, EdgeIds
    )
    State.CheckResult(Value, Result)
    return Result
