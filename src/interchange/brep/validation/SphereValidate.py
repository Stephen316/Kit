# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from math import isfinite as IsFinite

from interchange.brep.surfaces.BrepSurfaces import SphereSurface
from interchange.brep.validation.BrepRoundFrame import IsRoundFrame


# an untrimmed sphere needs a regular carrier before it can close a solid
def IsFullSphere(Surface: SphereSurface) -> bool:
    return (
        IsFinite(Surface.radius)
        and Surface.radius > 0.0
        and IsRoundFrame(Surface.center, Surface.axis, Surface.reference_direction)
    )
