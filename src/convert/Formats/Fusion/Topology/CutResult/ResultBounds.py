from interchange.geometry.Models.BoundingBox import BoundingBox
from interchange.geometry.Models.VectorSpace import SpaceVector


# planar linear carrier extrema are bounded by the owned saved vertices
def ResultBounds(Points: dict[int, SpaceVector]) -> BoundingBox:
    Coords = tuple(Points.values())
    Minimum = SpaceVector(
        min(Point.x for Point in Coords),
        min(Point.y for Point in Coords),
        min(Point.z for Point in Coords),
    )
    Maximum = SpaceVector(
        max(Point.x for Point in Coords),
        max(Point.y for Point in Coords),
        max(Point.z for Point in Coords),
    )
    if Minimum.x >= Maximum.x or Minimum.y >= Maximum.y or Minimum.z >= Maximum.z:
        raise ValueError("Fusion Cut result is degenerate")
    return BoundingBox(Minimum, Maximum)
