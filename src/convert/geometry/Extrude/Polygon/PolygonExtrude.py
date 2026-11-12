from math import isfinite as IsFinite

from convert.geometry.Extrude.Polygon.PrismEdges import BuildPrismEdges
from convert.geometry.Extrude.Polygon.PrismFaces import BuildPrismFaces
from convert.geometry.Extrude.Polygon.PrismFrame import CheckPrismFrame
from convert.geometry.Extrude.Polygon.PrismRing import MeasureRing, ReadPrismRing
from convert.geometry.Revolve.SweepModel import BuildSweepModel
from interchange.brep.topology.BrepModel import BrepModel
from interchange.geometry.models.BoundingBox import BoundingBox
from interchange.geometry.models.GeometryCurves import LineGeometry
from interchange.geometry.models.Transform import Transform
from interchange.geometry.models.VectorSpace import SpaceVector


# simple straight profile loops supply analytic planar solids with exact topology and measures
def BuildPrism(
    BodyId: str,
    FrameValue: Transform,
    Profile: tuple[LineGeometry, ...],
    LowerMm: float,
    UpperMm: float,
) -> tuple[BrepModel, float, float, BoundingBox]:
    Height = UpperMm - LowerMm
    if not BodyId or not IsFinite(Height) or Height <= 0:
        raise ValueError(
            "Extrude prism requires a body identity and finite positive depth"
        )
    CheckPrismFrame(FrameValue)
    Points, PlanarArea, Perimeter = MeasureRing(ReadPrismRing(Profile))
    Volume = PlanarArea * Height
    SurfaceArea = 2 * PlanarArea + Perimeter * Height
    if not (IsFinite(Volume) and Volume > 0 and IsFinite(SurfaceArea)):
        raise ValueError("Extrude prism measures exceed floating range")
    Prefix = f"{BodyId}-prism"
    Vertices, Curves, Edges = BuildPrismEdges(
        Prefix, FrameValue, Points, LowerMm, UpperMm
    )
    Surfaces, Faces, Loops, Coedges = BuildPrismFaces(Prefix, FrameValue, Curves, Edges)
    Model = BuildSweepModel(
        BodyId, Prefix, Curves, Surfaces, Vertices, Edges, Faces, Loops, Coedges
    )
    AxisValues = tuple(
        zip(*((Vertex.point.x, Vertex.point.y, Vertex.point.z) for Vertex in Vertices))
    )
    Bounds = BoundingBox(
        SpaceVector(*(min(Coordinates) for Coordinates in AxisValues)),
        SpaceVector(*(max(Coordinates) for Coordinates in AxisValues)),
    )
    return Model, Volume, SurfaceArea, Bounds
