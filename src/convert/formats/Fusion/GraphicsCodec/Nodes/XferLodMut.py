from __future__ import annotations
from typing import TYPE_CHECKING
from convert.formats.Fusion.GraphicsCodec.Nodes.XferPayloadMut import XferPayloadMut
from convert.formats.Fusion.GraphicsCodec.Geometry.XferGeometryMut import (
    XferGeometryMut,
)
from convert.formats.Fusion.GraphicsCodec.Geometry.XferEdgeMut import XferEdgeMut
from convert.formats.Fusion.GraphicsCodec.Geometry.XferFaceMut import XferFaceMut

from convert.formats.Fusion.GraphicsCodec.Model.Nodes.LodValue import LodValue
from convert.formats.Fusion.GraphicsCodec.Model.Values.EnhancedEdge import EnhancedEdge
from convert.formats.Fusion.GraphicsCodec.Model.Values.EnhancedFace import EnhancedFace
from convert.formats.Fusion.GraphicsCodec.Model.Values.FatPoint import FatPoint
from convert.formats.Fusion.GraphicsCodec.Model.Values.SimpleMesh import SimpleMesh

if TYPE_CHECKING:
    from convert.formats.Fusion.GraphicsCodec.Wire.SceneCodec import SceneCodec

KEdgeItem = 6
KFaceItem = 7


def XferLodMut(State: SceneCodec, Value: LodValue | None) -> LodValue:
    NodeData = XferPayloadMut(State, Value.NodeData if Value else None)
    LodMask = State.Integer(Value.LodMask if Value else None)
    Geometry: SimpleMesh | FatPoint | EnhancedEdge | EnhancedFace | None = None
    if LodMask:
        if LodMask & (LodMask - 1):
            raise ValueError("Unsupported graphics LOD set")
        Current = Value.Geometry if Value else None
        ItemType = State.Integer(
            KEdgeItem
            if isinstance(Current, EnhancedEdge)
            else KFaceItem if isinstance(Current, EnhancedFace) else 0
        )
        if ItemType == KEdgeItem:
            Geometry = XferEdgeMut(
                State, Current if isinstance(Current, EnhancedEdge) else None
            )
        elif ItemType == KFaceItem:
            Geometry = XferFaceMut(
                State, Current if isinstance(Current, EnhancedFace) else None
            )
        elif ItemType == 0:
            Geometry = XferGeometryMut(
                State, Current if isinstance(Current, SimpleMesh | FatPoint) else None
            )
        else:
            raise ValueError("Unsupported graphics display item")
    Bounds = State.Vector(Value.Bounds if Value else None, 6, "<d")
    UseClosest = State.IsFlag(Value.UseClosest if Value else None)
    Result = LodValue(NodeData, LodMask, Geometry, Bounds, UseClosest)
    State.CheckResult(Value, Result)
    return Result
