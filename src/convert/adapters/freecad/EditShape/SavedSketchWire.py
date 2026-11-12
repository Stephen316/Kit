from convert.adapters.freecad.EditShape.Sketch.MatchWireEdges import IsEdgeMatch
from convert.adapters.freecad.EditShape.Sketch.SavedWireData import ReadSavedWire
from convert.adapters.freecad.EditShape.Sketch.WireMatch import KSketchCurve
from convert.adapters.freecad.EditShape.Sketch.WireProof import ReadRootMut
from convert.geometry.Extrude.Polygon.PrismFrame import PlacePrismPoint
from convert.geometry.Opencascade import DecodeFailure
from interchange.geometry.models.GeometryCurves import (
    ArcGeometry,
    CircleGeometry,
    LineGeometry,
    PointGeometry,
)
from interchange.geometry.models.Sketch import Sketch
from interchange.geometry.models.Transform import Transform
from interchange.geometry.models.VectorSpace import SpaceVector

# analytic sketch archives remain bounded before reading native shape tokens
KMaxSketchBytes = 262_144


# construction geometry is omitted from the same visible wire exported by freecad
def ReadVisible(
    SketchValue: Sketch, FrameValue: Transform
) -> tuple[list[KSketchCurve], list[SpaceVector]]:
    ClosedIds = {
        Identity
        for Profile in SketchValue.closed_profile_entity_ids
        for Identity in Profile
    }
    Curves: list[KSketchCurve] = []
    Points: list[SpaceVector] = []
    for Entity in SketchValue.entities:
        if Entity.construction or (ClosedIds and Entity.id not in ClosedIds):
            continue
        Geometry = Entity.geometry
        if isinstance(Geometry, PointGeometry):
            Points.append(PlacePrismPoint(FrameValue, Geometry.point, 0.0))
        elif isinstance(Geometry, (ArcGeometry, CircleGeometry, LineGeometry)):
            Curves.append(Geometry)
        else:
            raise DecodeFailure("unsupported saved sketch cache geometry")
    return Curves, Points


# independent wire cache geometry must corroborate every visible point and curve
def IsSketchCache(
    ShapeData: bytes,
    SketchValue: Sketch,
    FrameValue: Transform,
    ClosedWire: bool = False,
    *,
    AllowPcurves: bool = False,
    DirectedLines: bool = False,
) -> bool:
    if len(ShapeData) > KMaxSketchBytes:
        return False
    try:
        Curves, Points = ReadVisible(SketchValue, FrameValue)
        if DirectedLines and any(
            not isinstance(Curve, LineGeometry) for Curve in Curves
        ):
            return False
        if AllowPcurves and (
            not ClosedWire
            or Points
            or any(not isinstance(Curve, LineGeometry) for Curve in Curves)
        ):
            return False
        if not ShapeData:
            return not ClosedWire and not Curves and not Points
        DataValue = ReadSavedWire(
            ShapeData, len(Curves), len(Points), AllowPcurves=AllowPcurves
        )
        RootValue = DataValue.Records[DataValue.RootRef.RecordA]
        if ClosedWire and (
            RootValue.KindValue != b"Wi" or RootValue.FlagBits[4] != "1"
        ):
            return False
        Edges = ReadRootMut(DataValue, Points, DirectedLines)
        return not Points and IsEdgeMatch(Edges, Curves, FrameValue, DirectedLines)
    except (
        DecodeFailure,
        IndexError,
        KeyError,
        TypeError,
        ValueError,
        OverflowError,
        RecursionError,
    ):
        return False
