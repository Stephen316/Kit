from convert.formats.Fusion.BrepCodec.Frustum.Models.ConeFrame import ConeFrame
from convert.formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord
from convert.formats.Fusion.GeometryCodec.MakeRecord import MakeRecord


def FrustumSurface(Surface: ConeFrame) -> GeometryRecord:
    return MakeRecord(
        "cone-surface",
        (
            Surface.OriginCm,
            Surface.Axis,
            Surface.MajorVectorCm,
            float(Surface.Ratio),
            False,
            False,
            float(Surface.SineAngle),
            float(Surface.CosineAngle),
            float(Surface.ScaleCm),
            Surface.ReverseSense,
            False,
            False,
            False,
            False,
        ),
    )
