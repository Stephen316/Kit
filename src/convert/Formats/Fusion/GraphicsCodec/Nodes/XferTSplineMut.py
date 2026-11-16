from __future__ import annotations
from typing import TYPE_CHECKING
from convert.Formats.Fusion.GraphicsCodec.Nodes.XferLodsMut import XferLodsMut

from convert.Formats.Fusion.GraphicsCodec.Model.Nodes.BrepWorld import BrepWorld

if TYPE_CHECKING:
    from convert.Formats.Fusion.GraphicsCodec.Wire.SceneCodec import SceneCodec


# transfer t spline needs an explicit validity boundary so display geometry retains its entity and scene relationships
def XferTSplineMut(State: SceneCodec, Value: BrepWorld | None) -> BrepWorld:
    if Value is not None and (Value.EdgeGroup is None or Value.FaceGroup is None):
        raise ValueError("T-spline graphics world needs edge and face groups")
    Result = XferLodsMut(State, Value)
    State.CheckResult(Value, Result)
    return Result
