from convert.formats.Fusion.Sketches.LinePointIds import ReadLineEnds
from convert.formats.Fusion.Topology.AsmEdge.AsmPoints import IsAsmNear
from convert.geometry.Revolve.SweepVector import OffsetVector
from interchange.geometry.models.GeometryCurves import LineGeometry
from interchange.geometry.models.Sketch import SketchEntity
from interchange.geometry.models.Transform import Transform
from interchange.geometry.models.VectorSpace import SpaceVector


# endpoint geometry corroborates the directed recipe mapping after source identity is fixed
def CheckCapLine(
    Entity: SketchEntity, Frame: Transform, Expected: tuple[SpaceVector, SpaceVector]
) -> tuple[int, int]:
    Geometry = Entity.geometry
    if (
        not isinstance(Geometry, LineGeometry)
        or Entity.construction
        or Entity.attributes.get("fusion.entity_genesis") != 0
    ):
        raise ValueError("Fusion cap projection lacks a native line cache")
    Start, Finish = ReadLineEnds(Entity)
    for Point, Native in zip((Geometry.start, Geometry.end), Expected, strict=True):
        Projected = OffsetVector(
            OffsetVector(Frame.origin, Frame.x_axis, Point.x),
            Frame.y_axis,
            Point.y,
        )
        if not IsAsmNear(Projected, Native):
            raise ValueError(
                "Fusion cap projection endpoints disagree in component millimeters"
            )
    return Start, Finish
