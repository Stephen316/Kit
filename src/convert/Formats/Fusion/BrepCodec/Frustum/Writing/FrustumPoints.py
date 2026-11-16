from convert.Formats.Fusion.BrepCodec.Frustum.Models.FrustumFrame import FrustumFrame
from convert.Formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord
from convert.Formats.Fusion.GeometryCodec.MakeRecord import MakeRecord


# the frustum points contract needs a shared interpretation so circular boundaries retain consistent cone and rim geometry
def FrustumPoints(Frame: FrustumFrame) -> tuple[GeometryRecord, ...]:
    return tuple(
        MakeRecord("point", (Value.PointCm,)) for Value in (Frame.Upper, Frame.Lower)
    )
