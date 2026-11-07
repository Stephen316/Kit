# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from math import atan2 as AtanTwo
from math import cos as Cos
from math import isclose as IsClose
from math import isfinite as IsFinite
from math import sin as Sin
from math import tau as FullTurn
from struct import unpack_from as UnpackFrom

from convert.formats.Fusion.Sketches.SketchPointRef import ReadPointRef
from interchange.geometry.models.GeometryCurves import ArcGeometry
from interchange.geometry.models.VectorPlane import PlaneVector


# circular carriers must lie in the local sketch plane before becoming neutral curves
def IsCircleFrame(Normal: tuple[float, ...], RefAxis: tuple[float, ...]) -> bool:
    return (
        all(map(IsFinite, Normal))
        and all(map(IsFinite, RefAxis))
        and abs(Normal[0]) <= 1e-9
        and abs(Normal[1]) <= 1e-9
        and IsClose(abs(Normal[2]), 1.0, abs_tol=1e-9)
        and abs(RefAxis[2]) <= 1e-9
        and IsClose(sum(Value * Value for Value in RefAxis), 1.0, abs_tol=1e-9)
    )


# the angular trim is qualified by its native center and ordered endpoint records
def ReadSketchArc(
    BodyValue: bytes, Offset: int, Points: dict[int, PlaneVector]
) -> tuple[ArcGeometry, dict[str, object]]:
    if Offset < 0 or len(BodyValue) - Offset != 182:
        raise ValueError("Unsupported Fusion sketch arc layout")
    Values = UnpackFrom("<12d", BodyValue, Offset)
    CenterCoords = tuple(Value * 10 for Value in Values[:3])
    Normal, RefAxis = Values[3:6], Values[6:9]
    Radius = Values[9] * 10
    NativeStart, NativeEnd = Values[10:12]
    Span = NativeEnd - NativeStart
    if (
        not all(map(IsFinite, (*CenterCoords, Radius)))
        or abs(CenterCoords[2]) > 1e-8
        or Radius <= 0.0
        or not 0.0 < Span < FullTurn
        or not IsCircleFrame(Normal, RefAxis)
        or abs(sum(Left * Right for Left, Right in zip(Normal, RefAxis))) > 1e-9
    ):
        raise ValueError("Invalid Fusion sketch arc frame or angular interval")
    CenterId, Center = ReadPointRef(BodyValue, Offset + 96, Points)
    EndId, EndPoint = ReadPointRef(BodyValue, Offset + 107, Points)
    StartId, StartPoint = ReadPointRef(BodyValue, Offset + 118, Points)
    if len({CenterId, StartId, EndId}) != 3 or not all(
        IsClose(Value, Expected, abs_tol=1e-8)
        for Value, Expected in zip((Center.x, Center.y), CenterCoords[:2])
    ):
        raise ValueError("Fusion sketch arc center or point references disagree")
    CrossAxis = (
        Normal[1] * RefAxis[2] - Normal[2] * RefAxis[1],
        Normal[2] * RefAxis[0] - Normal[0] * RefAxis[2],
        Normal[0] * RefAxis[1] - Normal[1] * RefAxis[0],
    )
    Radians = []
    for Angle, PointValue in ((NativeStart, StartPoint), (NativeEnd, EndPoint)):
        Cosine, Sine = Cos(Angle), Sin(Angle)
        Radial = tuple(
            Cosine * First + Sine * Second for First, Second in zip(RefAxis, CrossAxis)
        )
        Expected = tuple(
            CenterValue + Radius * RadialValue
            for CenterValue, RadialValue in zip(CenterCoords, Radial)
        )
        if not all(
            IsClose(Value, Target, abs_tol=1e-8)
            for Value, Target in zip((PointValue.x, PointValue.y, 0.0), Expected)
        ):
            raise ValueError("Fusion sketch arc endpoint reference disagrees")
        Radians.append(AtanTwo(Radial[1], Radial[0]) % FullTurn)
    Clockwise = Normal[2] < 0.0
    StartAngle = Radians[1 if Clockwise else 0]
    EndAngle = StartAngle + Span
    if EndAngle <= StartAngle:
        raise ValueError("Fusion sketch arc interval collapses in neutral coordinates")
    return (
        ArcGeometry(Center, Radius, StartAngle, EndAngle),
        {
            "fusion.arc_native_angles_radians": (NativeStart, NativeEnd),
            "fusion.arc_native_normal": Normal,
            "fusion.arc_native_reference_axis": RefAxis,
            "fusion.arc_native_point_ids": (CenterId, StartId, EndId),
            "fusion.arc_native_clockwise": Clockwise,
        },
    )
