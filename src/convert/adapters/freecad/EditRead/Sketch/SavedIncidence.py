# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt


from math import cos as Cosine, sin as SinValue

from convert.adapters.freecad.EditRead.Sketch.SavedEntity import IsSameCoord
from convert.adapters.freecad.SketchIncidence import GetIncidence
from interchange.geometry.models.GeometryCurves import (
    ArcGeometry,
    CircleGeometry,
    LineGeometry,
    PointGeometry,
)
from interchange.geometry.models.Sketch import SketchEntity
from interchange.geometry.models.VectorPlane import PlaneVector
from interchange.serialization.EncodeData import ToData


# sketcher slots identify exact curve endpoints and centers independently of coordinate matches
def GetSlotPoint(Entity: SketchEntity, PointSlot: int) -> PlaneVector:
    Geometry = Entity.geometry
    if isinstance(Geometry, LineGeometry):
        return Geometry.start if PointSlot == 1 else Geometry.end
    if isinstance(Geometry, (CircleGeometry, ArcGeometry)):
        if PointSlot == 3:
            return Geometry.center
        if isinstance(Geometry, ArcGeometry):
            Angle = Geometry.start_angle if PointSlot == 1 else Geometry.end_angle
            return PlaneVector(
                Geometry.center.x + Geometry.radius * Cosine(Angle),
                Geometry.center.y + Geometry.radius * SinValue(Angle),
            )
    raise ValueError("FreeCAD saved sketch has an unsupported incidence slot")


# duplicated point records must still agree with the exact source curve endpoint or center
def CheckIncidence(Entities: tuple[SketchEntity, ...]) -> None:
    Points = {
        Entity.id: Entity.geometry.point
        for Entity in Entities
        if isinstance(Entity.geometry, PointGeometry)
    }
    for Entity in Entities:
        if isinstance(Entity.geometry, PointGeometry):
            continue
        Attributes = ToData(Entity.attributes)
        if not isinstance(Attributes, dict):
            raise ValueError("FreeCAD saved sketch has invalid incidence attributes")
        Links = GetIncidence(type(Entity.geometry).__name__, Attributes)
        if not Links:
            raise ValueError("FreeCAD saved sketch has no native incidence evidence")
        for NativeId, PointSlot in Links:
            PointValue = Points.get(f"fusion-sketch-entity-{NativeId}")
            if (
                type(NativeId) is not int
                or PointValue is None
                or not IsSameCoord(GetSlotPoint(Entity, PointSlot), PointValue)
            ):
                raise ValueError("FreeCAD saved sketch changed native point incidence")
