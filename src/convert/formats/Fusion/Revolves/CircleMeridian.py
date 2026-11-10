# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt


from math import hypot as Hypot

from convert.geometry.Revolve.SweepVector import DotVector, OffsetVector
from interchange.geometry.models.GeometryCurves import CircleGeometry
from interchange.geometry.models.Transform import Transform
from interchange.geometry.models.VectorSpace import SpaceVector


# a whole circle supplies the torus centerline radius and radial direction
def ReadTorusFrame(
    FrameValue: Transform,
    Profile: CircleGeometry,
    AxisOrigin: SpaceVector,
    AxisDirection: SpaceVector,
) -> tuple[SpaceVector, SpaceVector, float]:
    CircleCenter = OffsetVector(
        OffsetVector(FrameValue.origin, FrameValue.x_axis, Profile.center.x),
        FrameValue.y_axis,
        Profile.center.y,
    )
    Offset = OffsetVector(CircleCenter, AxisOrigin, -1.0)
    Center = OffsetVector(AxisOrigin, AxisDirection, DotVector(Offset, AxisDirection))
    Radial = OffsetVector(CircleCenter, Center, -1.0)
    MajorRadius = Hypot(Radial.x, Radial.y, Radial.z)
    if not MajorRadius > Profile.radius:
        raise ValueError("Fusion full circular Revolve requires a ring torus profile")
    return (
        Center,
        SpaceVector(
            Radial.x / MajorRadius, Radial.y / MajorRadius, Radial.z / MajorRadius
        ),
        MajorRadius,
    )
