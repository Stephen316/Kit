from __future__ import annotations
from typing import TYPE_CHECKING
from convert.formats.Fusion.GraphicsCodec.Model.State.SceneObject import SceneObject

if TYPE_CHECKING:
    from convert.formats.Fusion.GraphicsCodec.Wire.SceneState import SceneState


def FinishScene(State: SceneState) -> tuple[SceneObject, ...]:
    if not State.HasGlobals:
        raise ValueError("Graphics world has no serializer version declaration")
    if State.IsReading and State.Position != len(State.Payload):
        raise ValueError("Trailing Fusion graphics world bytes")
    if not State.IsReading and set(State.InputObjects) != set(State.ObjectValues):
        raise ValueError("Unreachable graphics object definitions")
    if any(
        State.ObjectKinds.get(Handle) not in ("GroupNode", "GeometryNode", "FTextNode")
        for Handle in State.NodeLinks
    ):
        raise ValueError("Unresolved or incompatible graphics node reference")
    return tuple(
        SceneObject(Reference, Value) for Reference, Value in State.ObjectValues.items()
    )
