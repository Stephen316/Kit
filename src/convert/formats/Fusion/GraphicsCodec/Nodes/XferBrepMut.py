from __future__ import annotations
from typing import TYPE_CHECKING
from convert.formats.Fusion.GraphicsCodec.Nodes.XferLodsMut import XferLodsMut

from convert.formats.Fusion.GraphicsCodec.Model.Nodes.BrepWorld import BrepWorld

if TYPE_CHECKING:
    from convert.formats.Fusion.GraphicsCodec.Wire.SceneCodec import SceneCodec


def XferBrepMut(State: SceneCodec, Value: BrepWorld | None) -> BrepWorld:
    if State.IsFlag(Value is not None and Value.EdgeGroup is not None):
        Result = XferLodsMut(State, Value)
    else:
        ModelBox = (
            State.Vector(Value.ModelBox if Value else None, 6, "<d")
            if State.IsFlag(Value is not None and Value.ModelBox is not None)
            else None
        )
        Result = BrepWorld(None, (), None, (), ModelBox)
    State.CheckResult(Value, Result)
    return Result
