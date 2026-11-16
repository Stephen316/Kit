from convert.Formats.Fusion.BrepCodec.Frustum.Models.FrustumFrame import FrustumFrame
from convert.Formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord
from convert.Formats.Fusion.GeometryCodec.MakeRecord import MakeRecord


# the frustum curves contract needs a shared interpretation so circular boundaries retain consistent cone and rim geometry
def FrustumCurves(Frame: FrustumFrame) -> tuple[GeometryRecord, ...]:
    return tuple(
        MakeRecord(
            "ellipse-curve",
            (
                Value.CenterCm,
                Value.Normal,
                Value.MajorVectorCm,
                float(Value.Ratio),
                False,
                False,
            ),
        )
        for Value in (Frame.Upper, Frame.Lower)
    )
