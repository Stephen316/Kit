from convert.formats.Fusion.BrepCodec.Frustum.Models.ConeFrame import ConeFrame
from convert.formats.Fusion.BrepCodec.Frustum.Validation.FrustumNumbers import (
    CheckReal,
    CheckVector,
    IsNear,
    IsNearVector,
)
from convert.formats.Fusion.GeometryCodec.Frustum.FrustumBody import FrustumBody


def CheckConeFrame(Model: FrustumBody, Surface: ConeFrame) -> None:
    for Vector in (Surface.OriginCm, Surface.Axis, Surface.MajorVectorCm):
        CheckVector(Vector)
    for Value in (
        Surface.Ratio,
        Surface.SineAngle,
        Surface.CosineAngle,
        Surface.ScaleCm,
    ):
        CheckReal(Value)
    Origin = tuple(Value / 10 for Value in Model.BasePoint)
    if (
        Surface.Axis != (0.0, 0.0, 1.0)
        or Surface.Ratio != 1
        or Surface.ReverseSense is not False
    ):
        raise ValueError("Unsupported frustum cone axis, ellipse ratio or sense")
    if not IsNearVector(Surface.OriginCm, (Origin[0], Origin[1], Origin[2])):
        raise ValueError("Frustum cone origin disagrees with its body")
    if (
        Surface.MajorVectorCm[0] <= 0
        or Surface.MajorVectorCm[1:] != (0.0, 0.0)
        or not IsNear(Surface.MajorVectorCm[0], Model.BottomRadius / 10)
    ):
        raise ValueError("Frustum cone base radius disagrees with its body")
    if Surface.ScaleCm <= 0 or Surface.CosineAngle <= 0 or abs(Surface.SineAngle) >= 1:
        raise ValueError("Unsupported frustum cone parameterization")
    if not IsNear(Surface.SineAngle**2 + Surface.CosineAngle**2, 1.0):
        raise ValueError("Frustum cone angle is not normalized")
    UpperRadius = (
        Model.BottomRadius / 10
        + Model.Height / 10 * Surface.SineAngle / Surface.CosineAngle
    )
    if not IsNear(UpperRadius, Model.TopRadius / 10):
        raise ValueError("Frustum cone angle disagrees with its upper radius")
