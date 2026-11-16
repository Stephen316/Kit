from __future__ import annotations
from collections.abc import Callable
from convert.Formats.Fusion.GraphicsCodec.Wire.SceneState import SceneState
from convert.Formats.Fusion.GraphicsCodec.Wire.FinishScene import FinishScene
from convert.Formats.Fusion.GraphicsCodec.Model.State.GraphicScene import GraphicScene
from convert.Formats.Fusion.GraphicsCodec.Model.State.GraphicsStream import (
    GraphicsStream,
)
from convert.Formats.Fusion.GraphicsCodec.Model.Values.ObjectRef import ObjectRef
from convert.Formats.Fusion.GraphicsCodec.Model.State.SceneObject import SceneObject
from convert.Formats.Fusion.GraphicsCodec.Model.Values.OverrideSet import OverrideSet
from convert.Formats.Fusion.GraphicsCodec.Model.Values.SceneSet import SceneSet


# the scene codec contract needs a dedicated boundary so display geometry retains its entity and scene relationships
class SceneCodec(SceneState):

    # scene codec needs explicit initial state so display geometry retains its entity and scene relationships
    def __init__(
        self,
        Payload: bytes | None,
        Streams: tuple[GraphicsStream, ...],
        FusionStreams: tuple[GraphicsStream, ...],
        Scene: GraphicScene | None,
        ObjectHook: Callable[[SceneCodec, str, ObjectRef | None], ObjectRef],
        OverrideHook: Callable[
            [SceneCodec, tuple[OverrideSet[SceneSet], ...] | None],
            tuple[OverrideSet[SceneSet], ...],
        ],
    ) -> None:
        super().__init__(Payload, Streams, FusionStreams, Scene)
        self.ObjectHook = ObjectHook
        self.OverrideHook = OverrideHook

    # the object value contract needs a shared interpretation so display geometry retains its entity and scene relationships
    def ObjectValue(self, ClassName: str, Value: ObjectRef | None) -> ObjectRef:
        return self.ObjectHook(self, ClassName, Value)

    # linked object must resolve unambiguously so display geometry retains its entity and scene relationships
    def LinkedObject(self, ClassName: str, Value: ObjectRef | None) -> ObjectRef | None:
        if not self.IsFlag(Value is not None):
            return None
        self.ExpectText(ClassName)
        return self.ObjectValue(ClassName, Value)

    # the override sets contract needs a shared interpretation so display geometry retains its entity and scene relationships
    def OverrideSets(
        self, Values: tuple[OverrideSet[SceneSet], ...] | None
    ) -> tuple[OverrideSet[SceneSet], ...]:
        return self.OverrideHook(self, Values)

    # the finalize contract needs a shared interpretation so display geometry retains its entity and scene relationships
    def Finalize(self) -> tuple[SceneObject, ...]:
        return FinishScene(self)
