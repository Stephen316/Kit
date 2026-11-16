from dataclasses import replace as Replace
from typing import Mapping as TypeMap

from convert.Geometry.PlanarContain import FindPlanarOuter, KRingPointLimit
from interchange.brep.Curves.BrepCurves import LineCurve
from interchange.brep.Surfaces.BrepSurfaces import PlaneSurface
from interchange.brep.Topology.BrepModel import BrepModel
from interchange.brep.Topology.BrepTopology import (
    BrepCoedge,
    BrepEdge,
    BrepLoop,
    BrepVertex,
)
from interchange.geometry.Models.VectorSpace import SpaceVector


# signed coedge traversal ties a polygon proof to the saved connected line edges
def ReadRingPoints(
    LoopValue: BrepLoop,
    VertexIndex: TypeMap[str, BrepVertex],
    EdgeIndex: TypeMap[str, BrepEdge],
    CoedgeIndex: TypeMap[str, BrepCoedge],
    Lines: set[str],
) -> tuple[SpaceVector, ...] | None:
    Points: list[SpaceVector] = []
    FirstId, ExpectedId = "", ""
    try:
        for CoedgeId in LoopValue.coedge_ids:
            Coedge = CoedgeIndex[CoedgeId]
            EdgeValue = EdgeIndex[Coedge.edge_id]
            if (
                EdgeValue.degenerate
                or EdgeValue.curve_id not in Lines
                or Coedge.pcurve_id
            ):
                return None
            Start, Finish = EdgeValue.start_vertex_id, EdgeValue.end_vertex_id
            if Coedge.reversed:
                Start, Finish = Finish, Start
            if Points and Start != ExpectedId:
                return None
            if not Points:
                FirstId = Start
            Points.append(VertexIndex[Start].point)
            ExpectedId = Finish
    except KeyError:
        return None
    return tuple(Points) if FirstId == ExpectedId else None


# a face must prove one exterior before its legacy loop roles can be replaced
def ReadPlanarRoles(Model: BrepModel) -> dict[str, str]:
    Planes = {
        Surface.id: Surface
        for Surface in Model.surfaces
        if isinstance(Surface, PlaneSurface)
    }
    Faces = [
        FaceValue
        for FaceValue in Model.faces
        if len(FaceValue.loop_ids) > 1 and FaceValue.surface_id in Planes
    ]
    if not Faces:
        return {}
    Loops = {LoopValue.id: LoopValue for LoopValue in Model.loops}
    Coedges = {Coedge.id: Coedge for Coedge in Model.coedges}
    Edges = {EdgeValue.id: EdgeValue for EdgeValue in Model.edges}
    Vertices = {Vertex.id: Vertex for Vertex in Model.vertices}
    Lines = {Curve.id for Curve in Model.curves if isinstance(Curve, LineCurve)}
    Results: dict[str, str] = {}
    for FaceValue in Faces:
        Members = [Loops[LoopId] for LoopId in FaceValue.loop_ids if LoopId in Loops]
        if (
            len(Members) != len(FaceValue.loop_ids)
            or sum(len(LoopValue.coedge_ids) for LoopValue in Members) > KRingPointLimit
        ):
            continue
        Rings = [
            ReadRingPoints(LoopValue, Vertices, Edges, Coedges, Lines)
            for LoopValue in Members
        ]
        Complete = tuple(RingValue for RingValue in Rings if RingValue is not None)
        if len(Complete) != len(Members):
            continue
        OuterIndex = FindPlanarOuter(Complete, Planes[FaceValue.surface_id])
        if OuterIndex is not None:
            Results[FaceValue.id] = Members[OuterIndex].id
    return Results


# boundary role changes must preserve the native face loop and coedge order
def SetPlanarRoles(Model: BrepModel) -> BrepModel:
    Outers = ReadPlanarRoles(Model)
    if not Outers:
        return Model
    Roles = {
        LoopId: LoopId == Outers[FaceValue.id]
        for FaceValue in Model.faces
        if FaceValue.id in Outers
        for LoopId in FaceValue.loop_ids
    }
    return Replace(
        Model,
        loops=tuple(
            (
                Replace(LoopValue, outer=Roles[LoopValue.id])
                if LoopValue.id in Roles and LoopValue.outer != Roles[LoopValue.id]
                else LoopValue
            )
            for LoopValue in Model.loops
        ),
    )
