from __future__ import annotations
from typing import TYPE_CHECKING
from convert.Formats.Fusion.GraphicsCodec.Worlds.XferGlobalMut import XferGlobalMut
from convert.Formats.Fusion.GraphicsCodec.Worlds.XferWorldMut import XferWorldMut
from convert.Formats.Fusion.GraphicsCodec.Nodes.XferPayloadMut import XferPayloadMut
from convert.Formats.Fusion.GraphicsCodec.Nodes.XferBrepMut import XferBrepMut
from convert.Formats.Fusion.GraphicsCodec.Nodes.XferSketchMut import XferSketchMut
from convert.Formats.Fusion.GraphicsCodec.Nodes.XferTSplineMut import XferTSplineMut

from convert.Formats.Fusion.GraphicsCodec.Model.Nodes.GroupValue import GroupValue
from convert.Formats.Fusion.GraphicsCodec.Model.Nodes.SceneWorld import SceneWorld
from convert.Formats.Fusion.GraphicsCodec.Model.Nodes.BrepWorld import BrepWorld
from convert.Formats.Fusion.GraphicsCodec.Model.Nodes.SketchWorld import SketchWorld

if TYPE_CHECKING:
    from convert.Formats.Fusion.GraphicsCodec.Wire.SceneCodec import SceneCodec


# transfer group needs an explicit validity boundary so display geometry retains its entity and scene relationships
def XferGroupMut(State: SceneCodec, Value: GroupValue | None) -> GroupValue:
    if not State.HasGlobals:
        State.Globals = XferGlobalMut(State, State.Globals)
        State.HasGlobals = True
    Matrix = State.OptionalMat(Value.Matrix if Value else None)
    State.EmptyLinks(3)
    NoCulling = State.IsFlag(Value.NoCulling if Value else None)
    Bounds = (
        None if NoCulling else State.Vector(Value.Bounds if Value else None, 6, "<d")
    )
    HasWorld = State.IsFlag(Value.HasWorld if Value else None)
    WorldKind = 0
    WorldValue: SceneWorld | BrepWorld | SketchWorld | None = None
    Current = Value.WorldValue if Value else None
    if HasWorld:
        WorldKind = State.Integer(Value.WorldKind if Value else None)
        if WorldKind == 0:
            if State.IsFlag(Current is not None):
                WorldValue = XferWorldMut(
                    State, Current if isinstance(Current, SceneWorld) else None
                )
        elif WorldKind == 1:
            WorldValue = XferBrepMut(
                State, Current if isinstance(Current, BrepWorld) else None
            )
        elif WorldKind == 2:
            WorldValue = XferTSplineMut(
                State, Current if isinstance(Current, BrepWorld) else None
            )
        elif WorldKind == 3:
            WorldValue = XferSketchMut(
                State, Current if isinstance(Current, SketchWorld) else None
            )
        else:
            raise ValueError("Unsupported custom graphics world")
    NodeData = XferPayloadMut(State, Value.NodeData if Value else None)
    Result = GroupValue(
        Matrix, NoCulling, Bounds, HasWorld, WorldKind, WorldValue, NodeData
    )
    State.CheckResult(Value, Result)
    return Result
