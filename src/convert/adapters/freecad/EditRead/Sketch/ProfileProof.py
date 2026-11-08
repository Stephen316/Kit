# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from collections.abc import Mapping
from dataclasses import replace as Replace

from convert.adapters.freecad.Archive import JsonProp
from convert.adapters.freecad.EditExtProfile import GetCenterPoint
from convert.adapters.freecad.EditRead.Sketch.ProfileRule import CheckProfileRow
from convert.adapters.freecad.EditRead.Sketch.SavedEntity import IsSameCoord
from convert.adapters.freecad.EditRead.Sketch.SavedSketchGeom import ReadSketchGeom
from convert.adapters.freecad.EditRead.Sketch.SketchDefaults import (
    CheckExtensions,
    CheckSketchOpts,
)
from convert.adapters.freecad.EditRead.XmlField import EditScalar
from convert.adapters.freecad.Native import NativeObject
from interchange.geometry.models.GeometryCurves import CircleGeometry, PointGeometry
from interchange.geometry.models.Sketch import Sketch
from interchange.serialization.EncodeData import ToData


# the exact embedded profile identities must still match the original writer scaffold
def CheckProfileIds(
    Native: NativeObject, Original: Sketch, SketchData: Mapping[str, object]
) -> None:
    if EditScalar(Native, "KitId", "App::PropertyString", "String") != Original.id:
        raise ValueError("FreeCAD editable profile sketch identity changed")
    for NameValue, DataValue in (
        ("ClosedProfilesJSON", ToData(Original.closed_profile_entity_ids)),
        ("SourceSketchJSON", SketchData),
    ):
        if EditScalar(Native, NameValue, "App::PropertyString", "String") != JsonProp(
            NameValue, DataValue
        )[0].get("value"):
            raise ValueError(
                "FreeCAD editable profile selection or source sketch changed"
            )


# solver decimal roundoff cannot leave a distinct helper point in the neutral profile
def SyncProfile(
    Original: Sketch, Edited: Sketch, CircleIndex: int, CenterIndex: int
) -> Sketch:
    Circle = Edited.entities[CircleIndex].geometry
    Center = Edited.entities[CenterIndex]
    if (
        not isinstance(Circle, CircleGeometry)
        or not isinstance(Center.geometry, PointGeometry)
        or not IsSameCoord(Center.geometry.point, Circle.center)
    ):
        raise ValueError("FreeCAD editable profile center incidence disagrees")
    if Edited is Original or Center.geometry.point == Circle.center:
        return Edited
    Entities = list(Edited.entities)
    Entities[CenterIndex] = Replace(Center, geometry=PointGeometry(Circle.center))
    return Replace(Edited, entities=tuple(Entities))


# only the exact selected profile and its source center may change within the fixed sketch graph
def ReadEditProfile(Native: NativeObject, Original: Sketch) -> Sketch:
    Center = GetCenterPoint(Original)
    SketchData = ToData(Original)
    if (
        Center is None
        or not isinstance(SketchData, dict)
        or Original.constraints
        or Original.parameter_ids
        or Original.suppressed
    ):
        raise ValueError("FreeCAD editable profile has an invalid source sketch scope")
    CircleId = Original.closed_profile_entity_ids[0][0]
    Indices = {Value.id: Index for Index, Value in enumerate(Original.entities)}
    if len(Indices) != len(Original.entities):
        raise ValueError("FreeCAD editable profile geometry identities are ambiguous")
    CheckProfileIds(Native, Original, SketchData)
    CheckExtensions(Native)
    CheckSketchOpts(Native)
    CheckProfileRow(Native, SketchData, Indices, CircleId, Center.id)
    Edited = ReadSketchGeom(Native, Original)
    Movable = {CircleId, Center.id}
    if any(
        Before.id not in Movable and Before is not After
        for Before, After in zip(Original.entities, Edited.entities, strict=True)
    ):
        raise ValueError("FreeCAD editable profile unrelated helper point changed")
    return SyncProfile(Original, Edited, Indices[CircleId], Indices[Center.id])
