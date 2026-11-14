from __future__ import annotations
from collections.abc import Callable
from convert.formats.Fusion.GraphicsCodec.Wire.SceneState import SceneState
from convert.formats.Fusion.GraphicsCodec.Wire.FinishScene import FinishScene
from convert.formats.Fusion.GraphicsCodec.Model.State.GraphicScene import GraphicScene
from convert.formats.Fusion.GraphicsCodec.Model.State.GraphicsStream import (
    GraphicsStream,
)
from convert.formats.Fusion.GraphicsCodec.Model.Values.ObjectRef import ObjectRef
from convert.formats.Fusion.GraphicsCodec.Model.State.SceneObject import SceneObject
from convert.formats.Fusion.GraphicsCodec.Model.Values.OverrideSet import OverrideSet
from convert.formats.Fusion.GraphicsCodec.Model.Values.SceneSet import SceneSet


class SceneCodec(SceneState):
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

    def ObjectValue(self, ClassName: str, Value: ObjectRef | None) -> ObjectRef:
        return self.ObjectHook(self, ClassName, Value)

    def LinkedObject(self, ClassName: str, Value: ObjectRef | None) -> ObjectRef | None:
        if not self.IsFlag(Value is not None):
            return None
        self.ExpectText(ClassName)
        return self.ObjectValue(ClassName, Value)

    def OverrideSets(
        self, Values: tuple[OverrideSet[SceneSet], ...] | None
    ) -> tuple[OverrideSet[SceneSet], ...]:
        return self.OverrideHook(self, Values)

    def Finalize(self) -> tuple[SceneObject, ...]:
        return FinishScene(self)
