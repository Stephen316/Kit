from convert.formats.Fusion.BrepCodec.Frustum.Models.FrustumFrame import FrustumFrame
from convert.formats.Fusion.GeometryCodec.Frustum.FrustumBody import FrustumBody


def ReadFrustumBody(Frame: FrustumFrame) -> FrustumBody:
    Origin = Frame.Lower.CenterCm
    return FrustumBody(
        Frame.Lower.MajorVectorCm[0] * 10,
        Frame.Upper.MajorVectorCm[0] * 10,
        (Frame.Upper.CenterCm[2] - Origin[2]) * 10,
        (Origin[0] * 10, Origin[1] * 10, Origin[2] * 10),
    )
