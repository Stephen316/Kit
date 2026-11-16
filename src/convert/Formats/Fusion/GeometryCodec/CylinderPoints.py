from math import cos as Cosine
from math import pi as KCircleHalf
from math import sin as SineValue

from convert.Formats.Fusion.GeometryCodec.CylinderBody import CylinderBody
from convert.Formats.Fusion.GeometryCodec.CylinderCenters import GetCenters
from convert.Formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord
from convert.Formats.Fusion.GeometryCodec.MakeRecord import MakeRecord


# the points operation needs a consistent construction rule so geometric values retain their native record boundaries
def BuildPoints(Model: CylinderBody) -> tuple[GeometryRecord, ...]:
    return tuple(
        MakeRecord(
            "point",
            (
                (
                    CoordX + Model.Radius * Cosine(-KCircleHalf),
                    CoordY + Model.Radius * SineValue(-KCircleHalf),
                    CoordZ,
                ),
            ),
        )
        for CoordX, CoordY, CoordZ in GetCenters(Model)
    )
