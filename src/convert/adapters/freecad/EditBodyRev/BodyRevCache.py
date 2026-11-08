# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

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
def BuildBodyCache(DocValue: CadDocument, Plan: BodyRevPlan) -> BodyRevCache | None:
    try:
        Source = next(
            Value for Value in DocValue.sketches if Value.id == Plan.Extrude.SketchId
        )
        Order = ReadPrismOrder(
            Plan.ExtrudeModel,
            Source,
            Plan.SourceFrame,
            Plan.AxisEdgeId,
            Plan.AxisLineId,
            Plan.Extrude.DistanceMm,
        )
        Alignment = DotVector(Order.Axis, Plan.Revolve.AxisDirection)
        if abs(abs(Alignment) - 1.0) > 1e-9:
            return None
        Extrude = BrepModelBrep(Plan.ExtrudeModel, ChildOrders=Order.Children)
        Revolve = BrepModelBrep(Plan.RevolveModel)
    except (FreeCADBrepWriteError, IndexError, KeyError, StopIteration, ValueError):
        return None
    return BodyRevCache(
        Extrude,
        Revolve,
        Order.EdgeName,
        Order.Axis,
        Order.Base,
        Plan.Revolve.AngleDeg if Alignment > 0.0 else -Plan.Revolve.AngleDeg,
    )
