from __future__ import annotations
from typing import TYPE_CHECKING

from convert.formats.Fusion.GraphicsCodec.Model.Values.PathEntity import PathEntity
from convert.formats.Fusion.GraphicsCodec.Model.Values.NodeTarget import NodeTarget

if TYPE_CHECKING:
    from convert.formats.Fusion.GraphicsCodec.Wire.SceneCodec import SceneCodec


def XferTargetMut(State: SceneCodec, Value: NodeTarget | None) -> NodeTarget:
    if State.IsFlag(Value is not None and Value.ExternalRef is not None):
        Target = Value.ExternalRef if Value else None
        ObjectId = State.Integer(Target.ObjectId if Target else None, ">Q")
        SegmentId = State.Integer(Target.SegmentId if Target else None)
        Result = NodeTarget(PathEntity(SegmentId, ObjectId))
    else:
        NodeRef = State.TextValue(Value.NodeRef if Value else None)
        State.NodeLinks.add(NodeRef)
        Result = NodeTarget(None, NodeRef)
    State.CheckResult(Value, Result)
    return Result
