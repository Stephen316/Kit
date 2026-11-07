# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from math import hypot as Hypot
from math import isclose as IsClose
from math import isfinite as IsFinite

from interchange.brep.surfaces.BrepSurfaces import TorusSurface
from interchange.brep.topology.BrepMath import IsFiniteSpace


# a regular torus without a trim boundary must be a nonsingular ring
def IsRingTorus(Surface: TorusSurface) -> bool:
    Axis, Radial = Surface.axis, Surface.reference_direction
    return (
        IsFiniteSpace(Surface.center)
        and IsFinite(Surface.major_radius)
        and IsFinite(Surface.minor_radius)
        and Surface.major_radius > Surface.minor_radius > 0.0
        and IsClose(Hypot(Axis.x, Axis.y, Axis.z), 1.0, rel_tol=0.0, abs_tol=1e-9)
        and IsClose(Hypot(Radial.x, Radial.y, Radial.z), 1.0, rel_tol=0.0, abs_tol=1e-9)
        and abs(Axis.x * Radial.x + Axis.y * Radial.y + Axis.z * Radial.z) <= 1e-9
    )
