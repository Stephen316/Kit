from convert.formats.Fusion.BrepCodec.Frustum.Models.FrustumFrame import FrustumFrame
from convert.formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord
from convert.formats.Fusion.GeometryCodec.MakeRecord import MakeRecord


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
