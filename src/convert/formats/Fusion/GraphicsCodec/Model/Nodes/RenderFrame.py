from dataclasses import dataclass as MakeDataClass
from convert.formats.Fusion.GraphicsCodec.Model.Nodes.NodeValue import NodeValue


@MakeDataClass(frozen=True, slots=True)
class RenderFrame:
    Matrix: tuple[float, ...] | None
    NodeData: NodeValue | None
    HasEmptyLink: bool = False
