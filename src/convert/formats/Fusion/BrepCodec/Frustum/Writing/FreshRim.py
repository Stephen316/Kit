from math import cos as Cosine, pi as KHalfCircle, sin as SineValue

from convert.formats.Fusion.BrepCodec.Frustum.Models.RimFrame import RimFrame
from convert.formats.Fusion.GeometryCodec.Frustum.FrustumBody import FrustumBody


def FreshRim(Model: FrustumBody, IsUpper: bool) -> RimFrame:
    Origin = Model.BasePoint
    Center = (
        Origin[0] / 10,
        Origin[1] / 10,
        (Origin[2] + (Model.Height if IsUpper else 0)) / 10,
    )
    Radius = (Model.TopRadius if IsUpper else Model.BottomRadius) / 10
    Point = (
        Center[0] + Radius * Cosine(-KHalfCircle),
        Center[1] + Radius * SineValue(-KHalfCircle),
        Center[2],
    )
    return RimFrame(
        Center,
        (0.0, 0.0, 1.0),
        (Radius, 0.0, 0.0),
        1.0,
        Point,
        Center,
        (0.0, 0.0, 1.0),
        (1.0, 0.0, 0.0),
        False,
        -KHalfCircle,
        KHalfCircle,
        False,
        IsUpper,
        not IsUpper,
        0,
    )
