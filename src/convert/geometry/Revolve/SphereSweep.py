from typing import cast as CastValue
from math import isfinite as IsFinite
from math import pi as CirclePi

from convert.geometry.Revolve.WholeSweep import BuildWholeSolid
from interchange.brep.surfaces.BrepSurfaces import SphereSurface
from interchange.brep.topology.BrepMath import IsFiniteSpace
from interchange.brep.topology.BrepModel import BrepModel
from interchange.brep.validation.SphereValidate import IsFullSphere
from interchange.geometry.models.BoundingBox import BoundingBox
from interchange.geometry.models.VectorSpace import SpaceVector


# a complete semicircle revolution creates one sphere without invented seam topology
def BuildSphere(
    BodyId: str,
    Center: SpaceVector,
    AxisDirection: SpaceVector,
    Radial: SpaceVector,
    Radius: float,
) -> tuple[BrepModel, float, float, BoundingBox]:
    if not isinstance(CastValue(object, BodyId), str) or not BodyId.strip():
        raise ValueError("Sphere Revolve requires a design body identity")
    Surface = SphereSurface(
        f"{BodyId}-sweep-surface", Center, AxisDirection, Radial, Radius
    )
    if not IsFullSphere(Surface):
        raise ValueError("Sphere Revolve requires a finite orthonormal sphere")
    SurfaceArea = 4.0 * CirclePi * (Radius * Radius)
    Volume = SurfaceArea * (Radius / 3.0)
    Bounds = BoundingBox(
        SpaceVector(Center.x - Radius, Center.y - Radius, Center.z - Radius),
        SpaceVector(Center.x + Radius, Center.y + Radius, Center.z + Radius),
    )
    if not (
        IsFinite(Volume)
        and Volume > 0.0
        and IsFinite(SurfaceArea)
        and SurfaceArea > 0.0
        and IsFiniteSpace(Bounds.minimum)
        and IsFiniteSpace(Bounds.maximum)
    ):
        raise ValueError("Sphere Revolve measures exceed finite geometry")
    return BuildWholeSolid(BodyId, Surface), Volume, SurfaceArea, Bounds
