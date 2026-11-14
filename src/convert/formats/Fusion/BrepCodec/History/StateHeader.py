from convert.formats.Fusion.GeometryCodec.EntityRef import EntityRef
from convert.formats.Fusion.GeometryCodec.GeometryValue import KGeometryValue


def MakeStateHead(
    StateId: int, NodeIndex: int, PriorNode: int, NextNode: int
) -> tuple[KGeometryValue, ...]:
    return (
        StateId,
        1,
        0,
        EntityRef(PriorNode),
        EntityRef(NextNode),
        EntityRef(NodeIndex),
        EntityRef(-1),
        EntityRef(0),
        False,
    )
