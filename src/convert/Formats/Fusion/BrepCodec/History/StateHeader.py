from convert.Formats.Fusion.GeometryCodec.EntityRef import EntityRef
from convert.Formats.Fusion.GeometryCodec.GeometryValue import KGeometryValue


# the state head operation needs a consistent construction rule so topology identity survives native history reconstruction
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
