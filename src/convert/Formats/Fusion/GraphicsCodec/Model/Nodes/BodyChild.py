from dataclasses import dataclass as MakeDataClass
from convert.Formats.Fusion.GraphicsCodec.Model.Nodes.NodePayload import NodePayload


# body child needs an explicit state contract so display geometry retains its entity and scene relationships
@MakeDataClass(frozen=True, slots=True)
class BodyChild:
    Matrix: tuple[float, ...] | None
    NodeData: NodePayload
