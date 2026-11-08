# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from math import isfinite as IsFinite

from convert.adapters.freecad.EditShape.CylinderFaces import (
    HasOppositeRims,
    IsCylinderCap,
    IsCylinderSide,
)
from convert.adapters.freecad.EditShape.CylinderRaw import (
    HasCylTrims,
    ReadCylinderRaw,
    ReadFaceHands,
)
from convert.adapters.freecad.EditShape.CylinderRims import (
    KPositionTolerance,
    ReadCylRims,
    ReadCylSeam,
)
from convert.adapters.freecad.EditShape.CylinderShell import (
    HasCylShell,
    ReadCylFaces,
)
from convert.geometry.Extrude.Polygon.PrismFrame import CheckPrismFrame, PlacePrismPoint
from convert.geometry.Opencascade import DecodeAsciiBrep
from interchange.brep.surfaces.BrepSurfaces import BrepSurface, CylinderSurface
from interchange.geometry.models.GeometryCurves import CircleGeometry
from interchange.geometry.models.Transform import Transform

# editable circular extrusions need only a small analytic shape payload
KMaxCylinderBytes = 32_768


# placed surfaces retain their original carrier index for orientation checks
def FaceHand(Hands: dict[int, int], Surface: BrepSurface) -> int:
    Index = Surface.attributes.get("opencascade_index")
    return Hands[Index] if isinstance(Index, int) else 0


# geometry readback must agree with the native extrusion independently of editable properties
def IsEditCylinder(
    ShapeData: bytes, Frame: Transform, Profile: CircleGeometry, DistanceMm: float
) -> bool:
    if (
        len(ShapeData) > KMaxCylinderBytes
        or not IsFinite(DistanceMm)
        or not IsFinite(Profile.radius)
        or not IsFinite(Profile.center.x)
        or not IsFinite(Profile.center.y)
        or min(abs(DistanceMm), Profile.radius) <= 2.0 * KPositionTolerance
    ):
        return False
    try:
        CheckPrismFrame(Frame)
        Centers = (
            PlacePrismPoint(Frame, Profile.center, min(0.0, DistanceMm)),
            PlacePrismPoint(Frame, Profile.center, max(0.0, DistanceMm)),
        )
        Model = DecodeAsciiBrep(ShapeData, IdPrefix="freecad:edit-cylinder")
        if Model is None or not HasCylShell(Model):
            return False
        RimValues = ReadCylRims(Model, Centers, Frame.z_axis, Profile.radius)
        if not RimValues:
            return False
        SeamId = ReadCylSeam(Model, RimValues, Frame.z_axis)
        if SeamId is None:
            return False
        Faces = ReadCylFaces(Model)
        Sides = [Value for Value in Faces if isinstance(Value.Surface, CylinderSurface)]
        if len(Sides) != 1:
            return False
        RawValue = ReadCylinderRaw(ShapeData)
        Hands = ReadFaceHands(RawValue)
        SideFace = Sides[0]
        CapFaces = tuple(Value for Value in Faces if Value is not SideFace)
        return (
            IsCylinderSide(
                SideFace,
                RimValues,
                SeamId,
                Centers[0],
                Frame.z_axis,
                Profile.radius,
                FaceHand(Hands, SideFace.Surface),
            )
            and all(
                sum(
                    IsCylinderCap(
                        FaceValue,
                        RimValue,
                        Center,
                        Frame.z_axis,
                        Outward,
                        FaceHand(Hands, FaceValue.Surface),
                    )
                    for FaceValue in CapFaces
                )
                == 1
                for RimValue, Center, Outward in zip(
                    RimValues, Centers, (-1, 1), strict=True
                )
            )
            and HasOppositeRims(SideFace, CapFaces)
            and HasCylTrims(RawValue)
        )
    except (KeyError, TypeError, ValueError, OverflowError, RecursionError):
        return False
