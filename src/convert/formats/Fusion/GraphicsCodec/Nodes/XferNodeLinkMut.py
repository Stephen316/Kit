from __future__ import annotations
from typing import TYPE_CHECKING
from convert.formats.Fusion.GraphicsCodec.Model.Nodes.PrimitiveLod import PrimitiveLod
from convert.formats.Fusion.GraphicsCodec.Nodes.XferPrimLodMut import (
    XferPrimLodMut,
)
from convert.formats.Fusion.GraphicsCodec.Model.Values.ObjectRef import ObjectRef

if TYPE_CHECKING:
    from convert.formats.Fusion.GraphicsCodec.Wire.SceneCodec import SceneCodec


def XferNodeLinkMut(
    State: SceneCodec, Value: ObjectRef | PrimitiveLod | None
) -> ObjectRef | PrimitiveLod | None:
    if not State.IsFlag(Value is not None):
        return None
    ClassName = State.TextValue(
        "PrimitiveLODGeometryNode"
        if isinstance(Value, PrimitiveLod)
        else Value.ClassName if Value else None
    )
    if ClassName not in (
        "GroupNode",
        "GeometryNode",
        "FTextNode",
        "PrimitiveLODGeometryNode",
    ):
        raise ValueError("Unsupported linked graphics node class")
    if ClassName == "PrimitiveLODGeometryNode":
        return XferPrimLodMut(State, Value if isinstance(Value, PrimitiveLod) else None)
    return State.ObjectValue(ClassName, Value if isinstance(Value, ObjectRef) else None)
