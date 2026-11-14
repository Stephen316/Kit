from convert.formats.Fusion.BrepCodec.Journal.Geometry.CoedgeNode import CoedgeNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.EdgeNode import EdgeNode
from convert.formats.Fusion.BrepCodec.Journal.Planar.BoundaryUse import BoundaryUse
from convert.formats.Fusion.BrepCodec.Journal.Planar.LiveTable import LiveTable
from convert.formats.Fusion.BrepCodec.Journal.Planar.RequireLive import RequireLive
from convert.formats.Fusion.BrepCodec.Journal.Planar.StableRef import StableRef


def ReadBoundary(
    Table: LiveTable, FirstRef: int, LoopRef: int
) -> tuple[BoundaryUse, ...]:
    Current = StableRef(Table, FirstRef)
    FirstRef = Current
    Results: list[BoundaryUse] = []
    SeenRefs: set[int] = set()
    while Current not in SeenRefs:
        SeenRefs.add(Current)
        Coedge = RequireLive(Table, Current, CoedgeNode)
        if StableRef(Table, Coedge.OwnerLoop) != LoopRef:
            raise ValueError("Fusion coedge belongs to another loop")
        Following = RequireLive(Table, Coedge.NextCoedge, CoedgeNode)
        if StableRef(Table, Following.PriorCoedge) != Current:
            raise ValueError("Fusion coedge ring is not reciprocal")
        EdgeValue = RequireLive(Table, Coedge.EdgeRef, EdgeNode)
        Starts, EndVert = EdgeValue.StartVertex, EdgeValue.EndVertex
        if Coedge.Reversed:
            Starts, EndVert = EndVert, Starts
        Results.append(
            BoundaryUse(
                Current,
                StableRef(Table, Coedge.EdgeRef),
                StableRef(Table, Starts),
                StableRef(Table, EndVert),
                StableRef(Table, Coedge.Partner),
            )
        )
        Current = StableRef(Table, Coedge.NextCoedge)
    if Current != FirstRef or len(Results) < 3:
        raise ValueError("Fusion planar face requires one closed polygon")
    for Index, Value in enumerate(Results):
        if Value.EndVertex != Results[(Index + 1) % len(Results)].StartVertex:
            raise ValueError("Fusion planar boundary endpoints do not join")
    return tuple(Results)
