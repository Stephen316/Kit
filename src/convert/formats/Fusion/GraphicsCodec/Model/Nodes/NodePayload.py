from dataclasses import dataclass as MakeDataClass
from convert.formats.Fusion.GraphicsCodec.Model.Nodes.NodeValue import NodeValue


@MakeDataClass(frozen=True, slots=True)
class NodePayload:
    Selector: int
    DataValue: NodeValue | None
    IsXref: bool | None = None
    ActEntity: int | None = None
    InstanceId: int | None = None
