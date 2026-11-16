from math import isclose as IsClose

from convert.geometry.Parasolid import DecodeBrepModel, EncodeBrepModel
from interchange.brep.topology.BrepModel import BrepModel
from interchange.brep.topology.BrepTopology import BrepLoop


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
    Spans = sorted(
        max(Coordinates) - min(Coordinates)
        for Coordinates in zip(*((Point.x, Point.y, Point.z) for Point in Points))
    )
    assert IsClose(Spans[0], 0, abs_tol=1e-7)
    return Spans[1] * Spans[2]


# the exterior must be correct without changing the native hole first traversal order
def VerifySwLoops(
    Model: BrepModel, GrossArea: float, HoleArea: float, CapCount: int
) -> None:
    Loops = {LoopValue.id: LoopValue for LoopValue in Model.loops}
    Holed = [Face for Face in Model.faces if len(Face.loop_ids) > 1]
    assert len(Holed) == CapCount
    for Face in Holed:
        Hole, Exterior = (Loops[LoopId] for LoopId in Face.loop_ids)
        assert not Hole.outer and Exterior.outer
        assert IsClose(MeasureLoop(Model, Hole), HoleArea, abs_tol=1e-7)
        assert IsClose(MeasureLoop(Model, Exterior), GrossArea, abs_tol=1e-7)


# the supported parasolid writer must retain both ring order and roles through reexport
def VerifySwExport(Model: BrepModel, GrossArea: float, HoleArea: float) -> None:
    Restored = DecodeBrepModel(EncodeBrepModel(Model))
    assert Restored is not None
    VerifySwLoops(Restored, GrossArea, HoleArea, 2)
