from convert.Formats.Fusion.GeometryCodec.CylinderBody import CylinderBody
from convert.Formats.Fusion.GeometryCodec.CylinderCenters import GetCenters
from convert.Formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord
from convert.Formats.Fusion.GeometryCodec.KeywordToken import KeywordToken
from convert.Formats.Fusion.GeometryCodec.MakeRecord import MakeRecord


# the planes operation needs a consistent construction rule so geometric values retain their native record boundaries
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
