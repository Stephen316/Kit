from convert.formats.Fusion.GeometryCodec.CylinderBody import CylinderBody
from convert.formats.Fusion.GeometryCodec.CylinderCenters import GetCenters
from convert.formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord
from convert.formats.Fusion.GeometryCodec.KeywordToken import KeywordToken
from convert.formats.Fusion.GeometryCodec.MakeRecord import MakeRecord


def BuildCurves(Model: CylinderBody) -> tuple[GeometryRecord, ...]:
    Bound = KeywordToken("I")
    return tuple(
        MakeRecord(
            "ellipse-curve",
            (
                Center,
                (0.0, 0.0, 1.0),
                (Model.Radius, 0.0, 0.0),
                1.0,
                Bound,
                Bound,
            ),
        )
        for Center in GetCenters(Model)
    )
