from math import isfinite as IsFinite

from convert.formats.Fusion.Profiles.Trimmed.TrimSources import (
    GetLinePoints,
    KTrimDistance,
)
from interchange.geometry.models.GeometryCurves import LineGeometry
from interchange.geometry.models.Sketch import SketchEntity
from interchange.geometry.models.VectorPlane import PlaneVector

# line partitioning preserves both affine geometry and native endpoint topology
KTrimLine = tuple[LineGeometry, tuple[int, int]]


# explicit endpoint identities must form two disjoint four side cycles
def ReadLineGraph(Lines: tuple[SketchEntity, ...]) -> dict[str, KTrimLine]:
    Sources: dict[str, KTrimLine] = {}
    Adjacent: dict[int, set[int]] = {}
    Positions: dict[int, PlaneVector] = {}
    for Entity in Lines:
        Geometry = Entity.geometry
        if not isinstance(Geometry, LineGeometry):
            raise ValueError("Missing Fusion trimmed profile source line")
        DeltaX = Geometry.end.x - Geometry.start.x
        DeltaY = Geometry.end.y - Geometry.start.y
        if (
            not IsFinite(DeltaX)
            or not IsFinite(DeltaY)
            or (abs(DeltaX) > KTrimDistance) == (abs(DeltaY) > KTrimDistance)
        ):
            raise ValueError("Unsupported Fusion trimmed line alignment")
        StartId, EndId = GetLinePoints(Entity)
        if (
            Positions.setdefault(StartId, Geometry.start) != Geometry.start
            or Positions.setdefault(EndId, Geometry.end) != Geometry.end
        ):
            raise ValueError("Fusion trimmed line shared endpoint coordinates disagree")
        Adjacent.setdefault(StartId, set()).add(EndId)
        Adjacent.setdefault(EndId, set()).add(StartId)
        Sources[Entity.id] = (Geometry, (StartId, EndId))
    CheckLineCycles(Adjacent)
    return Sources


# native shared endpoints must form exactly two four sided cycles
def CheckLineCycles(Adjacent: dict[int, set[int]]) -> None:
    if len(Adjacent) != 8 or any(
        len(Neighbors) != 2 for Neighbors in Adjacent.values()
    ):
        raise ValueError("Unsupported Fusion trimmed line endpoint graph")
    Remaining = set(Adjacent)
    while Remaining:
        Pending = [next(iter(Remaining))]
        Cycle: set[int] = set()
        while Pending:
            PointId = Pending.pop()
            if PointId not in Cycle:
                Cycle.add(PointId)
                Pending.extend(Adjacent[PointId] - Cycle)
        if len(Cycle) != 4:
            raise ValueError("Fusion trimmed lines require two four side cycles")
        Remaining.difference_update(Cycle)
