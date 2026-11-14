from __future__ import annotations
from typing import TYPE_CHECKING
from convert.formats.Fusion.GraphicsCodec.Model.Nodes.PrimitiveLod import PrimitiveLod
from convert.formats.Fusion.GraphicsCodec.Nodes.XferPrimLodMut import (
    XferPrimLodMut,
)

from convert.formats.Fusion.GraphicsCodec.Model.Nodes.SceneWorld import SceneWorld
from convert.formats.Fusion.GraphicsCodec.Model.Values.ObjectRef import ObjectRef

if TYPE_CHECKING:
    from convert.formats.Fusion.GraphicsCodec.Wire.SceneCodec import SceneCodec


def XferWorldMut(
    State: SceneCodec, Value: SceneWorld | None, IsRoot: bool = False
) -> SceneWorld:
    WorldKind = State.TextValue(Value.WorldKind if Value else None)
    if WorldKind not in ("ARenderList", "SingleNodeWorld"):
        raise ValueError("Unsupported graphics world class")
    Revision = State.Integer(Value.RevisionId if Value else None)
    PublishMode = State.Integer(Value.PublishMode if Value else None, "<i")
    if Revision != 5 or PublishMode != 1:
        raise ValueError("Unsupported graphics world revision or publish mode")
    Nodes: list[ObjectRef | PrimitiveLod] = []
    while True:
        Current = (
            Value.Nodes[len(Nodes)] if Value and len(Nodes) < len(Value.Nodes) else None
        )
        ClassName = State.TextValue(
            "PrimitiveLODGeometryNode"
            if isinstance(Current, PrimitiveLod)
            else Current.ClassName if Current else "WorldSerializerEndMark"
        )
        if ClassName == "WorldSerializerEndMark":
            break
        if (
            ClassName
            not in (
                "GroupNode",
                "GeometryNode",
                "FTextNode",
                "PrimitiveLODGeometryNode",
            )
            or len(Nodes) >= 1000000
        ):
            raise ValueError(f"Unsupported world node class or count: {ClassName}")
        if ClassName == "PrimitiveLODGeometryNode":
            Nodes.append(
                XferPrimLodMut(
                    State, Current if isinstance(Current, PrimitiveLod) else None
                )
            )
        else:
            Nodes.append(
                State.ObjectValue(
                    ClassName, Current if isinstance(Current, ObjectRef) else None
                )
            )
    Accelerate = (
        State.IsFlag(Value.Accelerate if Value else None)
        if WorldKind == "ARenderList" and not IsRoot
        else None
    )
    Result = SceneWorld(WorldKind, Revision, PublishMode, tuple(Nodes), Accelerate)
    State.CheckResult(Value, Result)
    return Result
