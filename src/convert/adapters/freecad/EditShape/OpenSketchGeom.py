from math import hypot as Hypot

from interchange.brep.Topology.BrepMath import IsFinitePlane
from interchange.Enums.EnumGeometry import GeometryKind
from interchange.geometry.Models.GeometryCurves import LineGeometry, PointGeometry
from interchange.geometry.Models.Sketch import Sketch
from interchange.geometry.Models.VectorPlane import PlaneVector


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
