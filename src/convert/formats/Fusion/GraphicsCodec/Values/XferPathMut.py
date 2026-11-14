from __future__ import annotations
from typing import TYPE_CHECKING

from convert.formats.Fusion.GraphicsCodec.Model.Values.PathEntity import PathEntity
from convert.formats.Fusion.GraphicsCodec.Model.Values.NodePath import NodePath

if TYPE_CHECKING:
    from convert.formats.Fusion.GraphicsCodec.Wire.SceneCodec import SceneCodec


def XferPathMut(State: SceneCodec, Value: NodePath | None) -> NodePath:
    Count = State.CountValue(len(Value.Entries) if Value else None)
    Entries: list[PathEntity] = []
    for Index in range(Count):
        Target = Value.Entries[Index] if Value else None
        SegmentId = State.Integer(Target.SegmentId if Target else None)
        ObjectId = State.Integer(Target.ObjectId if Target else None, ">Q")
        Entries.append(PathEntity(SegmentId, ObjectId))
    Result = NodePath(tuple(Entries))
    State.CheckResult(Value, Result)
    return Result
