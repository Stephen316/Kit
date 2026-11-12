from math import isclose as IsClose, isfinite as IsFinite
from struct import unpack as Unpack

from interchange.geometry.models.Transform import Transform
from interchange.geometry.models.VectorSpace import SpaceVector


# local geometry needs an orthonormal frame before entering neutral millimetre coordinates
def ReadPlaneAxes(DataValue: bytes) -> Transform:
    Values = tuple(float(Value) for Value in Unpack("<9d", DataValue))
    OriginX, OriginY, OriginZ, AxisXX, AxisXY, AxisXZ, AxisYX, AxisYY, AxisYZ = Values
    Origin = (OriginX * 10, OriginY * 10, OriginZ * 10)
    if not all(map(IsFinite, (*Values, *Origin))):
        raise ValueError("Non-finite Fusion construction plane coordinates")
    AxisX = (AxisXX, AxisXY, AxisXZ)
    AxisY = (AxisYX, AxisYY, AxisYZ)
    DotValue = AxisXX * AxisYX + AxisXY * AxisYY + AxisXZ * AxisYZ
    if (
        not IsClose(sum(Value * Value for Value in AxisX), 1.0, abs_tol=1e-9)
        or not IsClose(sum(Value * Value for Value in AxisY), 1.0, abs_tol=1e-9)
        or not IsClose(DotValue, 0.0, abs_tol=1e-9)
    ):
        raise ValueError("Fusion construction plane axes are not orthonormal")
    return Transform(
        origin=SpaceVector(*Origin),
        x_axis=SpaceVector(*AxisX),
        y_axis=SpaceVector(*AxisY),
        z_axis=SpaceVector(
            AxisXY * AxisYZ - AxisXZ * AxisYY,
            AxisXZ * AxisYX - AxisXX * AxisYZ,
            AxisXX * AxisYY - AxisXY * AxisYX,
        ),
    )
