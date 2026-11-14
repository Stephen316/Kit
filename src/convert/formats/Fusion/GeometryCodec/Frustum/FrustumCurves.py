from convert.formats.Fusion.GeometryCodec.Frustum.FrustumBody import FrustumBody
from convert.formats.Fusion.GeometryCodec.Frustum.FrustumRims import FrustumRims
from convert.formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord
from convert.formats.Fusion.GeometryCodec.KeywordToken import KeywordToken
from convert.formats.Fusion.GeometryCodec.MakeRecord import MakeRecord


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
