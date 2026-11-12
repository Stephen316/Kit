from math import hypot as Hypot

from interchange.geometry.models.BoundingBox import BoundingBox
from interchange.geometry.models.VectorSpace import SpaceVector


# projected major circle radii and the tube radius bound every cartesian direction
def GetTorusBounds(
    Center: SpaceVector, AxisValue: SpaceVector, MajorRadius: float, MinorRadius: float
) -> BoundingBox:
    Length = Hypot(AxisValue.x, AxisValue.y, AxisValue.z)
    Extents = (
        MajorRadius * (Hypot(AxisValue.y, AxisValue.z) / Length) + MinorRadius,
        MajorRadius * (Hypot(AxisValue.z, AxisValue.x) / Length) + MinorRadius,
        MajorRadius * (Hypot(AxisValue.x, AxisValue.y) / Length) + MinorRadius,
    )
    Coordinates = (Center.x, Center.y, Center.z)
    return BoundingBox(
        SpaceVector(*(Value - Extent for Value, Extent in zip(Coordinates, Extents))),
        SpaceVector(*(Value + Extent for Value, Extent in zip(Coordinates, Extents))),
    )
