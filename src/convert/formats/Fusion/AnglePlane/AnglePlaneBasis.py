# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt


from math import cos as Cosine, dist as Distance, sin as SinValue

from convert.geometry.Revolve.SweepVector import CrossVector, OffsetVector
from interchange.geometry.models.Transform import Transform
from interchange.geometry.models.VectorSpace import SpaceVector


# storage uses exact vector tuples without requiring typed attributes in the wire schema
def VectorCoords(Value: SpaceVector) -> tuple[float, float, float]:
    return Value.x, Value.y, Value.z


# the local positive rotation axis is the construction plane frame first axis
def RotatePlane(ZeroFrame: Transform, Radians: float) -> Transform:
    AxisValue = ZeroFrame.x_axis
    Normal = OffsetVector(
        OffsetVector(SpaceVector(0.0, 0.0, 0.0), ZeroFrame.z_axis, Cosine(Radians)),
        CrossVector(AxisValue, ZeroFrame.z_axis),
        SinValue(Radians),
    )
    return Transform(
        ZeroFrame.origin, AxisValue, CrossVector(Normal, AxisValue), Normal
    )


# geometry identity accepts only native rounding in the same coordinate system
def IsSameAngPlane(Expected: Transform, Actual: Transform) -> bool:
    return all(
        Distance(VectorCoords(First), VectorCoords(Second)) <= TolValue
        for First, Second, TolValue in (
            (Expected.origin, Actual.origin, 1e-8),
            (Expected.x_axis, Actual.x_axis, 1e-9),
            (Expected.y_axis, Actual.y_axis, 1e-9),
            (Expected.z_axis, Actual.z_axis, 1e-9),
        )
    )
