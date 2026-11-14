from math import cos as Cosine
from math import pi as KCircleHalf
from math import sin as SineValue

from convert.formats.Fusion.GeometryCodec.CylinderBody import CylinderBody
from convert.formats.Fusion.GeometryCodec.CylinderCenters import GetCenters
from convert.formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord
from convert.formats.Fusion.GeometryCodec.MakeRecord import MakeRecord


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
