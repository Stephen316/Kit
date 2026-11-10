# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from math import hypot as Hypot

from interchange.brep.topology.BrepMath import IsFinitePlane
from interchange.enums.EnumGeometry import GeometryKind
from interchange.geometry.models.GeometryCurves import LineGeometry, PointGeometry
from interchange.geometry.models.Sketch import Sketch
from interchange.geometry.models.VectorPlane import PlaneVector


# only simple independent sketch geometry with a known cache grammar can be preserved
def ReadOpenGeom(
    SketchValue: Sketch,
) -> tuple[LineGeometry, tuple[PlaneVector, ...]] | None:
    if (
        SketchValue.suppressed
        or SketchValue.parameter_ids
        or SketchValue.constraints
        or SketchValue.closed_profile_entity_ids
        or not 2 <= len(SketchValue.entities) <= 17
        or len({Value.id for Value in SketchValue.entities})
        != len(SketchValue.entities)
    ):
        return None
    Points: list[PlaneVector] = []
    Segment: LineGeometry | None = None
    for Entity in SketchValue.entities:
        Geometry = Entity.geometry
        if Entity.fixed or Entity.construction:
            return None
        if Entity.kind == GeometryKind.KPoint and isinstance(Geometry, PointGeometry):
            if not IsFinitePlane(Geometry.point):
                return None
            Points.append(Geometry.point)
        elif Entity.kind == GeometryKind.KLine and isinstance(Geometry, LineGeometry):
            if Segment is not None or not (
                IsFinitePlane(Geometry.start) and IsFinitePlane(Geometry.end)
            ):
                return None
            if (
                Hypot(
                    Geometry.start.x - Geometry.end.x, Geometry.start.y - Geometry.end.y
                )
                <= 1e-6
            ):
                return None
            Segment = Geometry
        else:
            return None
    return (Segment, tuple(Points)) if Segment is not None and Points else None
