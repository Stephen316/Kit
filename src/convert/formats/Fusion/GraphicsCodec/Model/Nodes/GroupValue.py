from dataclasses import dataclass as MakeDataClass
from convert.formats.Fusion.GraphicsCodec.Model.Nodes.NodePayload import NodePayload
from convert.formats.Fusion.GraphicsCodec.Model.Nodes.SceneWorld import SceneWorld
from convert.formats.Fusion.GraphicsCodec.Model.Nodes.BrepWorld import BrepWorld
from convert.formats.Fusion.GraphicsCodec.Model.Nodes.SketchWorld import SketchWorld


@MakeDataClass(frozen=True, slots=True)
class GroupValue:
    Matrix: tuple[float, ...] | None
    NoCulling: bool
    Bounds: tuple[float, ...] | None
    HasWorld: bool
    WorldKind: int
    WorldValue: SceneWorld | BrepWorld | SketchWorld | None
    NodeData: NodePayload
