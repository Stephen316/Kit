from convert.Formats.Fusion.GeometryCodec.Frustum.FrustumBody import FrustumBody
from convert.Formats.Fusion.GeometryCodec.Frustum.FrustumRims import FrustumRims
from convert.Formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord
from convert.Formats.Fusion.GeometryCodec.KeywordToken import KeywordToken
from convert.Formats.Fusion.GeometryCodec.MakeRecord import MakeRecord


# the frustum curves contract needs a shared interpretation so geometric values retain their native record boundaries
def FrustumCurves(Model: FrustumBody) -> tuple[GeometryRecord, ...]:
    return tuple(
        MakeRecord(
            "ellipse-curve",
            (
                Center,
                (0.0, 0.0, 1.0),
                (Radius, 0.0, 0.0),
                1.0,
                KeywordToken("I"),
                KeywordToken("I"),
            ),
        )
        for Center, Radius in FrustumRims(Model)
    )
