# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

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
