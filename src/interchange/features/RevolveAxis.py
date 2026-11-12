from typing import cast as CastValue
from math import hypot as Hypot
from math import isclose as IsClose
from sys import float_info as FloatInfo

from interchange.geometry.models.VectorSpace import SpaceVector


# shared axis qualification keeps every revolution definition safe for geometry consumers
def CheckRevAxis(AxisOrigin: SpaceVector, AxisDirection: SpaceVector) -> None:
    if not isinstance(CastValue(object, AxisOrigin), SpaceVector) or not isinstance(
        CastValue(object, AxisDirection), SpaceVector
    ):
        raise ValueError("revolution axis requires spatial vectors")
    Direction = (AxisDirection.x, AxisDirection.y, AxisDirection.z)
    Origin = (AxisOrigin.x, AxisOrigin.y, AxisOrigin.z)
    if not all(
        type(Value) in (float, int) and -FloatInfo.max <= Value <= FloatInfo.max
        for Value in (*Direction, *Origin)
    ):
        raise ValueError("revolution axis must contain finite numbers")
    if not IsClose(Hypot(*Direction), 1.0, abs_tol=1e-9, rel_tol=0.0):
        raise ValueError("revolution axis direction must have unit length")
