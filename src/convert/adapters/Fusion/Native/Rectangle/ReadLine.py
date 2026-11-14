from math import dist as Distance

from convert.adapters.Fusion.Native.Graph.GraphChecks import (
    RequireFields,
    ResolveField,
    SameNumbers,
)
from convert.adapters.Fusion.Native.Graph.GraphValues import ObjectFields, PointCoords
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Graph.NativeNode import NativeNode
from interchange.geometry.models.GeometryCurves import LineGeometry
from interchange.geometry.models.VectorPlane import PlaneVector


def ReadLine(Graph: NativeGraph, NodeValue: NativeNode) -> LineGeometry:
    Start = ResolveField(Graph, NodeValue, "rStartPoint", "Point3D")
    Finish = ResolveField(Graph, NodeValue, "rEndPoint", "Point3D")
    First = PointCoords(Start.Fields["point"])
    Second = PointCoords(Finish.Fields["point"])
    Delta = tuple(Second[Index] - First[Index] for Index in range(3))
    Length = Distance(First, Second)
    if Length <= 0 or First[2] != 0 or Second[2] != 0:
        raise ValueError("Native rectangle requires positive XY line segments")
    Carrier = ObjectFields(NodeValue.Fields["lineCurve"])
    SameNumbers(PointCoords(Carrier["startPoint"]), First)
    SameNumbers(PointCoords(Carrier["displacement"]), Delta)
    SameNumbers(
        PointCoords(NodeValue.Fields["lineDirection"]),
        tuple(Value / Length for Value in Delta),
    )
    SameNumbers(PointCoords(NodeValue.Fields["planeNormal"]), (0.0, 0.0, -1.0))
    RequireFields(
        NodeValue,
        {
            "isFixed": False,
            "isProjected": False,
            "isReference": False,
            "isoCurve": False,
            "isCachedProjected": False,
            "isConstraintOnPlane": False,
        },
    )
    return LineGeometry(
        PlaneVector(First[0] * 10, First[1] * 10),
        PlaneVector(Second[0] * 10, Second[1] * 10),
    )
