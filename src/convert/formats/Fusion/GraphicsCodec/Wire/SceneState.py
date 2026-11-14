from convert.formats.Fusion.GraphicsCodec.Model.State.GraphicScene import GraphicScene
from convert.formats.Fusion.GraphicsCodec.Model.State.GraphicsStream import (
    GraphicsStream,
)
from convert.formats.Fusion.GraphicsCodec.Model.State.KObjectValue import KObjectValue
from convert.formats.Fusion.GraphicsCodec.Model.State.SceneGlobals import SceneGlobals
from convert.formats.Fusion.GraphicsCodec.Model.Values.ObjectRef import ObjectRef
from convert.formats.Fusion.GraphicsCodec.Wire.SceneWire import SceneWire
from convert.formats.Fusion.GraphicsCodec.Wire.MeshStreams import MeshStreams


class SceneState(SceneWire):
    def __init__(
        self,
        Payload: bytes | None,
        Streams: tuple[GraphicsStream, ...],
        FusionStreams: tuple[GraphicsStream, ...],
        Scene: GraphicScene | None,
    ) -> None:
        super().__init__(Payload)
        self.MeshData = MeshStreams(
            Streams, self.IsReading, Scene.MeshSlack if Scene else ()
        )
        self.FusionData = MeshStreams(
            FusionStreams, self.IsReading, Scene.FusionSlack if Scene else ()
        )
        self.Globals: SceneGlobals | None = Scene.Globals if Scene else None
        self.HasGlobals = False
        self.InputObjects = (
            {Entry.Reference: Entry.Value for Entry in Scene.Objects} if Scene else {}
        )
        self.ObjectValues: dict[ObjectRef, KObjectValue] = {}
        self.ObjectKinds: dict[str, str] = {}
        self.NodeLinks: set[str] = set()
        self.ActiveNode: str | None = None
        self.Depth = 0
        if Scene and len(self.InputObjects) != len(Scene.Objects):
            raise ValueError("Duplicate graphics object definitions")

    def CheckResult(self, Value: object, Result: object) -> None:
        if not self.IsReading and Value != Result:
            raise ValueError(
                "Graphics model contains unsupported or inconsistent fields"
            )

    def ClassVersion(self, ClassName: str) -> int:
        if self.Globals is None:
            raise ValueError("Graphics class precedes its serializer version")
        return dict(self.Globals.Versions)[ClassName]
