# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from math import cos as Cos, sin as Sin

from interchange.geometry.models.Transform import Transform
from interchange.geometry.models.VectorSpace import SpaceVector


# exact angular directions keep cap and circle parameter origins aligned
def RotateRadial(Frame: Transform, Angle: float) -> SpaceVector:
    Cosine, Sine = Cos(Angle), Sin(Angle)
    Radial, Tangent = Frame.x_axis, Frame.y_axis
    return SpaceVector(
        Radial.x * Cosine + Tangent.x * Sine,
        Radial.y * Cosine + Tangent.y * Sine,
        Radial.z * Cosine + Tangent.z * Sine,
    )
