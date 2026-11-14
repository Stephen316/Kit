from __future__ import annotations
from typing import TYPE_CHECKING
from convert.formats.Fusion.GraphicsCodec.Nodes.XferBrepMut import XferBrepMut
from convert.formats.Fusion.GraphicsCodec.Nodes.XferLodMut import XferLodMut
from convert.formats.Fusion.GraphicsCodec.Nodes.XferNodeLinkMut import XferNodeLinkMut

from convert.formats.Fusion.GraphicsCodec.Model.Nodes.SketchWorld import SketchWorld

if TYPE_CHECKING:
    from convert.formats.Fusion.GraphicsCodec.Wire.SceneCodec import SceneCodec


def XferSketchMut(State: SceneCodec, Value: SketchWorld | None) -> SketchWorld:
    FaceBody = (
        XferBrepMut(State, Value.FaceBody if Value else None)
        if State.IsFlag(Value is not None and Value.FaceBody is not None)
        else None
    )
    LodCount = State.CountValue(len(Value.Nodes) if Value else None, "<i")
    RegularCount = State.CountValue(len(Value.RegularNodes) if Value else None, "<i")
    Nodes = tuple(
        XferLodMut(State, Value.Nodes[Index] if Value else None)
        for Index in range(LodCount)
    )
    RegularNodes = tuple(
        XferNodeLinkMut(State, Value.RegularNodes[Index] if Value else None)
        for Index in range(RegularCount)
    )
    NoCullingCount = State.CountValue(
        len(Value.NoCullingNodes) if Value else None, "<i"
    )
    NoCullingNodes = tuple(
        XferNodeLinkMut(State, Value.NoCullingNodes[Index] if Value else None)
        for Index in range(NoCullingCount)
    )
    return SketchWorld(FaceBody, Nodes, RegularNodes, NoCullingNodes)
