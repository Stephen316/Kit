from math import hypot as Hypot, isfinite as IsFinite

from convert.formats.Fusion.GeometryCodec.Frustum.CheckRimFit import CheckRimFit


def CheckFrustum(
    BottomRadius: float,
    TopRadius: float,
    Height: float,
    BasePoint: tuple[float, float, float],
) -> None:
    if len(BasePoint) != 3:
        raise ValueError("Frustum base must have three millimetre coordinates")
    Lengths = (BottomRadius, TopRadius, Height)
    if any(
        isinstance(Value, bool) or not IsFinite(Value)
        for Value in (*Lengths, *BasePoint)
    ):
        raise ValueError("Frustum dimensions must be finite real numbers")
    if any(Value <= 0 or Value / 10 == 0 for Value in Lengths):
        raise ValueError("Frustum dimensions must be positive representable lengths")
    RadiusDelta = TopRadius - BottomRadius
    SlantLength = Hypot(Height, RadiusDelta)
    if not IsFinite(SlantLength) or Height / SlantLength == 0:
        raise ValueError("Frustum cone angle exceeds floating-point precision")
    if RadiusDelta != 0 and (
        RadiusDelta / SlantLength == 0 or BottomRadius / 10 == TopRadius / 10
    ):
        raise ValueError("Frustum taper exceeds floating-point precision")
    CheckRimFit(BottomRadius, TopRadius, Height, BasePoint)
