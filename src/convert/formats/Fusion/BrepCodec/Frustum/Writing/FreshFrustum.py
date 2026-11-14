from math import hypot as Hypot

from convert.formats.Fusion.BrepCodec.Frustum.Models.ConeFrame import ConeFrame
from convert.formats.Fusion.BrepCodec.Frustum.Models.FrustumFrame import FrustumFrame
from convert.formats.Fusion.BrepCodec.Frustum.Writing.FreshRim import FreshRim
from convert.formats.Fusion.GeometryCodec.Frustum.FrustumBody import FrustumBody


def FreshFrustum(Model: FrustumBody) -> FrustumFrame:
    RadiusDelta = Model.TopRadius - Model.BottomRadius
    SlantLength = Hypot(Model.Height, RadiusDelta)
    Origin = Model.BasePoint
    Surface = ConeFrame(
        (Origin[0] / 10, Origin[1] / 10, Origin[2] / 10),
        (0.0, 0.0, 1.0),
        (Model.BottomRadius / 10, 0.0, 0.0),
        1.0,
        RadiusDelta / SlantLength,
        Model.Height / SlantLength,
        Model.BottomRadius / 10,
        False,
    )
    return FrustumFrame(Surface, FreshRim(Model, True), FreshRim(Model, False))
