# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from math import hypot as Hypot

from interchange.geometry.models.BoundingBox import BoundingBox
from interchange.geometry.models.VectorSpace import SpaceVector


# projected major circle radii and the tube radius bound every cartesian direction
def GetTorusBounds(
    Center: SpaceVector, Axis: SpaceVector, MajorRadius: float, MinorRadius: float
) -> BoundingBox:
    Length = Hypot(Axis.x, Axis.y, Axis.z)
    Extents = (
        MajorRadius * (Hypot(Axis.y, Axis.z) / Length) + MinorRadius,
        MajorRadius * (Hypot(Axis.z, Axis.x) / Length) + MinorRadius,
        MajorRadius * (Hypot(Axis.x, Axis.y) / Length) + MinorRadius,
    )
    Coordinates = (Center.x, Center.y, Center.z)
    return BoundingBox(
        SpaceVector(*(Value - Extent for Value, Extent in zip(Coordinates, Extents))),
        SpaceVector(*(Value + Extent for Value, Extent in zip(Coordinates, Extents))),
    )
