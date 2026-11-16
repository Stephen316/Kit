# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

"""Construct the upper-pad distance display opening before its allocated owner."""

from dataclasses import dataclass as Dataclass
from math import isclose as IsClose, isfinite as IsFinite

from Display.Opening import EncodeDisplayOpen
from DisplayStyle import EncodeDefaultStyle, EncodeInlineDisplayText
from PartArchive import PartArchiveState
from RectDimDisplay import KDisplayMode
from WritePadDimLink import CheckDimObjects, CheckDimRoles, CheckDimStation
from convert.adapters.solidworks.Config.RootLayout import KConfigGen
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Sketch.GeometryTypes import SketchGeometry

# the lower sketch owns the first two visual keys in the distance display sequence
KFirstPadVisual = 12

# the witnessed bottom offset text has a separate normal lift
KBottomTextLift = 0.0001


# the annotation belongs to the active sketch and its measured supporting plane
@Dataclass(frozen=True, slots=True)
class PadDimView:
    SketchIndex: int
    VisualIndex: int
    PlaneOrigin: tuple[float, float, float]
    PlaneNormal: tuple[float, float, float]
    TextWorld: tuple[float, float, float]


# the opening binds its own visual slot and the same positive support plane
def CheckDimView(
    ViewValue: PadDimView, Geometry: SketchGeometry, SlotValue: int
) -> None:
    RequireArch(
        type(ViewValue.SketchIndex) is int
        and ViewValue.SketchIndex == Geometry["object_index"]
        and type(ViewValue.VisualIndex) is int
        and ViewValue.VisualIndex == KFirstPadVisual + SlotValue,
        True,
        "same active sketch and ordered visual index",
    )
    RequireArch(
        len(ViewValue.PlaneOrigin)
        == len(ViewValue.PlaneNormal)
        == len(ViewValue.TextWorld)
        == 3
        and all(
            map(
                IsFinite,
                (*ViewValue.PlaneOrigin, *ViewValue.PlaneNormal, *ViewValue.TextWorld),
            )
        )
        and ViewValue.PlaneOrigin[:2] == (0, 0)
        and ViewValue.PlaneOrigin[2] > 0
        and ViewValue.PlaneNormal == (0, 0, 1),
        True,
        "finite world annotation on a positive xy support",
    )
    LiftValue = KBottomTextLift if SlotValue == 3 else 0.0
    RequireArch(
        IsClose(
            ViewValue.TextWorld[2],
            ViewValue.PlaneOrigin[2] + LiftValue,
            rel_tol=0.0,
            abs_tol=1e-12,
        ),
        True,
        "world annotation follows the owned support and witnessed normal lift",
    )


# the framing has no allocation until the separately constructed handle begins
def EncodePadDimOpen(
    Generation: int,
    StateValue: PartArchiveState,
    Geometry: SketchGeometry,
    SlotValue: int,
    DimensionId: int,
    ViewValue: PadDimView,
) -> bytes:
    RequireArch(Generation, KConfigGen, "upper-pad display opening generation")
    Objects = CheckDimStation(StateValue, Geometry, SlotValue)
    Rows = Geometry["length_dimensions"]
    RequireArch(
        len(Rows) == 4
        and all(len(DimValue["point_native_ids"]) == 2 for DimValue in Rows)
        and type(DimensionId) is int
        and Rows[SlotValue]["native_id"] == DimensionId,
        True,
        "same dimension role as the following display owner",
    )
    CheckDimObjects(Objects, Geometry, Rows)
    CheckDimRoles(Geometry, Rows)
    CheckDimView(ViewValue, Geometry, SlotValue)
    return (
        EncodeDisplayOpen(Generation, KDisplayMode, ViewValue.VisualIndex)
        + EncodeDefaultStyle()
        + EncodeInlineDisplayText(ViewValue.TextWorld, 1)
    )
