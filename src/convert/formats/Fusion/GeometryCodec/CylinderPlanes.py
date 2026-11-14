from convert.formats.Fusion.GeometryCodec.CylinderBody import CylinderBody
from convert.formats.Fusion.GeometryCodec.CylinderCenters import GetCenters
from convert.formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord
from convert.formats.Fusion.GeometryCodec.KeywordToken import KeywordToken
from convert.formats.Fusion.GeometryCodec.MakeRecord import MakeRecord


def BuildPlanes(Model: CylinderBody) -> tuple[GeometryRecord, ...]:
    Bound = KeywordToken("I")
    return tuple(
        MakeRecord(
            "plane-surface",
            (
                Center,
                (0.0, 0.0, 1.0),
                (1.0, 0.0, 0.0),
                KeywordToken("forward_v"),
                Bound,
                Bound,
                Bound,
                Bound,
            ),
        )
        for Center in GetCenters(Model)
    )
