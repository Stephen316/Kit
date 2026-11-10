# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt


from dataclasses import dataclass as MakeDataClass
from math import hypot as Hypot

from convert.adapters.freecad.EditShape.CylinderRims import KAngleTolerance
from convert.adapters.freecad.EditShape.Scale.ScaleSpan import ReadScaleDomain
from convert.geometry.Opencascade import (
    ApplyDirection,
    DecodeFailure,
    KIdentityLocation,
    Tokens,
    VectorValue,
)
from convert.geometry.Revolve.SweepVector import CrossVector, OffsetVector
from interchange.brep.surfaces.BrepSurfaces import PlaneSurface
from interchange.geometry.models.VectorSpace import SpaceVector

# the affine reduction allows only numeric roundoff in spatial control points
KPlaneResidual = 1e-9


# an affine patch retains the native coordinates needed to verify trims
@MakeDataClass(frozen=True, slots=True)
class ScalePatch:
    Origin: SpaceVector
    Across: SpaceVector
    Upward: SpaceVector
    UDomain: tuple[float, float]
    VDomain: tuple[float, float]
    Plane: PlaneSurface

    # coordinates outside the spline domain cannot trace a bounded face
    def EvalPoint(self, Param: tuple[float, ...]) -> SpaceVector:
        UValue, VValue = Param
        ULower, UUpper = self.UDomain
        VLower, VUpper = self.VDomain
        if not ULower <= UValue <= UUpper or not VLower <= VValue <= VUpper:
            raise DecodeFailure("Scale trim lies outside its spline surface domain")
        return OffsetVector(
            OffsetVector(
                self.Origin, self.Across, (UValue - ULower) / (UUpper - ULower)
            ),
            self.Upward,
            (VValue - VLower) / (VUpper - VLower),
        )


# a planar reduction must preserve the native parameter basis and orientation
def ReadScalePatch(Cursor: Tokens, Index: int) -> ScalePatch:
    for Token in (b"9", b"0", b"0", b"0", b"0", b"1", b"1", b"2", b"2", b"2", b"2"):
        Cursor.ExpectToken(Token)
    Origin, AlongV, AlongU, Corner = (VectorValue(Cursor) for _ in range(4))
    UDomain = ReadScaleDomain(Cursor)
    VDomain = ReadScaleDomain(Cursor)
    Across = OffsetVector(AlongU, Origin, -1.0)
    Upward = OffsetVector(AlongV, Origin, -1.0)
    Predicted = OffsetVector(AlongU, Upward, 1.0)
    Residual = Hypot(
        Corner.x - Predicted.x, Corner.y - Predicted.y, Corner.z - Predicted.z
    )
    if not Residual <= KPlaneResidual:
        raise DecodeFailure("Scale spline surface has a nonzero bilinear term")
    AcrossUnit = ApplyDirection(KIdentityLocation, Across)
    UpwardUnit = ApplyDirection(KIdentityLocation, Upward)
    Normal = CrossVector(AcrossUnit, UpwardUnit)
    if Hypot(Normal.x, Normal.y, Normal.z) <= KAngleTolerance:
        raise DecodeFailure("Scale spline surface has a singular basis")
    Normal = ApplyDirection(KIdentityLocation, Normal)
    SideValue = CrossVector(Normal, AcrossUnit)
    Plane = PlaneSurface(
        f"freecad:scale:surface:{Index}",
        Origin,
        Normal,
        AcrossUnit,
        attributes={"reference_y": (SideValue.x, SideValue.y, SideValue.z)},
    )
    return ScalePatch(Origin, Across, Upward, UDomain, VDomain, Plane)
