from __future__ import annotations
from typing import TYPE_CHECKING
from convert.formats.Fusion.GraphicsCodec.Model.Nodes.PrimitiveLod import PrimitiveLod
from convert.formats.Fusion.GraphicsCodec.Nodes.XferPayloadMut import XferPayloadMut

if TYPE_CHECKING:
    from convert.formats.Fusion.GraphicsCodec.Wire.SceneCodec import SceneCodec


def XferPrimLodMut(State: SceneCodec, Value: PrimitiveLod | None) -> PrimitiveLod:
    NodeData = XferPayloadMut(State, Value.NodeData if Value else None)
    LodMask = State.Integer(Value.LodMask if Value else None)
    if LodMask and LodMask & (LodMask - 1):
        raise ValueError("Unsupported graphics LOD set")
    Geometry = (
        State.LinkedObject("SimpleMesh", Value.Geometry if Value else None)
        if LodMask
        else None
    )
    Bounds = State.Vector(Value.Bounds if Value else None, 6, "<d")
    UseClosest = State.IsFlag(Value.UseClosest if Value else None)
    Primitive = State.LinkedObject(
        "CircleArc<double>", Value.Primitive if Value else None
    )
    return PrimitiveLod(NodeData, LodMask, Geometry, Bounds, UseClosest, Primitive)
