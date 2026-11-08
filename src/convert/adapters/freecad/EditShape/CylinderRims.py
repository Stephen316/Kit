# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from dataclasses import dataclass as MakeDataClass
from math import cos as Cosine, hypot as Hypot, sin as SineValue, tau as TauValue

from convert.geometry.Revolve.SweepVector import CrossVector, DotVector, OffsetVector
from interchange.brep.curves.BrepCurves import CircleCurve, LineCurve
from interchange.brep.topology.BrepModel import BrepModel
from interchange.brep.topology.BrepTopology import BrepEdge
from interchange.geometry.models.VectorSpace import SpaceVector

# an absolute millimeter bound avoids accepting a large displacement at far coordinates
KPositionTolerance = 1e-6

# unit direction and angular interval comparisons use a separate dimensionless bound
KAngleTolerance = 1e-9


# the confirmed rim vertices also serve as the only valid seam endpoints
@MakeDataClass(frozen=True, slots=True)
class CylinderRim:
    EdgeId: str
    VertexId: str
    CurveAxis: SpaceVector


# spatial comparison keeps large coordinates from hiding significant local differences
def IsNearPoint(First: SpaceVector, Second: SpaceVector) -> bool:
    return (
        Hypot(First.x - Second.x, First.y - Second.y, First.z - Second.z)
        <= KPositionTolerance
    )


# unit vectors parallel to the profile normal can use either carrier sign
def IsParallel(First: SpaceVector, Second: SpaceVector) -> bool:
    Cross = CrossVector(First, Second)
    return Hypot(Cross.x, Cross.y, Cross.z) <= KAngleTolerance


# a closed rim must travel the full analytic circle and start at its actual vertex
def IsFullRim(EdgeValue: BrepEdge, Curve: CircleCurve, Vertex: SpaceVector) -> bool:
    Start = EdgeValue.start_parameter
    SideVector = CrossVector(Curve.axis, Curve.reference_direction)
    PointValue = OffsetVector(
        OffsetVector(
            Curve.center, Curve.reference_direction, Curve.radius * Cosine(Start)
        ),
        SideVector,
        Curve.radius * SineValue(Start),
    )
    return (
        EdgeValue.start_vertex_id == EdgeValue.end_vertex_id
        and abs(EdgeValue.end_parameter - Start - TauValue) <= KAngleTolerance
        and Curve.radius * abs(EdgeValue.end_parameter - Start - TauValue)
        <= KPositionTolerance
        and IsNearPoint(Vertex, PointValue)
    )


# unique circles at both cap stations prove the boundary diameter and depth
def ReadCylRims(
    Model: BrepModel,
    Centers: tuple[SpaceVector, SpaceVector],
    AxisValue: SpaceVector,
    Radius: float,
) -> tuple[CylinderRim, ...]:
    Curves = {Value.id: Value for Value in Model.curves}
    Vertices = {Value.id: Value.point for Value in Model.vertices}
    RimValues: list[CylinderRim] = []
    for Center in Centers:
        Matches: list[CylinderRim] = []
        for EdgeValue in Model.edges:
            Curve = Curves[EdgeValue.curve_id]
            if (
                isinstance(Curve, CircleCurve)
                and abs(Curve.radius - Radius) <= KPositionTolerance
                and IsNearPoint(Curve.center, Center)
                and IsParallel(Curve.axis, AxisValue)
                and IsFullRim(EdgeValue, Curve, Vertices[EdgeValue.start_vertex_id])
            ):
                Matches.append(
                    CylinderRim(EdgeValue.id, EdgeValue.start_vertex_id, Curve.axis)
                )
        if len(Matches) != 1:
            return ()
        RimValues.extend(Matches)
    return tuple(RimValues) if RimValues[0].VertexId != RimValues[1].VertexId else ()


# both circular trims must connect through the same straight generator edge
def ReadCylSeam(
    Model: BrepModel, RimValues: tuple[CylinderRim, ...], AxisValue: SpaceVector
) -> str | None:
    RimIds = {Value.EdgeId for Value in RimValues}
    VertexIds = {Value.VertexId for Value in RimValues}
    Curves = {Value.id: Value for Value in Model.curves}
    Vertices = {Value.id: Value.point for Value in Model.vertices}
    SeamEdge = next((Value for Value in Model.edges if Value.id not in RimIds), None)
    if (
        SeamEdge is None
        or {SeamEdge.start_vertex_id, SeamEdge.end_vertex_id} != VertexIds
    ):
        return None
    Curve = Curves[SeamEdge.curve_id]
    if not isinstance(Curve, LineCurve) or not IsParallel(Curve.direction, AxisValue):
        return None
    for VertexId, Parameter in (
        (SeamEdge.start_vertex_id, SeamEdge.start_parameter),
        (SeamEdge.end_vertex_id, SeamEdge.end_parameter),
    ):
        if not IsNearPoint(
            Vertices[VertexId], OffsetVector(Curve.origin, Curve.direction, Parameter)
        ):
            return None
    return SeamEdge.id if SeamEdge.start_parameter < SeamEdge.end_parameter else None
