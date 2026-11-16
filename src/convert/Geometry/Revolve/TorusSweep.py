from typing import cast as CastValue
from math import isfinite as IsFinite
from math import pi as CirclePi

from convert.Geometry.Revolve.TorusBounds import GetTorusBounds
from convert.Geometry.Revolve.WholeSweep import BuildWholeSolid
from interchange.brep.Surfaces.BrepSurfaces import TorusSurface
from interchange.brep.Topology.BrepMath import IsFiniteSpace
from interchange.brep.Topology.BrepModel import BrepModel
from interchange.brep.Validation.RingTorusValidate import IsRingTorus
from interchange.geometry.Models.BoundingBox import BoundingBox
from interchange.geometry.Models.VectorSpace import SpaceVector


# a full circle sweep closes analytically without invented trims or seam entities
def BuildTorusSweep(
    BodyId: str,
    Center: SpaceVector,
    AxisDirection: SpaceVector,
    Radial: SpaceVector,
    MajorRadius: float,
    MinorRadius: float,
) -> tuple[BrepModel, float, float, BoundingBox]:
    if not isinstance(CastValue(object, BodyId), str) or not BodyId.strip():
        raise ValueError("Torus Revolve requires a design body identity")
    Prefix = f"{BodyId}-sweep"
    Surface = TorusSurface(
        f"{Prefix}-surface", Center, AxisDirection, Radial, MajorRadius, MinorRadius
    )
    if not IsRingTorus(Surface):
        raise ValueError("Torus Revolve requires a finite orthonormal ring torus")
    SurfaceArea = 4.0 * CirclePi * CirclePi * (MajorRadius * MinorRadius)
    Volume = SurfaceArea * (MinorRadius * 0.5)
    Bounds = GetTorusBounds(Center, AxisDirection, MajorRadius, MinorRadius)
    if not (
        IsFinite(Volume)
        and Volume > 0.0
        and IsFinite(SurfaceArea)
        and SurfaceArea > 0.0
        and IsFiniteSpace(Bounds.minimum)
        and IsFiniteSpace(Bounds.maximum)
    ):
        raise ValueError("Torus Revolve measures exceed finite geometry")
    Model = BuildWholeSolid(BodyId, Surface)
    return Model, Volume, SurfaceArea, Bounds
