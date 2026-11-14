from convert.adapters.Fusion.Native.Graph.GraphChecks import (
    EmptyFields,
    LinkedNodes,
    ResolveField,
    SameNodes,
)
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Graph.NativeNode import NativeNode


def CheckCircleUses(
    Graph: NativeGraph,
    Circle: NativeNode,
    Center: NativeNode,
    Points: tuple[NativeNode, ...],
) -> None:
    UsageNodes = tuple(
        ResolveField(Graph, Point, "curveUses", "CurveUses") for Point in Points
    )
    SameNodes(UsageNodes, Graph.ByClass("CurveUses"))
    EmptyFields(Circle, ("children", "DAGNodeParents"))
    for Point, Usage in zip(Points, UsageNodes, strict=True):
        SameNodes(LinkedNodes(Graph, Point, "children"), (Usage,))
        if Graph.Resolve(Usage.Fields["rParent"]) != Point:
            raise ValueError("Native circle point incidence has inconsistent ownership")
        SameNodes(
            LinkedNodes(Graph, Usage, "geometries"),
            (Circle,) if Point == Center else (),
        )
        EmptyFields(Point, ("DAGNodeParents",))
        if (
            Point.Fields["isConstraintOnPlane"] is not False
            or Point.Fields["isFullyConstrained"] != Point.Fields["isOrigin"]
        ):
            raise ValueError("Native circle point has unsupported constraint state")
