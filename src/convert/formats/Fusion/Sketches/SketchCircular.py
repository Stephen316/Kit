from math import atan2 as AtanTwo
from math import cos as CosData
from math import isclose as IsClose
from math import isfinite as IsFinite
from math import sin as SineValue
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
    SpanValue = NativeEnd - NativeStart
    if (
        not all(map(IsFinite, (*CenterCoords, Radius)))
        or abs(CenterCoords[2]) > 1e-8
        or Radius <= 0.0
        or not 0.0 < SpanValue < FullTurn
        or not IsCircleFrame(Normal, RefAxis)
        or abs(sum(LeftValue * Right for LeftValue, Right in zip(Normal, RefAxis)))
        > 1e-9
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
    Radians = ReadArcAngles(
        Normal,
        RefAxis,
        CenterCoords,
        Radius,
        ((NativeStart, StartPoint), (NativeEnd, EndPoint)),
    )
    Clockwise = Normal[2] < 0.0
    StartAngle = Radians[1 if Clockwise else 0]
    EndAngle = StartAngle + SpanValue
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


# the analytic arc must reproduce both referenced endpoints in the native frame
def ReadArcAngles(
    Normal: tuple[float, ...],
    RefAxis: tuple[float, ...],
    CenterCoords: tuple[float, ...],
    Radius: float,
    EndsValue: tuple[tuple[float, PlaneVector], tuple[float, PlaneVector]],
) -> list[float]:
    CrossAxis = (
        Normal[1] * RefAxis[2] - Normal[2] * RefAxis[1],
        Normal[2] * RefAxis[0] - Normal[0] * RefAxis[2],
        Normal[0] * RefAxis[1] - Normal[1] * RefAxis[0],
    )
    Radians: list[float] = []
    for Angle, PointValue in EndsValue:
        Cosine, SineData = CosData(Angle), SineValue(Angle)
        Radial = tuple(
            Cosine * First + SineData * Second
            for First, Second in zip(RefAxis, CrossAxis)
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
    return Radians
