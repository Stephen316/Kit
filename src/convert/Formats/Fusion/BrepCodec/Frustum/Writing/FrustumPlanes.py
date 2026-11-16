from convert.Formats.Fusion.BrepCodec.Frustum.Models.FrustumFrame import FrustumFrame
from convert.Formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord
from convert.Formats.Fusion.GeometryCodec.MakeRecord import MakeRecord


# the frustum planes contract needs a shared interpretation so circular boundaries retain consistent cone and rim geometry
def FrustumPlanes(Frame: FrustumFrame) -> tuple[GeometryRecord, ...]:
    return tuple(
        MakeRecord(
            "plane-surface",
            (
                Value.PlaneOriginCm,
                Value.PlaneNormal,
                Value.PlaneBasis,
                Value.PlaneReverseV,
                False,
                False,
                False,
                False,
            ),
        )
        for Value in (Frame.Upper, Frame.Lower)
    )
