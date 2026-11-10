# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from collections.abc import Mapping
from dataclasses import dataclass as MakeDataClass
from math import hypot as Hypot, isfinite as IsFinite

from interchange.geometry.models.GeometryCurves import (
    CircleGeometry,
    LineGeometry,
    PointGeometry,
)
from interchange.geometry.models.Sketch import SketchEntity, SketchRelation
from interchange.geometry.models.VectorPlane import PlaneVector

# residual tolerances use physical millimeters and separate unitless directions
KSketchRuleTol = 1e-6

# unit axis checks and angular measurements have a tighter dimensionless tolerance
KSketchAngleTol = 1e-9


# neutral references keep the exact source geometry and selected point role together
@MakeDataClass(frozen=True, slots=True)
class RuleOperand:
    Geometry: PointGeometry | LineGeometry | CircleGeometry
    SlotName: str


# authored identities are never resolved by coordinate proximity
def RuleOperands(
    Relation: SketchRelation, Entities: Mapping[str, SketchEntity]
) -> tuple[RuleOperand, ...]:
    Result: list[RuleOperand] = []
    for RefValue in Relation.references:
        Entity = Entities.get(RefValue.entity_id)
        if Entity is None or not isinstance(
            Entity.geometry, (PointGeometry, LineGeometry, CircleGeometry)
        ):
            raise ValueError(
                "FreeCAD editable sketch constraint operand is unavailable"
            )
        Result.append(RuleOperand(Entity.geometry, RefValue.point))
    return tuple(Result)


# a whole curve is distinct from one explicitly selected geometric point
def RulePoint(Value: RuleOperand) -> PlaneVector:
    Geometry = Value.Geometry
    if isinstance(Geometry, PointGeometry) and Value.SlotName in ("", "start"):
        return Geometry.point
    if isinstance(Geometry, LineGeometry):
        if Value.SlotName == "start":
            return Geometry.start
        if Value.SlotName == "end":
            return Geometry.end
    if isinstance(Geometry, CircleGeometry) and Value.SlotName == "center":
        return Geometry.center
    raise ValueError("FreeCAD editable sketch constraint point slot is unsupported")


# whole segment operands retain native order so signed axes and angles stay stable
def RuleLine(Value: RuleOperand) -> LineGeometry:
    if isinstance(Value.Geometry, LineGeometry) and not Value.SlotName:
        return Value.Geometry
    raise ValueError("FreeCAD editable sketch constraint line slot is unsupported")


# circular dimensions use the complete carrier rather than a selected point
def RuleCircle(Value: RuleOperand) -> CircleGeometry:
    if (
        isinstance(Value.Geometry, CircleGeometry)
        and not Value.SlotName
        and IsFinite(Value.Geometry.radius)
        and Value.Geometry.radius > KSketchRuleTol
    ):
        return Value.Geometry
    raise ValueError("FreeCAD editable sketch constraint circle slot is unsupported")


# local differences make residuals independent of a sketch origin translation
def PointDelta(First: PlaneVector, Second: PlaneVector) -> PlaneVector:
    return PlaneVector(Second.x - First.x, Second.y - First.y)


# line direction comparisons must be independent of unequal segment lengths
def RuleLineAxis(LineValue: LineGeometry) -> tuple[PlaneVector, float]:
    Delta = PointDelta(LineValue.start, LineValue.end)
    Length = Hypot(Delta.x, Delta.y)
    if not IsFinite(Length) or Length <= KSketchRuleTol:
        raise ValueError("FreeCAD editable sketch constraint has a degenerate line")
    return PlaneVector(Delta.x / Length, Delta.y / Length), Length


# signed perpendicular offsets distinguish tangency and symmetry branches
def RuleLineLocal(
    Point: PlaneVector, LineValue: LineGeometry
) -> tuple[float, float, float]:
    Direction, Length = RuleLineAxis(LineValue)
    Delta = PointDelta(LineValue.start, Point)
    return (
        Delta.x * Direction.x + Delta.y * Direction.y,
        Direction.x * Delta.y - Direction.y * Delta.x,
        Length,
    )
