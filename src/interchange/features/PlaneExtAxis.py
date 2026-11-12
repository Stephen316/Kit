from math import hypot as Hypot, isclose as IsClose
from sys import float_info as FloatInfo
from typing import cast as CastValue

from interchange.geometry.models.VectorSpace import SpaceVector

# small rounding differences in stored unit vectors must not imply an oblique limit
KAxisTolerance = 1e-9


# extent evaluation only uses finite numerical operands in component coordinates
def GetExtVector(Vector: SpaceVector) -> tuple[float, float, float]:
    if not isinstance(CastValue(object, Vector), SpaceVector):
        raise ValueError("plane extrusion requires a spatial vector")
    Values = (Vector.x, Vector.y, Vector.z)
    if not all(
        type(Value) in (float, int) and -FloatInfo.max <= Value <= FloatInfo.max
        for Value in Values
    ):
        raise ValueError("plane extrusion vectors must contain finite numbers")
    return Values


# an axial distance has physical units only when measured along a unit direction
def GetExtAxis(Vector: SpaceVector) -> tuple[float, float, float]:
    Values = GetExtVector(Vector)
    if not IsClose(Hypot(*Values), 1.0, abs_tol=KAxisTolerance, rel_tol=0.0):
        raise ValueError("plane extrusion direction must be a unit vector")
    return Values
