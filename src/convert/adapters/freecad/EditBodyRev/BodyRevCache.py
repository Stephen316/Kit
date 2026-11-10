# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from dataclasses import dataclass as MakeDataClass

from convert.adapters.freecad.Brep import BrepModelBrep, FreeCADBrepWriteError
from convert.adapters.freecad.EditBodyRev.BodyRevPlan import BodyRevPlan
from convert.adapters.freecad.EditBodyRev.PrismOrder import ReadPrismOrder
from convert.geometry.Revolve.SweepVector import DotVector
from interchange.document.models.DocumentModel import CadDocument
from interchange.geometry.models.VectorSpace import SpaceVector


# each feature owns its starting solid and the axis link already resolves on first load
@MakeDataClass(frozen=True, slots=True)
class BodyRevCache:
    Extrude: bytes
    Revolve: bytes
    EdgeName: str
    Axis: SpaceVector
    Base: SpaceVector
    AngleDeg: float


# the ordered prism cache and the live result share one corroborated signed sweep
def BuildBodyCache(DocValue: CadDocument, PlanValue: BodyRevPlan) -> BodyRevCache:
    try:
        Source = next(
            Value
            for Value in DocValue.sketches
            if Value.id == PlanValue.Extrude.SketchId
        )
        Order = ReadPrismOrder(
            PlanValue.ExtrudeModel,
            Source,
            PlanValue.SourceFrame,
            PlanValue.AxisEdgeId,
            PlanValue.AxisLineId,
            PlanValue.Extrude.DistanceMm,
        )
        Alignment = DotVector(Order.Axis, PlanValue.Revolve.AxisDirection)
        if abs(abs(Alignment) - 1.0) > 1e-9:
            raise ValueError("saved edge and Revolve axes disagree")
        Extrude = BrepModelBrep(PlanValue.ExtrudeModel, ChildOrders=Order.Children)
        Revolve = BrepModelBrep(PlanValue.RevolveModel)
    except (
        FreeCADBrepWriteError,
        IndexError,
        KeyError,
        StopIteration,
        ValueError,
    ) as ErrorInfo:
        raise FreeCADBrepWriteError(
            "FreeCAD editable body axis Revolve cache could not be built"
        ) from ErrorInfo
    return BodyRevCache(
        Extrude,
        Revolve,
        Order.EdgeName,
        Order.Axis,
        Order.Base,
        PlanValue.Revolve.AngleDeg if Alignment > 0.0 else -PlanValue.Revolve.AngleDeg,
    )
