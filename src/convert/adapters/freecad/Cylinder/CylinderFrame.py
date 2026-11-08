# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from math import hypot as Hypot, isfinite as IsFinite

from convert.geometry.Revolve.SweepVector import DotVector, OffsetVector
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


# Euclidean residual bounds vertex and generator agreement in physical units
def CylinderGap(First: SpaceVector, Second: SpaceVector) -> float:
    return Hypot(First.x - Second.x, First.y - Second.y, First.z - Second.z)
