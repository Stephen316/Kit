from dataclasses import dataclass as MakeDataClass
from convert.formats.Fusion.GraphicsCodec.Model.Nodes.NodePayload import NodePayload


@MakeDataClass(frozen=True, slots=True)
class BodyChild:
    Matrix: tuple[float, ...] | None
    NodeData: NodePayload
