# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from interchange.geometry.models.VectorSpace import SpaceVector


# frame qualification depends on dot products between spatial directions
def DotVector(First: SpaceVector, Second: SpaceVector) -> float:
    return First.x * Second.x + First.y * Second.y + First.z * Second.z


# the signed cross product determines the sweep direction and cap normals
def CrossVector(First: SpaceVector, Second: SpaceVector) -> SpaceVector:
    return SpaceVector(
        First.y * Second.z - First.z * Second.y,
        First.z * Second.x - First.x * Second.z,
        First.x * Second.y - First.y * Second.x,
    )


# scaled displacement preserves the units of the spatial point
def OffsetVector(
    Origin: SpaceVector, Direction: SpaceVector, Factor: float
) -> SpaceVector:
    return SpaceVector(
        Origin.x + Direction.x * Factor,
        Origin.y + Direction.y * Factor,
        Origin.z + Direction.z * Factor,
    )
