from math import hypot as Hypot

from convert.formats.Fusion.GeometryCodec.Frustum.FrustumBody import FrustumBody
from convert.formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord
from convert.formats.Fusion.GeometryCodec.KeywordToken import KeywordToken
from convert.formats.Fusion.GeometryCodec.MakeRecord import MakeRecord


def FrustumSurface(Model: FrustumBody) -> GeometryRecord:
    RadiusDelta = Model.TopRadius - Model.BottomRadius
    SlantLength = Hypot(Model.Height, RadiusDelta)
    return MakeRecord(
        "cone-surface",
        (
            Model.BasePoint,
            (0.0, 0.0, 1.0),
            (Model.BottomRadius, 0.0, 0.0),
            1.0,
            KeywordToken("I"),
            KeywordToken("I"),
            RadiusDelta / SlantLength,
            Model.Height / SlantLength,
            Model.BottomRadius,
            KeywordToken("forward"),
            KeywordToken("I"),
            KeywordToken("I"),
            KeywordToken("I"),
            KeywordToken("I"),
        ),
    )
