# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from math import atan2 as ArcTangent, hypot as Hypot, isclose as IsClose, pi as HalfTurn

from interchange.enums.EnumGeometry import ConstraintKind
from interchange.enums.EnumValues import ValueKind
from interchange.geometry.models.GeometryCurves import (
    CircleGeometry,
    LineGeometry,
    PointGeometry,
)
from interchange.geometry.models.Sketch import SketchEntity
from interchange.records.RecordParameter import ParameterValue


# the explicit point order determines a signed component for target solvers
def PointMeasure(
    KindValue: ConstraintKind, First: PointGeometry, Second: PointGeometry
) -> float:
    DeltaX = Second.point.x - First.point.x
    DeltaY = Second.point.y - First.point.y
    if KindValue == ConstraintKind.KDistanceX:
        return DeltaX
    if KindValue == ConstraintKind.KDistanceY:
        return DeltaY
    return Hypot(DeltaX, DeltaY)


# directed line vectors rule out unverified supplementary angle conventions
def AngleMeasure(First: LineGeometry, Second: LineGeometry) -> float:
    FirstX = First.end.x - First.start.x
    FirstY = First.end.y - First.start.y
    SecondX = Second.end.x - Second.start.x
    SecondY = Second.end.y - Second.start.y
    if not Hypot(FirstX, FirstY) > 0.0 or not Hypot(SecondX, SecondY) > 0.0:
        raise ValueError("Degenerate Fusion angular dimension line")
    Angle = ArcTangent(
        FirstX * SecondY - FirstY * SecondX, FirstX * SecondX + FirstY * SecondY
    )
    if not 0.0 < Angle < HalfTurn:
        raise ValueError("Unsupported Fusion angular dimension orientation")
    return Angle


# source measurement is checked against the bound value only after targets resolve
def DimMeasure(KindValue: ConstraintKind, Entities: tuple[SketchEntity, ...]) -> float:
    First = Entities[0].geometry
    if isinstance(First, CircleGeometry):
        return First.radius * (2.0 if KindValue == ConstraintKind.KDiameter else 1.0)
    Second = Entities[1].geometry
    if isinstance(First, PointGeometry) and isinstance(Second, PointGeometry):
        return PointMeasure(KindValue, First, Second)
    if isinstance(First, LineGeometry) and isinstance(Second, LineGeometry):
        return AngleMeasure(First, Second)
    raise ValueError("Unsupported Fusion dimensional measurement geometry")


# geometric corroboration preserves raw magnitudes while reporting axis sign separately
def CheckDimMeasure(
    KindValue: ConstraintKind,
    Entities: tuple[SketchEntity, ...],
    ParamValue: ParameterValue,
) -> int:
    Measurement = DimMeasure(KindValue, Entities)
    Expected = (
        (ValueKind.KAngle, "rad", 1.0)
        if KindValue == ConstraintKind.KAngle
        else (ValueKind.KLength, "cm", 10.0)
    )
    NativeValue = ParamValue.value
    if (
        (ParamValue.kind, ParamValue.unit) != Expected[:2]
        or not isinstance(NativeValue, (float, int))
        or isinstance(NativeValue, bool)
        or NativeValue <= 0.0
        or not IsClose(
            abs(Measurement), NativeValue * Expected[2], rel_tol=1e-8, abs_tol=1e-7
        )
    ):
        raise ValueError("Fusion dimension geometry disagrees with its bound value")
    return -1 if Measurement < 0.0 else 1
