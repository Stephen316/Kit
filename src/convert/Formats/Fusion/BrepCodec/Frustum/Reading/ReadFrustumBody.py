from convert.Formats.Fusion.BrepCodec.Frustum.Models.FrustumFrame import FrustumFrame
from convert.Formats.Fusion.GeometryCodec.Frustum.FrustumBody import FrustumBody


# the frustum body operation needs a distinct decoding boundary so circular boundaries retain consistent cone and rim geometry
def ReadFrustumBody(Frame: FrustumFrame) -> FrustumBody:
    Origin = Frame.Lower.CenterCm
    return FrustumBody(
        Frame.Lower.MajorVectorCm[0] * 10,
        Frame.Upper.MajorVectorCm[0] * 10,
        (Frame.Upper.CenterCm[2] - Origin[2]) * 10,
        (Origin[0] * 10, Origin[1] * 10, Origin[2] * 10),
    )
