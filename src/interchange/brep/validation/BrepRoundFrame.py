# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from math import hypot as Hypot
from math import isclose as IsClose

from interchange.brep.topology.BrepMath import IsFiniteSpace
from interchange.geometry.models.VectorSpace import SpaceVector


# periodic carriers need a finite center and orthonormal parameter frame
def IsRoundFrame(
    Center: SpaceVector, AxisValue: SpaceVector, Radial: SpaceVector
) -> bool:
    return (
        IsFiniteSpace(Center)
        and IsClose(
            Hypot(AxisValue.x, AxisValue.y, AxisValue.z), 1.0, rel_tol=0.0, abs_tol=1e-9
        )
        and IsClose(Hypot(Radial.x, Radial.y, Radial.z), 1.0, rel_tol=0.0, abs_tol=1e-9)
        and abs(
            AxisValue.x * Radial.x + AxisValue.y * Radial.y + AxisValue.z * Radial.z
        )
        <= 1e-9
    )
