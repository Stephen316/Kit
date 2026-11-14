from convert.formats.Fusion.BrepCodec.Frustum.Models.FrustumFrame import FrustumFrame
from convert.formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord
from convert.formats.Fusion.GeometryCodec.MakeRecord import MakeRecord


def FrustumPoints(Frame: FrustumFrame) -> tuple[GeometryRecord, ...]:
    return tuple(
        MakeRecord("point", (Value.PointCm,)) for Value in (Frame.Upper, Frame.Lower)
    )
