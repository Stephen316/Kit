from convert.formats.Fusion.GeometryCodec.CylinderBody import CylinderBody
from convert.formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord
from convert.formats.Fusion.GeometryCodec.KeywordToken import KeywordToken
from convert.formats.Fusion.GeometryCodec.MakeRecord import MakeRecord


def BuildSurface(Model: CylinderBody) -> GeometryRecord:
    Bound = KeywordToken("I")
    return MakeRecord(
        "cone-surface",
        (
            Model.BasePoint,
            (0.0, 0.0, 1.0),
            (Model.Radius, 0.0, 0.0),
            1.0,
            Bound,
            Bound,
            0.0,
            1.0,
            Model.Radius,
            KeywordToken("forward"),
            Bound,
            Bound,
            Bound,
            Bound,
        ),
    )
