from math import dist as Distance, isfinite as IsFinite

from convert.formats.Fusion.BrepCodec.Journal.Geometry.EdgeNode import EdgeNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.StraightNode import StraightNode
from convert.formats.Fusion.BrepCodec.Journal.Planar.LiveTable import LiveTable
from convert.formats.Fusion.BrepCodec.Journal.Planar.ReadVertexPoint import (
    ReadVertexPoint,
)
from convert.formats.Fusion.BrepCodec.Journal.Planar.RequireLive import RequireLive
from convert.formats.Fusion.BrepCodec.Journal.Planar.StableRef import StableRef


def CheckLineEdge(Table: LiveTable, EdgeRef: int) -> None:
    EdgeValue = RequireLive(Table, EdgeRef, EdgeNode)
    Curve = RequireLive(Table, EdgeValue.CurveRef, StraightNode)
    for VertexRef, Parameter in (
        (EdgeValue.StartVertex, EdgeValue.StartParam),
        (EdgeValue.EndVertex, EdgeValue.EndParam),
    ):
        Position = ReadVertexPoint(Table, StableRef(Table, VertexRef))
        Parameter = -Parameter if EdgeValue.Reversed else Parameter
        Evaluated = tuple(
            Origin + Parameter * Direction
            for Origin, Direction in zip(
                Curve.OriginCm, Curve.DirectionVector, strict=True
            )
        )
        if (
            any(not IsFinite(Value) for Value in Evaluated)
            or Distance(Evaluated, Position) > 1e-7
        ):
            raise ValueError("Fusion straight carrier does not reach its vertex")
        if (Curve.LowerBound is not None and Parameter < Curve.LowerBound - 1e-7) or (
            Curve.UpperBound is not None and Parameter > Curve.UpperBound + 1e-7
        ):
            raise ValueError("Fusion edge lies outside its straight carrier bounds")
