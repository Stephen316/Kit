from convert.Formats.Fusion.GeometryCodec.CylinderBody import CylinderBody
from convert.Formats.Fusion.GeometryCodec.CylinderCenters import GetCenters
from convert.Formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord
from convert.Formats.Fusion.GeometryCodec.KeywordToken import KeywordToken
from convert.Formats.Fusion.GeometryCodec.MakeRecord import MakeRecord


# the curves operation needs a consistent construction rule so geometric values retain their native record boundaries
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
