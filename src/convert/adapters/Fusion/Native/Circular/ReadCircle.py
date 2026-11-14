from convert.adapters.Fusion.Native.Circular.CheckCircleUses import CheckCircleUses
from convert.adapters.Fusion.Native.Graph.NativeNode import NativeNode

from math import tau as FullTurn

from convert.adapters.Fusion.Native.Graph.GraphChecks import (
    LinkedNodes,
    RequireFields,
    ResolveField,
    SameNodes,
    SameNumbers,
)
from convert.adapters.Fusion.Native.Graph.GraphValues import (
    ObjectFields,
    NumberValue,
    PointCoords,
)
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Graph.SketchContexts import KSketchContexts
from convert.adapters.Fusion.Native.Circular.CircleShape import CircleShape
from interchange.enums.EnumGeometry import GeometryKind
from interchange.geometry.models.GeometryCurves import CircleGeometry, PointGeometry
from interchange.geometry.models.Sketch import SketchEntity
from interchange.geometry.models.VectorPlane import PlaneVector


def ReadCircle(Graph: NativeGraph, Context: KSketchContexts) -> CircleShape:
    Circle = Graph.OneClass("CircArc3D")
    Center = ResolveField(Graph, Circle, "rCenterPoint", "Point3D")
    Points = Graph.ByClass("Point3D")
    if (
        len(Points) != 2
        or Graph.ByClass("Line3D")
        or sum(Point.Fields["isOrigin"] is True for Point in Points) != 1
    ):
        raise ValueError(
            "Native circular profile requires only an origin, center and full circle"
        )
    SameNodes((*Points, Circle), LinkedNodes(Graph, Context.Sketch, "children"))
    if Graph.Resolve(Circle.Fields["rParent"]) != Context.Sketch:
        raise ValueError("Native circle has inconsistent sketch ownership")
    CheckCircleUses(Graph, Circle, Center, Points)
    Carrier = ObjectFields(Circle.Fields["arcCurve"])
    SameNumbers(PointCoords(Carrier["center"]), PointCoords(Center.Fields["point"]))
    SameNumbers(PointCoords(Carrier["normal"]), (0.0, 0.0, 1.0))
    SameNumbers(PointCoords(Carrier["refVec"]), (1.0, 0.0, 0.0))
    SameNumbers(
        (NumberValue(Carrier["startAngle"]), NumberValue(Carrier["endAngle"])),
        (0.0, FullTurn),
    )
    RequireFields(
        Circle,
        {
            "rStartPoint": None,
            "rEndPoint": None,
            "isFixed": False,
            "isFullyConstrained": False,
            "isProjected": False,
            "isReference": False,
            "isoCurve": False,
            "isCachedProjected": False,
            "isConstraintOnPlane": False,
        },
    )
    Radius = NumberValue(Carrier["radius"]) * 10
    Coordinates = PointCoords(Carrier["center"])
    if Radius <= 0 or Coordinates[2] != 0 or Center.Fields["isOrigin"] is not False:
        raise ValueError(
            "Native circular profile requires a positive XY radius and distinct center"
        )
    Geometry = CircleGeometry(
        PlaneVector(Coordinates[0] * 10, Coordinates[1] * 10), Radius
    )
    Entities = ReadPoints(Graph, Context, Points)
    Entity = SketchEntity(
        Circle.Identity,
        GeometryKind.KCircle,
        Geometry,
        attributes={"center_point_id": Center.Identity},
    )
    return CircleShape(Circle, Center, (*Entities, Entity), Geometry)


def ReadPoints(
    Graph: NativeGraph, Context: KSketchContexts, Points: tuple[NativeNode, ...]
) -> tuple[SketchEntity, ...]:
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
        if (
            Coordinates[2] != 0
            or Point.Fields["isFixed"] != Point.Fields["isOrigin"]
            or Graph.Resolve(Point.Fields["rParent"]) != Context.Sketch
        ):
            raise ValueError("Unsupported native circle point constraint or ownership")
        if Point.Fields["isOrigin"] is True:
            SameNumbers(Coordinates, (0.0, 0.0, 0.0))
        Entities.append(
            SketchEntity(
                Point.Identity,
                GeometryKind.KPoint,
                PointGeometry(PlaneVector(Coordinates[0] * 10, Coordinates[1] * 10)),
                fixed=Point.Fields["isFixed"] is True,
            )
        )
    return tuple(Entities)
