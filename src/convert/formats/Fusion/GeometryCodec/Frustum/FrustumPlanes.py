from convert.formats.Fusion.GeometryCodec.Frustum.FrustumBody import FrustumBody
from convert.formats.Fusion.GeometryCodec.Frustum.FrustumRims import FrustumRims
from convert.formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord
from convert.formats.Fusion.GeometryCodec.KeywordToken import KeywordToken
from convert.formats.Fusion.GeometryCodec.MakeRecord import MakeRecord


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
