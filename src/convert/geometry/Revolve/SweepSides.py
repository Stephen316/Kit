from math import atan2 as AtanTwo

from convert.geometry.Revolve.SweepVector import OffsetVector
from interchange.brep.surfaces.BrepSurfaces import (
    BrepSurface,
    ConeSurface,
    CylinderSurface,
    PlaneSurface,
)
from interchange.geometry.models.Transform import Transform
from interchange.geometry.models.VectorSpace import SpaceVector


# swept segments keep their exact planar cylindrical or conical carriers
def BuildSide(
    SurfaceId: str,
    First: tuple[float, float],
    Second: tuple[float, float],
    Frame: Transform,
) -> tuple[BrepSurface, bool]:
    Radius, Height = First
    DeltaRadius = Second[0] - Radius
    DeltaHeight = Second[1] - Height
    Origin = OffsetVector(Frame.origin, Frame.z_axis, Height)
    AxisValue, Radial = Frame.z_axis, Frame.x_axis
    if DeltaHeight == 0.0:
        Direction = -1.0 if DeltaRadius > 0.0 else 1.0
        Normal = SpaceVector(
            Direction * AxisValue.x, Direction * AxisValue.y, Direction * AxisValue.z
        )
        return PlaneSurface(SurfaceId, Origin, Normal, Radial), True
    if DeltaRadius == 0.0:
        return CylinderSurface(SurfaceId, Origin, AxisValue, Radial, Radius), (
            DeltaHeight > 0.0
        )
    if (DeltaHeight > 0.0) == (DeltaRadius > 0.0):
        AxisValue = SpaceVector(-AxisValue.x, -AxisValue.y, -AxisValue.z)
    Angle = AtanTwo(abs(DeltaRadius), abs(DeltaHeight))
    return ConeSurface(SurfaceId, Origin, AxisValue, Radial, Radius, Angle), (
        DeltaHeight > 0.0
    )
