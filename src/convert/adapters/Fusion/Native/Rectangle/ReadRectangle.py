from convert.adapters.Fusion.Native.Graph.GraphChecks import (
    LinkedNodes,
    RequireFields,
    SameNodes,
)
from convert.adapters.Fusion.Native.Graph.GraphValues import PointCoords
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Rectangle.OrderLines import OrderLines
from convert.adapters.Fusion.Native.Rectangle.ReadLine import ReadLine
from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext
from convert.adapters.Fusion.Native.Rectangle.RectGeometry import RectGeometry
from interchange.enums.EnumGeometry import GeometryKind
from interchange.geometry.models.GeometryCurves import PointGeometry
from interchange.geometry.models.Sketch import SketchEntity
from interchange.geometry.models.VectorPlane import PlaneVector


def ReadRectangle(Graph: NativeGraph, Context: ExtrudeContext) -> RectGeometry:
    if Graph.ByClass("CircArc3D"):
        raise ValueError(
            "Native rectangle profile contains an unaccounted circular curve"
        )
    Children = LinkedNodes(Graph, Context.Sketch, "children")
    if any(
        Graph.Resolve(NodeValue.Fields["rParent"]) != Context.Sketch
        for NodeValue in Children
    ):
        raise ValueError("Native sketch child belongs to another parent")
    Points = tuple(
        NodeValue for NodeValue in Children if NodeValue.ClassName == "Point3D"
    )
    Lines = tuple(
        NodeValue for NodeValue in Children if NodeValue.ClassName == "Line3D"
    )
    if len(Points) != 5 or len(Lines) != 4 or len(Children) != 9:
        raise ValueError("Native rectangle requires five points and four lines")
    SameNodes(Points, Graph.ByClass("Point3D"))
    SameNodes(Lines, Graph.ByClass("Line3D"))
    LineNodes = OrderLines(Graph, Lines)
    Geometry = tuple(ReadLine(Graph, NodeValue) for NodeValue in LineNodes)
    if (
        sum(
            LineValue.start.x * LineValue.end.y - LineValue.end.x * LineValue.start.y
            for LineValue in Geometry
        )
        <= 0
    ):
        raise ValueError("Native rectangle requires counterclockwise profile winding")
    Corners = {(LineValue.start.x, LineValue.start.y) for LineValue in Geometry}
    XValues, YValues = {Point[0] for Point in Corners}, {Point[1] for Point in Corners}
    if (
        len(XValues) != 2
        or len(YValues) != 2
        or len(Corners) != 4
        or any(
            LineValue.start.x != LineValue.end.x
            and LineValue.start.y != LineValue.end.y
            for LineValue in Geometry
        )
    ):
        raise ValueError("Native rectangle requires axis-aligned rectangular geometry")
    Entities: list[SketchEntity] = []
    for Point in Points:
        Coordinates = PointCoords(Point.Fields["point"])
        RequireFields(
            Point,
            {
                "isProjected": False,
                "isCachedProjected": False,
                "isCoincident": False,
                "specialType": 0,
            },
        )
        if Coordinates[2] != 0 or Point.Fields["isFixed"] != Point.Fields["isOrigin"]:
            raise ValueError("Unsupported native rectangle point constraints")
        Entities.append(
            SketchEntity(
                Point.Identity,
                GeometryKind.KPoint,
                PointGeometry(PlaneVector(Coordinates[0] * 10, Coordinates[1] * 10)),
                fixed=Point.Fields["isFixed"] is True,
            )
        )
    Entities.extend(
        SketchEntity(NodeValue.Identity, GeometryKind.KLine, LineValue)
        for NodeValue, LineValue in zip(LineNodes, Geometry, strict=True)
    )
    return RectGeometry(
        tuple(Entities),
        Geometry,
        LineNodes,
        max(XValues) - min(XValues),
        max(YValues) - min(YValues),
        (min(XValues), min(YValues), 0.0),
    )
