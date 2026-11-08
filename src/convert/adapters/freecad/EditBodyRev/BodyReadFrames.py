# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import replace as Replace

from convert.adapters.freecad.EditRead.EditObjects import RequireEditObj
from convert.adapters.freecad.EditRead.EditPlacement import KEditFrameTol, ReadEditFrame
from convert.adapters.freecad.EditRead.EditProfile import CheckEditPlane
from convert.adapters.freecad.Native import IsTransformNear, NativeObject
from convert.geometry.Extrude.Polygon.PrismFrame import CheckPrismFrame
from interchange.geometry.models.SupportPlane import SupportPlane
from interchange.geometry.models.Transform import Transform


# independent authored planes can move only when the linked sketch agrees with the saved rigid frame
def ReadBodyFrame(
    Objects: tuple[NativeObject, ...],
    SketchValue: NativeObject,
    Original: SupportPlane,
) -> Transform:
    Plane = RequireEditObj(Objects, Original.id, "App::Plane")
    Frame = ReadEditFrame(Plane, "Placement")
    CheckPrismFrame(Frame)
    CheckEditPlane(SketchValue, Plane, Replace(Original, transform=Frame))
    return (
        Original.transform
        if IsTransformNear(Frame, Original.transform, KEditFrameTol)
        else Frame
    )
