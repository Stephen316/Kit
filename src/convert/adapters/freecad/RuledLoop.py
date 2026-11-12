from math import isfinite as IsFinite

from convert.adapters.freecad.BrepGraph import ModelGraph
from convert.adapters.freecad.Cylinder.CylinderFrame import (
    KAxisTolerance,
    NormCylinder,
)
from convert.adapters.freecad.Cylinder.RuledSpans import IsRuledSpans
from convert.geometry.Revolve.SweepVector import DotVector
from interchange.brep.surfaces.BrepSurfaces import ConeSurface, CylinderSurface
from interchange.brep.topology.BrepTopology import BrepFace, BrepLoop


# ruled periodic faces require one trim rectangle with two proven generators
def IsRuledLoop(
    Graph: ModelGraph,
    FaceValue: BrepFace,
    Surface: CylinderSurface | ConeSurface,
    LoopValue: BrepLoop,
    Tolerance: float,
) -> bool:
    if (
        not IsFinite(Tolerance)
        or Tolerance <= 0.0
        or FaceValue.loop_ids != (LoopValue.id,)
        or not LoopValue.outer
        or len(LoopValue.coedge_ids) != 4
        or Surface.id != FaceValue.surface_id
        or not IsFinite(Surface.radius)
        or Surface.radius < 0.0
        or (isinstance(Surface, CylinderSurface) and Surface.radius == 0.0)
    ):
        return False
    AxisValue = NormCylinder(Surface.axis)
    RefValue = NormCylinder(Surface.reference_direction)
    if (
        AxisValue is None
        or RefValue is None
        or abs(DotVector(AxisValue, RefValue)) > KAxisTolerance
    ):
        return False
    Coedges = tuple(Graph.coedges[Identity] for Identity in LoopValue.coedge_ids)
    if (
        any(Value.pcurve_id for Value in Coedges)
        or len({Value.edge_id for Value in Coedges}) != 4
    ):
        return False
    Edges = tuple(Graph.edges[Value.edge_id] for Value in Coedges)
    Directions = tuple((1, 0) if UseValue.reversed else (0, 1) for UseValue in Coedges)
    Pairs = tuple(
        (
            (EdgeValue.end_vertex_id, EdgeValue.start_vertex_id)
            if Order == (1, 0)
            else (EdgeValue.start_vertex_id, EdgeValue.end_vertex_id)
        )
        for EdgeValue, Order in zip(Edges, Directions)
    )
    if len({Value[0] for Value in Pairs}) != 4 or any(
        Current[1] != Following[0]
        for Current, Following in zip(Pairs, Pairs[1:] + Pairs[:1])
    ):
        return False
    Allowed = max(
        1e-7,
        Tolerance,
        FaceValue.tolerance,
        *(Value.tolerance for Value in Edges),
        *(Graph.vertices[Value[0]].tolerance for Value in Pairs),
    )
    return IsRuledSpans(Graph, Surface, AxisValue, Edges, Directions, Pairs, Allowed)
