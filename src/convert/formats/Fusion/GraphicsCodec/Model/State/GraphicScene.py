from dataclasses import dataclass as MakeDataClass
from convert.formats.Fusion.GraphicsCodec.Model.State.SceneGlobals import SceneGlobals
from convert.formats.Fusion.GraphicsCodec.Model.Nodes.SceneWorld import SceneWorld
from convert.formats.Fusion.GraphicsCodec.Model.State.SceneObject import SceneObject
from convert.formats.Fusion.GraphicsCodec.Model.State.GraphicsStream import (
    GraphicsStream,
)


@MakeDataClass(frozen=True, slots=True)
class GraphicScene:
    Globals: SceneGlobals
    RootWorld: SceneWorld
    Objects: tuple[SceneObject, ...]
    MeshSlack: tuple[GraphicsStream, ...] = ()
    FusionSlack: tuple[GraphicsStream, ...] = ()
