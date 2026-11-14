from __future__ import annotations
from typing import TYPE_CHECKING
from convert.formats.Fusion.GraphicsCodec.Geometry.XferMeshMut import XferMeshMut

from convert.formats.Fusion.GraphicsCodec.Model.Values.SimpleMesh import SimpleMesh
from convert.formats.Fusion.GraphicsCodec.Model.Values.FatPoint import FatPoint

if TYPE_CHECKING:
    from convert.formats.Fusion.GraphicsCodec.Wire.SceneCodec import SceneCodec


def XferGeometryMut(
    State: SceneCodec, Value: SimpleMesh | FatPoint | None
) -> SimpleMesh | FatPoint | None:
    if not State.IsFlag(Value is not None):
        return None
    KindValue = "FatPointMesh" if isinstance(Value, FatPoint) else "OgsSimpleMesh"
    ClassName = State.TextValue(KindValue)
    if ClassName == "OgsSimpleMesh":
        return XferMeshMut(State, Value if isinstance(Value, SimpleMesh) else None)
    if ClassName == "FatPointMesh":
        Current = Value if isinstance(Value, FatPoint) else None
        Width = State.Integer(Current.Width if Current else None, "<i")
        Height = State.Integer(Current.Height if Current else None, "<i")
        BoxSize = State.Vector(Current.BoxSize if Current else None, 3)
        return FatPoint(Width, Height, BoxSize)
    raise ValueError("Unsupported graphics geometry class")
