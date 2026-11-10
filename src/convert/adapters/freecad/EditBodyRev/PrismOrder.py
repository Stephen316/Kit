# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from dataclasses import dataclass as MakeDataClass

from convert.geometry.Extrude.Polygon.PrismFrame import PlacePrismPoint
from convert.geometry.Revolve.SweepVector import OffsetVector
from interchange.brep.curves.BrepCurves import LineCurve
from interchange.brep.topology.BrepModel import BrepModel
from interchange.geometry.models.GeometryCurves import LineGeometry
from interchange.geometry.models.Sketch import Sketch
from interchange.geometry.models.Transform import KOriginZero, Transform
from interchange.geometry.models.VectorSpace import SpaceVector


# native edge identity needs the same child traversal on load and on recompute
@MakeDataClass(frozen=True, slots=True)
class PrismOrder:
    Children: dict[str, tuple[int, ...]]
    EdgeName: str
    Axis: SpaceVector
    Base: SpaceVector


# native wall traversal follows the source wire when its authored slots already form a cycle
def ReadWallOrder(
    Model: BrepModel, SketchValue: Sketch, Frame: Transform, Negative: bool
) -> tuple[tuple[int, bool, str], ...]:
    (Profile,) = SketchValue.closed_profile_entity_ids
    Count = len(Profile)
    Vertices = {Value.id: Value.point for Value in Model.vertices}
    Offset = Count if Negative else 0
    Pairs = tuple(
        (Vertices[EdgeValue.start_vertex_id], Vertices[EdgeValue.end_vertex_id])
        for EdgeValue in Model.edges[Offset : Offset + Count]
    )
    ByEnds = {frozenset(PairValue): Index for Index, PairValue in enumerate(Pairs)}
    if len(ByEnds) != Count:
        raise ValueError("FreeCAD linked extrusion has ambiguous base edges")
    Members = set(Profile)
    Order: list[tuple[int, bool, str]] = []
    for Entity in SketchValue.entities:
        if Entity.id not in Members:
            continue
        LineValue = Entity.geometry
        if not isinstance(LineValue, LineGeometry):
            raise ValueError("FreeCAD linked extrusion needs a line profile")
        Endpoints = (
            PlacePrismPoint(Frame, LineValue.start, 0.0),
            PlacePrismPoint(Frame, LineValue.end, 0.0),
        )
        Index = ByEnds[frozenset(Endpoints)]
        Order.append((Index, Endpoints == Pairs[Index], Entity.id))
    Indices = tuple(ItemValue[0] for ItemValue in Order)
    if len(set(Indices)) != Count or not any(
        Indices == tuple((Indices[0] + Sense * Index) % Count for Index in range(Count))
        for Sense in (1, -1)
    ):
        raise ValueError(
            "FreeCAD linked extrusion requires an already ordered sketch wire"
        )
    FirstIndex, FirstForward, _ = Order[0]
    Following = (FirstIndex + (1 if FirstForward else -1)) % Count
    return tuple(Order) if Indices[1] == Following else (Order[0], *Order[:0:-1])


# first encounters of rails and rims determine the linked subelement without vendor bytes
def ReadPrismOrder(
    Model: BrepModel,
    SketchValue: Sketch,
    Frame: Transform,
    AxisEdgeId: str,
    AxisLineId: str,
    DepthMm: float,
) -> PrismOrder:
    Negative = DepthMm < 0.0
    Order = ReadWallOrder(Model, SketchValue, Frame, Negative)
    Count = len(Order)
    Offset = Count if Negative else 0
    (Shell,) = Model.shells
    if len(Shell.face_use_ids) != Count + 2 or len(Model.loops) != Count + 2:
        raise ValueError("FreeCAD linked extrusion is missing its wall or cap topology")
    Selected = next(
        (
            (SlotValue, Index)
            for SlotValue, (Index, _, Identity) in enumerate(Order, 1)
            if Identity == AxisLineId and Model.edges[Offset + Index].id == AxisEdgeId
        ),
        None,
    )
    if Selected is None:
        raise ValueError("FreeCAD linked extrusion does not own the selected base edge")
    SlotValue, Index = Selected
    EdgeValue = Model.edges[Offset + Index]
    Curve = Model.curves[Offset + Index]
    EndId = EdgeValue.start_vertex_id if Negative else EdgeValue.end_vertex_id
    BaseValue = next(Value.point for Value in Model.vertices if Value.id == EndId)
    if not isinstance(Curve, LineCurve) or Curve.id != EdgeValue.curve_id:
        raise ValueError("FreeCAD linked extrusion needs a straight selected edge")
    RimValue, FarRim = (2, 0) if Negative else (0, 2)
    Children: dict[str, tuple[int, ...]] = {
        f"loop:{Model.loops[WallValue + 2].id}": (
            *((3, 1) if IsForward else (1, 3)),
            RimValue,
            FarRim,
        )
        for WallValue, IsForward, _ in Order
    }
    Capabilities = (1, 0) if Negative else (0, 1)
    Children[f"shell:{Shell.id}"] = (
        *(WallValue + 2 for WallValue, _, _ in Order),
        *Capabilities,
    )
    EdgeNumber = 3 * SlotValue - (1 if SlotValue == Count else 0)
    AxisValue = (
        OffsetVector(KOriginZero, Curve.direction, -1.0)
        if Negative
        else Curve.direction
    )
    return PrismOrder(Children, f"Edge{EdgeNumber}", AxisValue, BaseValue)
