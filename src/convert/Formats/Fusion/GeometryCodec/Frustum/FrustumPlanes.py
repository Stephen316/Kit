from convert.Formats.Fusion.GeometryCodec.Frustum.FrustumBody import FrustumBody
from convert.Formats.Fusion.GeometryCodec.Frustum.FrustumRims import FrustumRims
from convert.Formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord
from convert.Formats.Fusion.GeometryCodec.KeywordToken import KeywordToken
from convert.Formats.Fusion.GeometryCodec.MakeRecord import MakeRecord


# the frustum planes contract needs a shared interpretation so geometric values retain their native record boundaries
def FrustumPlanes(Model: FrustumBody) -> tuple[GeometryRecord, ...]:
    return tuple(
        MakeRecord(
            "plane-surface",
            (
                Center,
                (0.0, 0.0, 1.0),
                (1.0, 0.0, 0.0),
                KeywordToken("forward_v"),
                KeywordToken("I"),
                KeywordToken("I"),
                KeywordToken("I"),
                KeywordToken("I"),
            ),
        )
        for Center, _ in FrustumRims(Model)
    )
