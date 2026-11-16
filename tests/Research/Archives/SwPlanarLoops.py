from math import isclose as IsClose

from convert.Geometry.Parasolid import DecodeBrepModel, EncodeBrepModel
from interchange.brep.Topology.BrepModel import BrepModel
from interchange.brep.Topology.BrepTopology import BrepLoop


# captured rectangles give an independent area witness for exterior and cut boundaries
def MeasureLoop(Model: BrepModel, LoopValue: BrepLoop) -> float:
    Edges = {EdgeValue.id: EdgeValue for EdgeValue in Model.edges}
    Coedges = {Coedge.id: Coedge for Coedge in Model.coedges}
    Vertices = {Vertex.id: Vertex.point for Vertex in Model.vertices}
    VertexIds = {
        VertexId
        for CoedgeId in LoopValue.coedge_ids
        for EdgeValue in (Edges[Coedges[CoedgeId].edge_id],)
        for VertexId in (EdgeValue.start_vertex_id, EdgeValue.end_vertex_id)
    }
    assert len(VertexIds) == len(LoopValue.coedge_ids) == 4
    Points = tuple(Vertices[VertexId] for VertexId in VertexIds)
    AxisCoordinates = (
        tuple(Point.x for Point in Points),
        tuple(Point.y for Point in Points),
        tuple(Point.z for Point in Points),
    )
    Spans = sorted(
        max(Coordinates) - min(Coordinates) for Coordinates in AxisCoordinates
    )
    assert IsClose(Spans[0], 0, abs_tol=1e-7)
    return Spans[1] * Spans[2]


# the exterior must be correct without changing the native hole first traversal order
def VerifySwLoops(
    Model: BrepModel, GrossArea: float, HoleArea: float, CapCount: int
) -> None:
    Loops = {LoopValue.id: LoopValue for LoopValue in Model.loops}
    Holed = [CapFace for CapFace in Model.faces if len(CapFace.loop_ids) > 1]
    assert len(Holed) == CapCount
    for CapFace in Holed:
        HoleLoop, Exterior = (Loops[LoopId] for LoopId in CapFace.loop_ids)
        assert not HoleLoop.outer and Exterior.outer
        assert IsClose(MeasureLoop(Model, HoleLoop), HoleArea, abs_tol=1e-7)
        assert IsClose(MeasureLoop(Model, Exterior), GrossArea, abs_tol=1e-7)


# the supported parasolid writer must retain both ring order and roles through reexport
def VerifySwExport(Model: BrepModel, GrossArea: float, HoleArea: float) -> None:
    Restored = DecodeBrepModel(EncodeBrepModel(Model))
    assert Restored is not None
    VerifySwLoops(Restored, GrossArea, HoleArea, 2)
