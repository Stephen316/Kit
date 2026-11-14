from convert.formats.Fusion.BrepCodec.Journal.Geometry.EdgeNode import EdgeNode
from convert.formats.Fusion.BrepCodec.Journal.Planar.BoundaryUse import BoundaryUse
from convert.formats.Fusion.BrepCodec.Journal.Planar.FaceBoundary import FaceBoundary
from convert.formats.Fusion.BrepCodec.Journal.Planar.LiveTable import LiveTable
from convert.formats.Fusion.BrepCodec.Journal.Planar.RequireLive import RequireLive
from convert.formats.Fusion.BrepCodec.Journal.Planar.StableRef import StableRef


def CheckEdgeUses(Table: LiveTable, Faces: tuple[FaceBoundary, ...]) -> None:
    Edges: dict[int, list[BoundaryUse]] = {}
    BoundaryUses = tuple(
        Value for FaceValue in Faces for Value in FaceValue.BoundaryUses
    )
    if len({Value.CoedgeRef for Value in BoundaryUses}) != len(BoundaryUses):
        raise ValueError("Fusion coedge is owned by multiple face boundaries")
    for Value in BoundaryUses:
        Edges.setdefault(Value.EdgeRef, []).append(Value)
    for EdgeRef, Entries in Edges.items():
        if len(Entries) != 2:
            raise ValueError("Fusion planar solid edge requires two coedges")
        First, Second = Entries
        if (
            First.StartVertex,
            First.EndVertex,
            First.PartnerRef,
            Second.PartnerRef,
        ) != (Second.EndVertex, Second.StartVertex, Second.CoedgeRef, First.CoedgeRef):
            raise ValueError("Fusion planar partner coedges disagree")
        EdgeValue = RequireLive(Table, EdgeRef, EdgeNode)
        if StableRef(Table, EdgeValue.OwnerCoedge) not in (
            First.CoedgeRef,
            Second.CoedgeRef,
        ):
            raise ValueError("Fusion edge owner is outside its face uses")
