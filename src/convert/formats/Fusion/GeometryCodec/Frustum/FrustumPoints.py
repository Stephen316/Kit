from math import cos as Cosine, pi as KHalfCircle, sin as SineValue

from convert.formats.Fusion.GeometryCodec.Frustum.FrustumBody import FrustumBody
from convert.formats.Fusion.GeometryCodec.Frustum.FrustumRims import FrustumRims
from convert.formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord
from convert.formats.Fusion.GeometryCodec.MakeRecord import MakeRecord


# the frustum points contract needs a shared interpretation so geometric values retain their native record boundaries
def FrustumPoints(Model: FrustumBody) -> tuple[GeometryRecord, ...]:
    return tuple(
        MakeRecord(
            "point",
            (
                (
                    Center[0] + Radius * Cosine(-KHalfCircle),
                    Center[1] + Radius * SineValue(-KHalfCircle),
                    Center[2],
                ),
            ),
        )
        for Center, Radius in FrustumRims(Model)
    )
