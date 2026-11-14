from __future__ import annotations
from typing import TYPE_CHECKING
from typing import cast as CastValue
from convert.formats.Fusion.GraphicsCodec.Values.XferTargetMut import XferTargetMut

from convert.formats.Fusion.GraphicsCodec.Model.Values.NodeTarget import NodeTarget
from convert.formats.Fusion.GraphicsCodec.Model.Values.ObjectRef import ObjectRef
from convert.formats.Fusion.GraphicsCodec.Model.Values.OverrideSet import OverrideSet
from convert.formats.Fusion.GraphicsCodec.Model.Values.SceneSet import SceneSet

if TYPE_CHECKING:
    from convert.formats.Fusion.GraphicsCodec.Wire.SceneCodec import SceneCodec


def XferOverMut(
    State: SceneCodec, WireKind: str, Current: object
) -> ObjectRef | NodeTarget | tuple[OverrideSet[SceneSet], ...] | None:
    if WireKind == "path":
        if Current is not None and not isinstance(Current, ObjectRef):
            raise ValueError("Expected a graphics node path reference")
        return State.LinkedObject("PersistentPassiveNodePath", Current)
    if WireKind == "target":
        if Current is not None and not isinstance(Current, NodeTarget):
            raise ValueError("Expected a graphics override target")
        return XferTargetMut(State, Current)
    if WireKind != "overrides":
        raise ValueError("Unsupported graphics override field descriptor")
    if Current is not None and not isinstance(Current, tuple):
        raise ValueError("Expected graphics override sets")
    return State.OverrideSets(
        CastValue(tuple[OverrideSet[SceneSet], ...] | None, Current)
    )
