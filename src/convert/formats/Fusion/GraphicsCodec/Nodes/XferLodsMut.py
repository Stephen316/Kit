from __future__ import annotations
from typing import TYPE_CHECKING
from convert.formats.Fusion.GraphicsCodec.Nodes.XferChildMut import XferChildMut
from convert.formats.Fusion.GraphicsCodec.Nodes.XferLodMut import XferLodMut
from convert.formats.Fusion.GraphicsCodec.Nodes.AuditItems import AuditItems

from convert.formats.Fusion.GraphicsCodec.Model.Nodes.BrepWorld import BrepWorld

if TYPE_CHECKING:
    from convert.formats.Fusion.GraphicsCodec.Wire.SceneCodec import SceneCodec


def XferLodsMut(State: SceneCodec, Value: BrepWorld | None) -> BrepWorld:
    EdgeGroup = XferChildMut(State, Value.EdgeGroup if Value else None)
    EdgeCount = State.CountValue(len(Value.EdgeNodes) if Value else None)
    EdgeNodes = tuple(
        XferLodMut(State, Value.EdgeNodes[Index] if Value else None)
        for Index in range(EdgeCount)
    )
    FaceGroup = XferChildMut(State, Value.FaceGroup if Value else None)
    FaceCount = State.CountValue(len(Value.FaceNodes) if Value else None)
    FaceNodes = tuple(
        XferLodMut(State, Value.FaceNodes[Index] if Value else None)
        for Index in range(FaceCount)
    )
    AuditItems(EdgeNodes, FaceNodes)
    ModelBox = (
        State.Vector(Value.ModelBox if Value else None, 6, "<d")
        if State.IsFlag(Value is not None and Value.ModelBox is not None)
        else None
    )
    return BrepWorld(EdgeGroup, EdgeNodes, FaceGroup, FaceNodes, ModelBox)
