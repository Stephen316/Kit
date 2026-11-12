from math import isfinite as IsFinite
from typing import cast as CastValue

from interchange.features.PlaneExtAxis import GetExtAxis, GetExtVector, KAxisTolerance
from interchange.geometry.models.Transform import Transform
from interchange.geometry.models.VectorSpace import SpaceVector

# centimetre scale source tolerance converted to neutral millimetres
KStationTolerance = 1e-8


# a plane normal must agree with the same finite right handed frame as its origin
def GetExtFrame(
    FrameValue: Transform,
) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    if not isinstance(CastValue(object, FrameValue), Transform):
        raise ValueError("plane extrusion requires a typed plane frame")
    Origin = GetExtVector(FrameValue.origin)
    First, Second, Normal = (
        GetExtAxis(Value)
        for Value in (FrameValue.x_axis, FrameValue.y_axis, FrameValue.z_axis)
    )
    FirstX, FirstY, FirstZ = First
    SecondX, SecondY, SecondZ = Second
    Cross = (
        FirstY * SecondZ - FirstZ * SecondY,
        FirstZ * SecondX - FirstX * SecondZ,
        FirstX * SecondY - FirstY * SecondX,
    )
    if abs(
        sum(AxisValue * Other for AxisValue, Other in zip(First, Second))
    ) > KAxisTolerance or any(
        abs(AxisValue - Other) > KAxisTolerance
        for AxisValue, Other in zip(Cross, Normal)
    ):
        raise ValueError(
            "plane extrusion requires orthonormal right handed plane frames"
        )
    return Origin, Normal


# the offset convention is proven only for a forward plane facing the extrusion axis
def GetPlaneRise(Profile: Transform, Limit: Transform, Direction: SpaceVector) -> float:
    ProfileOrigin, ProfileNormal = GetExtFrame(Profile)
    LimitOrigin, LimitNormal = GetExtFrame(Limit)
    AxisValue = GetExtAxis(Direction)
    Denominator = sum(Value * Normal for Value, Normal in zip(AxisValue, LimitNormal))
    if abs(Denominator - 1.0) > KAxisTolerance or any(
        abs(Value - Normal) > KAxisTolerance
        for AxisNormal in (ProfileNormal, LimitNormal)
        for Value, Normal in zip(AxisValue, AxisNormal)
    ):
        raise ValueError(
            "plane extrusion requires parallel co-directed plane and extrusion normals"
        )
    Station = (
        sum(
            Normal * (Target - Origin)
            for Normal, Target, Origin in zip(LimitNormal, LimitOrigin, ProfileOrigin)
        )
        / Denominator
    )
    if not IsFinite(Station) or Station <= KStationTolerance:
        raise ValueError(
            "plane extrusion selected plane must be finite and forward from the profile"
        )
    return Station
