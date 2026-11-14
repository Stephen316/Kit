from math import cos as Cosine, sin as SineValue, tau as FullTurn

from convert.adapters.Fusion.Native.Circular.Snapshots.SnapAccess import SnapEntity
from convert.adapters.Fusion.Native.Graph.GraphChecks import SameNumbers
from convert.formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)
from convert.formats.Fusion.BrepCodec.Journal.Geometry.EdgeNode import EdgeNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.VertexNode import VertexNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.PointNode import PointNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.EllipseNode import EllipseNode


def CheckRim(
    State: GeometryState,
    EdgeValue: EdgeNode,
    Center: tuple[float, float, float],
    Radius: float,
    IsTop: bool,
) -> None:
    Curve = SnapEntity(State, EdgeValue.CurveRef, EllipseNode)
    SameNumbers(Curve.OriginCm, Center)
    SameNumbers(Curve.MajorAxisCm, (Radius, 0.0, 0.0))
    SameNumbers(Curve.Normal, (0.0, 0.0, -1.0 if IsTop else 1.0))
    if (
        Curve.EllipseRatio != 1
        or Curve.LowerBound is not None
        or Curve.UpperBound is not None
    ):
        raise ValueError(
            "Native circular snapshot requires an unbounded circular carrier"
        )
    if (
        EdgeValue.StartVertex != EdgeValue.EndVertex
        or EdgeValue.Reversed
        or EdgeValue.Convexity != "unknown"
    ):
        raise ValueError(
            "Native circular snapshot edge has unsupported closure or orientation"
        )
    SameNumbers((EdgeValue.EndParam - EdgeValue.StartParam,), (FullTurn,))
    Vertex = SnapEntity(State, EdgeValue.StartVertex, VertexNode)
    Point = SnapEntity(State, Vertex.PointRef, PointNode)
    Expected = (
        Center[0] + Radius * Cosine(EdgeValue.StartParam),
        Center[1] + Radius * SineValue(EdgeValue.StartParam) * Curve.Normal[2],
        Center[2],
    )
    SameNumbers(Point.PositionCm, Expected)
