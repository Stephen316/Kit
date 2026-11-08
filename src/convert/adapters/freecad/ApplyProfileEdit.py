# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import replace as Replace

from convert.adapters.freecad.EditableExt import FindEditFrame
from convert.adapters.freecad.EditExtProfile import GetCenterPoint, GetEditCircle
from convert.adapters.freecad.EditExtRing import GetEditRing
from convert.adapters.freecad.EditExtSolid import KEditProfile
from convert.adapters.freecad.EditRing.RingChange import CheckRingEdit
from interchange.document.models.DocumentModel import CadDocument
from interchange.geometry.models.GeometryCurves import CircleGeometry
from interchange.geometry.models.Sketch import Sketch
from interchange.geometry.models.Transform import Transform


# only the selected circle and its proven center point may change geometry
def CheckProfEdit(
    Original: Sketch,
    Edited: Sketch,
    Before: CircleGeometry,
    After: CircleGeometry,
) -> None:
    if (
        len(Edited.entities) != len(Original.entities)
        or Replace(Edited, entities=Original.entities) != Original
    ):
        raise ValueError("FreeCAD editable extrusion sketch identity changed")
    ProfileId = Original.closed_profile_entity_ids[0][0]
    Allowed = {ProfileId}
    if Before.center != After.center:
        OldCenter = GetCenterPoint(Original)
        NewCenter = GetCenterPoint(Edited)
        if OldCenter is None or NewCenter is None or OldCenter.id != NewCenter.id:
            raise ValueError(
                "FreeCAD editable extrusion center point disagrees with the circle"
            )
        Allowed.add(OldCenter.id)
    for Previous, Current in zip(Original.entities, Edited.entities, strict=True):
        if Replace(Current, geometry=Previous.geometry) != Previous:
            raise ValueError(
                "FreeCAD editable extrusion sketch entity identity changed"
            )
        if Previous.id not in Allowed and Previous.geometry != Current.geometry:
            raise ValueError(
                "FreeCAD editable extrusion has an unrelated sketch geometry edit"
            )


# a rebuilt body and its sketch must use the same proven edited circle and frame
def GetProfileEdits(
    DocValue: CadDocument,
    Profile: KEditProfile,
    FrameValue: Transform,
    EditedSketch: Sketch | None,
) -> tuple[Sketch, ...]:
    Feature = DocValue.feature_timeline[-1]
    Found = FindEditFrame(DocValue, Feature.sketch_id)
    if Found is None or Found[1].transform != FrameValue:
        raise ValueError("FreeCAD editable extrusion source profile frame changed")
    Original = Found[0]
    ReadProfile = GetEditCircle if isinstance(Profile, CircleGeometry) else GetEditRing
    Before = ReadProfile(Feature, Original)
    Current = Original if EditedSketch is None else EditedSketch
    if Before is None or ReadProfile(Feature, Current) != Profile:
        raise ValueError(
            "FreeCAD editable extrusion rebuilt profile disagrees with its sketch"
        )
    if Current == Original:
        return DocValue.sketches
    if isinstance(Before, CircleGeometry) and isinstance(Profile, CircleGeometry):
        CheckProfEdit(Original, Current, Before, Profile)
    else:
        CheckRingEdit(Original, Current)
    return tuple(
        Current if Value.id == Original.id else Value for Value in DocValue.sketches
    )
