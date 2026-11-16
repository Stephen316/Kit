from dataclasses import dataclass as MakeDataClass
from convert.Formats.Fusion.GraphicsCodec.Model.State.SceneGlobals import SceneGlobals
from convert.Formats.Fusion.GraphicsCodec.Model.Nodes.SceneWorld import SceneWorld
from convert.Formats.Fusion.GraphicsCodec.Model.State.SceneObject import SceneObject
from convert.Formats.Fusion.GraphicsCodec.Model.State.GraphicsStream import (
    GraphicsStream,
)


# graphic scene needs an explicit state contract so display geometry retains its entity and scene relationships
@MakeDataClass(frozen=True, slots=True)
class GraphicScene:
    Globals: SceneGlobals
    RootWorld: SceneWorld
    Objects: tuple[SceneObject, ...]
    MeshSlack: tuple[GraphicsStream, ...] = ()
    FusionSlack: tuple[GraphicsStream, ...] = ()
