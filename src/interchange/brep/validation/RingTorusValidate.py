# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from math import isfinite as IsFinite

from interchange.brep.surfaces.BrepSurfaces import TorusSurface
from interchange.brep.validation.BrepRoundFrame import IsRoundFrame


# a regular torus without a trim boundary must be a nonsingular ring
def IsRingTorus(Surface: TorusSurface) -> bool:
    return (
        IsFinite(Surface.major_radius)
        and IsFinite(Surface.minor_radius)
        and Surface.major_radius > Surface.minor_radius > 0.0
        and IsRoundFrame(Surface.center, Surface.axis, Surface.reference_direction)
    )
