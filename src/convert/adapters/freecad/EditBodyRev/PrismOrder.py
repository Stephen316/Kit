# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import dataclass as MakeDataClass

from convert.geometry.Extrude.Polygon.PrismFrame import PlacePrismPoint
from interchange.brep.curves.BrepCurves import LineCurve
from interchange.brep.topology.BrepModel import BrepModel
from interchange.geometry.models.GeometryCurves import LineGeometry
from interchange.geometry.models.Sketch import Sketch
from interchange.geometry.models.Transform import Transform
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
    Model: BrepModel, SketchValue: Sketch, Frame: Transform
) -> tuple[tuple[int, bool, str], ...]:
    (Profile,) = SketchValue.closed_profile_entity_ids
    Count = len(Profile)
    Vertices = {Value.id: Value.point for Value in Model.vertices}
    Pairs = tuple(
        (Vertices[Edge.start_vertex_id], Vertices[Edge.end_vertex_id])
        for Edge in Model.edges[:Count]
    )
    ByEnds = {frozenset(Pair): Index for Index, Pair in enumerate(Pairs)}
    if len(ByEnds) != Count:
        raise ValueError("FreeCAD linked extrusion has ambiguous base edges")
    Members = set(Profile)
    Order = []
    for Entity in SketchValue.entities:
        if Entity.id not in Members:
            continue
        Line = Entity.geometry
        if not isinstance(Line, LineGeometry):
            raise ValueError("FreeCAD linked extrusion needs a line profile")
        Ends = (
            PlacePrismPoint(Frame, Line.start, 0.0),
            PlacePrismPoint(Frame, Line.end, 0.0),
        )
        Index = ByEnds[frozenset(Ends)]
        Order.append((Index, Ends == Pairs[Index], Entity.id))
    Indices = tuple(Item[0] for Item in Order)
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
) -> PrismOrder:
    Order = ReadWallOrder(Model, SketchValue, Frame)
    Count = len(Order)
    (Shell,) = Model.shells
    if len(Shell.face_use_ids) != Count + 2 or len(Model.loops) != Count + 2:
        raise ValueError("FreeCAD linked extrusion is missing its wall or cap topology")
    Selected = next(
        (
            (Slot, Index)
            for Slot, (Index, _, Identity) in enumerate(Order, 1)
            if Identity == AxisLineId and Model.edges[Index].id == AxisEdgeId
        ),
        None,
    )
    if Selected is None:
        raise ValueError("FreeCAD linked extrusion does not own the selected base edge")
    Slot, Index = Selected
    Edge = Model.edges[Index]
    Curve = Model.curves[Index]
    Base = next(
        Value.point for Value in Model.vertices if Value.id == Edge.end_vertex_id
    )
    if not isinstance(Curve, LineCurve) or Curve.id != Edge.curve_id:
        raise ValueError("FreeCAD linked extrusion needs a straight selected edge")
    Children = {
        f"loop:{Model.loops[Wall + 2].id}": (3, 1, 0, 2) if IsForward else (1, 3, 0, 2)
        for Wall, IsForward, _ in Order
    }
    Children[f"shell:{Shell.id}"] = (*(Wall + 2 for Wall, _, _ in Order), 0, 1)
    EdgeNumber = 3 * Slot - (1 if Slot == Count else 0)
    return PrismOrder(Children, f"Edge{EdgeNumber}", Curve.direction, Base)
