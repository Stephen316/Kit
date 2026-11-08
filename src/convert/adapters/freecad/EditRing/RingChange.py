# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from dataclasses import replace as Replace

from convert.adapters.freecad.EditExtRing import GetRingPoints
from convert.adapters.freecad.EditRead.Sketch.SavedEntity import IsSameCoord
from convert.adapters.freecad.EditRing.RingEndpoints import ReadRingEnds
from interchange.geometry.models.GeometryCurves import LineGeometry, PointGeometry
from interchange.geometry.models.Sketch import Sketch, SketchEntity
from interchange.geometry.models.VectorPlane import PlaneVector


# unchanged source identity restricts geometry edits to the ring and its exact endpoint points
def CheckRingModel(
    Original: Sketch, Edited: Sketch, ExtraPointId: str = ""
) -> frozenset[str]:
    Points = GetRingPoints(Original)
    if (
        Points is None
        or len(Edited.entities) != len(Original.entities)
        or Replace(Edited, entities=Original.entities) != Original
    ):
        raise ValueError("FreeCAD editable ring sketch identity changed")
    Allowed = Points | set(Original.closed_profile_entity_ids[0]) | {ExtraPointId}
    for Before, After in zip(Original.entities, Edited.entities, strict=True):
        if Replace(After, geometry=Before.geometry) != Before:
            raise ValueError("FreeCAD editable ring sketch entity identity changed")
        if Before.id not in Allowed and Before.geometry != After.geometry:
            raise ValueError(
                "FreeCAD editable ring has an unrelated sketch geometry edit"
            )
    return Points


# neutral rebuilding requires the same complete and exact simple ring incidence
def CheckRingEdit(Original: Sketch, Edited: Sketch) -> None:
    PointIds = CheckRingModel(Original, Edited)
    if GetRingPoints(Edited) != PointIds:
        raise ValueError(
            "FreeCAD editable ring profile no longer has the same incidence"
        )


# matching helper points remove only native serialization noise from shared vertices
def SyncRingLine(Entity: SketchEntity, Points: dict[str, PlaneVector]) -> SketchEntity:
    StartId, EndId = ReadRingEnds(Entity)
    Geometry = Entity.geometry
    Start, EndPoint = Points.get(StartId), Points.get(EndId)
    if (
        not isinstance(Geometry, LineGeometry)
        or Start is None
        or EndPoint is None
        or not IsSameCoord(Geometry.start, Start)
        or not IsSameCoord(Geometry.end, EndPoint)
    ):
        raise ValueError(
            "FreeCAD editable ring endpoint disagrees with its native point"
        )
    if Geometry.start == Start and Geometry.end == EndPoint:
        return Entity
    return Replace(Entity, geometry=LineGeometry(Start, EndPoint))


# both occurrences of every saved ring vertex share its proven neutral point value
def SyncRingEdit(Original: Sketch, Edited: Sketch, *, ExtraPointId: str = "") -> Sketch:
    PointIds = CheckRingModel(Original, Edited, ExtraPointId)
    if Edited is Original:
        return Original
    ProfileIds = set(Original.closed_profile_entity_ids[0])
    Points = {
        Entity.id: Entity.geometry.point
        for Entity in Edited.entities
        if Entity.id in PointIds and isinstance(Entity.geometry, PointGeometry)
    }
    Entities = tuple(
        SyncRingLine(Entity, Points) if Entity.id in ProfileIds else Entity
        for Entity in Edited.entities
    )
    Result = Replace(Edited, entities=Entities)
    if GetRingPoints(Result) != PointIds:
        raise ValueError(
            "FreeCAD editable ring profile no longer has the same incidence"
        )
    return Original if Result == Original else Result
