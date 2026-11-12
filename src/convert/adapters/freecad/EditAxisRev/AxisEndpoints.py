from math import hypot as Hypot, isfinite as IsFinite

from convert.adapters.freecad.EditAxisRev.AxisPrimitives import (
    ReadAxisGeom,
    ReadAxisPoint,
)
from convert.adapters.freecad.EditRing.RingEndpoints import ReadRingEnds
from convert.geometry.Extrude.Polygon.PrismFrame import PlacePrismPoint
from convert.geometry.Revolve.SweepVector import OffsetVector
from interchange.brep.topology.BrepMath import IsFiniteSpace
from interchange.geometry.models.GeometryCurves import LineGeometry
from interchange.geometry.models.Sketch import Sketch
from interchange.geometry.models.Transform import KOriginZero, Transform
from interchange.geometry.models.VectorPlane import PlaneVector
from interchange.geometry.models.VectorSpace import SpaceVector


# the independent sketch owns one construction line and its original endpoint records
def ReadAxisLine(
    SketchValue: Sketch, AxisLineId: str
) -> tuple[LineGeometry, tuple[str, str]]:
    Entities = {Value.id: Value for Value in SketchValue.entities}
    if (
        SketchValue.suppressed
        or SketchValue.parameter_ids
        or SketchValue.constraints
        or SketchValue.closed_profile_entity_ids
        or SketchValue.attributes.get("freecad")
        or len(Entities) != len(SketchValue.entities)
        or not 3 <= len(Entities) <= 4
    ):
        raise ValueError("FreeCAD editable axis sketch geometry is unsupported")
    AxisValue = Entities[AxisLineId]
    Geometry = ReadAxisGeom(AxisValue, Construction=True)
    Points = {
        KeyName: ReadAxisPoint(Value)
        for KeyName, Value in Entities.items()
        if KeyName != AxisLineId
    }
    Start, EndId = ReadRingEnds(AxisValue)
    Other = tuple(
        Value for KeyName, Value in Points.items() if KeyName not in (Start, EndId)
    )
    if (
        Points.get(Start) != Geometry.start
        or Points.get(EndId) != Geometry.end
        or (Other and Other != (PlaneVector(0.0, 0.0),))
    ):
        raise ValueError("FreeCAD editable axis line and native helper points disagree")
    return Geometry, (Start, EndId)


# local directed geometry is converted without subtracting rounded world coordinates
def WorldAxisLine(
    Geometry: LineGeometry, FrameValue: Transform
) -> tuple[SpaceVector, SpaceVector, SpaceVector]:
    Start = PlacePrismPoint(FrameValue, Geometry.start, 0.0)
    Finish = PlacePrismPoint(FrameValue, Geometry.end, 0.0)
    Delta = OffsetVector(
        OffsetVector(KOriginZero, FrameValue.x_axis, Geometry.end.x - Geometry.start.x),
        FrameValue.y_axis,
        Geometry.end.y - Geometry.start.y,
    )
    Length = Hypot(Delta.x, Delta.y, Delta.z)
    if (
        not IsFiniteSpace(Start)
        or not IsFiniteSpace(Finish)
        or not IsFinite(Length)
        or Length <= 1e-8
    ):
        raise ValueError("FreeCAD editable sketch axis has degenerate world endpoints")
    return (
        Start,
        Finish,
        SpaceVector(Delta.x / Length, Delta.y / Length, Delta.z / Length),
    )
