# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from math import hypot as Hypot
from math import isclose as IsClose

from interchange.brep.topology.BrepMath import IsFiniteSpace
from interchange.geometry.models.VectorSpace import SpaceVector


# periodic carriers need a finite center and orthonormal parameter frame
def IsRoundFrame(Center: SpaceVector, Axis: SpaceVector, Radial: SpaceVector) -> bool:
    return (
        IsFiniteSpace(Center)
        and IsClose(Hypot(Axis.x, Axis.y, Axis.z), 1.0, rel_tol=0.0, abs_tol=1e-9)
        and IsClose(Hypot(Radial.x, Radial.y, Radial.z), 1.0, rel_tol=0.0, abs_tol=1e-9)
        and abs(Axis.x * Radial.x + Axis.y * Radial.y + Axis.z * Radial.z) <= 1e-9
    )
