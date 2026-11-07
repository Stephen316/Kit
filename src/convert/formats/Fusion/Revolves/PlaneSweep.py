# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from math import atan2 as AtanTwo, hypot as Hypot, isclose as IsClose, pi as Pi
from operator import mul as Mul

from convert.formats.Fusion.Revolves.ProfileMeridian import CalcMeridian
from interchange.geometry.models.GeometryCurves import LineGeometry
from interchange.geometry.models.Transform import Transform
from interchange.geometry.models.VectorSpace import SpaceVector


# plane limits are evaluated in the positively directed sketch frame
def DerivePlaneSpan(
    SketchFrame: Transform,
    ProfileLines: tuple[LineGeometry, ...],
    AxisOrigin: SpaceVector,
    AxisDirection: SpaceVector,
    TargetFrames: tuple[Transform, ...],
) -> tuple[SpaceVector, float, float]:
    if len(ProfileLines) != 4:
        raise ValueError("Plane limited Fusion Revolve requires a four line profile")
    if len(TargetFrames) not in (1, 2):
        raise ValueError("Fusion Revolve requires one or two target planes")
    AxisTuple, Radial = CalcMeridian(
        SketchFrame, ProfileLines, AxisOrigin, AxisDirection
    )
    Tangent = (SketchFrame.z_axis.x, SketchFrame.z_axis.y, SketchFrame.z_axis.z)
    Roots: list[float] = []
    for Target in TargetFrames:
        Normal = (Target.z_axis.x, Target.z_axis.y, Target.z_axis.z)
        Offset = (
            Target.origin.x - AxisOrigin.x,
            Target.origin.y - AxisOrigin.y,
            Target.origin.z - AxisOrigin.z,
        )
        AlongAxis, AlongRadial, AlongTangent, Distance = (
            sum(map(Mul, Normal, Vector))
            for Vector in (AxisTuple, Radial, Tangent, Offset)
        )
        if (
            not IsClose(Hypot(*Normal), 1.0, rel_tol=0.0, abs_tol=1e-9)
            or not IsClose(AlongAxis, 0.0, abs_tol=1e-9)
            or not IsClose(Distance, 0.0, abs_tol=1e-8)
            or not IsClose(
                Hypot(AlongRadial, AlongTangent), 1.0, rel_tol=0.0, abs_tol=1e-9
            )
        ):
            raise ValueError("Fusion Revolve target plane must contain the axis")
        RootAngle = AtanTwo(-AlongRadial, AlongTangent) % Pi
        if min(RootAngle, Pi - RootAngle) <= 1e-9:
            raise ValueError("Fusion Revolve target plane coincides with the sketch")
        Roots.append(RootAngle)
    EffectiveAxis = SpaceVector(*AxisTuple)
    if len(Roots) == 1:
        return EffectiveAxis, 0.0, Roots[0]
    Earlier, Later = sorted(Roots)
    if Later - Earlier <= 1e-9:
        raise ValueError("Fusion Revolve target planes coincide")
    return EffectiveAxis, Later, Earlier + Pi
