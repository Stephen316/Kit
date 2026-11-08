# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from math import isfinite as IsFinite

from convert.adapters.freecad.BrepGraph import ModelGraph
from convert.adapters.freecad.Cylinder.CylinderArc import ReadCylinderArc
from convert.adapters.freecad.Cylinder.CylinderFrame import (
    KAxisTolerance,
    NormCylinder,
)
from convert.adapters.freecad.Cylinder.CylinderQuad import IsCylinderQuad
from convert.adapters.freecad.Cylinder.CylinderRail import ReadCylRail
from convert.adapters.freecad.Cylinder.CylinderSpan import CylinderSpan
from convert.geometry.Revolve.SweepVector import DotVector
from interchange.brep.curves.BrepCurves import CircleCurve, LineCurve
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
        or Surface.radius <= 0.0
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
        tuple(
            (EdgeValue.start_vertex_id, EdgeValue.end_vertex_id)[Index]
            for Index in Order
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
    AngleTol = max(KAxisTolerance, Allowed / Surface.radius)
    Spans: list[CylinderSpan] = []
    for EdgeValue, Order, PairValue in zip(Edges, Directions, Pairs):
        if EdgeValue.degenerate:
            return False
        Curve = Graph.curves[EdgeValue.curve_id]
        Bounds = EdgeValue.start_parameter, EdgeValue.end_parameter
        Params = Bounds[Order[0]], Bounds[Order[1]]
        Vertices = (
            Graph.vertices[PairValue[0]].point,
            Graph.vertices[PairValue[1]].point,
        )
        if not all(map(IsFinite, Params)):
            return False
        if isinstance(Curve, CircleCurve):
            SpanValue = ReadCylinderArc(
                Curve, Surface, AxisValue, Params, Vertices, Allowed, AngleTol
            )
        elif isinstance(Curve, LineCurve):
            SpanValue = ReadCylRail(
                Curve, Surface, AxisValue, Params, Vertices, Allowed
            )
        else:
            return False
        if SpanValue is None:
            return False
        Spans.append(SpanValue)
    return IsCylinderQuad(tuple(Spans), Allowed, AngleTol)
