from __future__ import annotations
from typing import TYPE_CHECKING
from dataclasses import replace as ReplaceValue
from convert.formats.Fusion.GraphicsCodec.Fields.XferSetBaseMut import XferSetBaseMut
from convert.formats.Fusion.GraphicsCodec.Fields.XferChildSetMut import XferChildSetMut

from convert.formats.Fusion.GraphicsCodec.Model.Values.SceneSet import SceneSet
from convert.formats.Fusion.GraphicsCodec.Model.Values.EntityRef import EntityRef

if TYPE_CHECKING:
    from convert.formats.Fusion.GraphicsCodec.Wire.SceneCodec import SceneCodec


def XferSetMut(State: SceneCodec, Value: SceneSet | None) -> SceneSet:
    SetKind = State.Integer(Value.SetKind if Value else None, "<i")
    if SetKind in (0, 1):
        Result = SceneSet(SetKind)
    elif SetKind in (2, 3):
        Result = XferSetBaseMut(State, Value, SetKind)
        if SetKind == 3:
            ExternalRef, NodeRef = None, None
            if State.IsFlag(Value is not None and Value.ExternalRef is not None):
                Target = Value.ExternalRef if Value else None
                ObjectId = State.Integer(Target.ObjectId if Target else None, ">Q")
                SegmentId = State.Integer(Target.SegmentId if Target else None)
                ExternalRef = EntityRef(SegmentId, ObjectId)
            else:
                NodeRef = State.TextValue(Value.NodeRef if Value else None)
                State.NodeLinks.add(NodeRef)
            Count = State.CountValue(len(Value.ChildSets) if Value else None, "<i")
            Children = tuple(
                XferChildSetMut(State, Value.ChildSets[Index] if Value else None)
                for Index in range(Count)
            )
            Result = ReplaceValue(
                Result, ExternalRef=ExternalRef, NodeRef=NodeRef, ChildSets=Children
            )
    else:
        raise ValueError("Unsupported graphics attribute set")
    State.CheckResult(Value, Result)
    return Result
