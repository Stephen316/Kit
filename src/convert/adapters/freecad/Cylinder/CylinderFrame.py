# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from math import hypot as Hypot, isfinite as IsFinite, tan as TanValue

from convert.geometry.Revolve.SweepVector import DotVector, OffsetVector
from interchange.brep.surfaces.BrepSurfaces import ConeSurface, CylinderSurface
from interchange.geometry.models.VectorSpace import SpaceVector

# normalized carrier axes must agree before lengths establish a trim
KAxisTolerance = 1e-9


# analytic trim checks need a finite normalized direction from each carrier
def NormCylinder(Value: SpaceVector) -> SpaceVector | None:
    Length = Hypot(Value.x, Value.y, Value.z)
    if not IsFinite(Length) or Length == 0.0:
        return None
    return SpaceVector(Value.x / Length, Value.y / Length, Value.z / Length)


# radial displacement and axial station are independent of the periodic seam
def ProjectCylinder(
    PointValue: SpaceVector, Origin: SpaceVector, AxisValue: SpaceVector
) -> tuple[float, SpaceVector]:
    Delta = SpaceVector(
        PointValue.x - Origin.x, PointValue.y - Origin.y, PointValue.z - Origin.z
    )
    Station = DotVector(Delta, AxisValue)
    return Station, OffsetVector(Delta, AxisValue, -Station)


# euclidean residual bounds vertex and generator agreement in physical units
def CylinderGap(First: SpaceVector, Second: SpaceVector) -> float:
    return Hypot(First.x - Second.x, First.y - Second.y, First.z - Second.z)


# the neutral cone convention decreases radius along the positive surface axis
def RuledRadius(Surface: CylinderSurface | ConeSurface, Station: float) -> float:
    if isinstance(Surface, ConeSurface):
        return Surface.radius - Station * TanValue(Surface.half_angle)
    return Surface.radius
