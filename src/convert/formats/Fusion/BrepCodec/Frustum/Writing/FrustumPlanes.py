from convert.formats.Fusion.BrepCodec.Frustum.Models.FrustumFrame import FrustumFrame
from convert.formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord
from convert.formats.Fusion.GeometryCodec.MakeRecord import MakeRecord


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
