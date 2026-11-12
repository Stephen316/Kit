from math import hypot as Hypot, tau as FullTurn
from xml.etree.ElementTree import Element

from convert.adapters.freecad.EditRead.EditGeometry import KSketchTolerance
from convert.adapters.freecad.EditRead.XmlField import EditFloat
from interchange.geometry.models.GeometryCurves import (
    ArcGeometry,
    CircleGeometry,
    LineGeometry,
    PointGeometry,
)
from interchange.geometry.models.VectorPlane import PlaneVector

# bounded editable shapes share one explicit planar geometry vocabulary
KSketchPrimitive = PointGeometry | LineGeometry | CircleGeometry | ArcGeometry


# explicit field schemas prevent unknown geometry state from entering the editable scope
KCircularFields = frozenset(
    {
        "CenterX",
        "CenterY",
        "CenterZ",
        "NormalX",
        "NormalY",
        "NormalZ",
        "AngleXU",
        "Radius",
    }
)

# primitive layouts isolate geometry coordinates from unsupported native attributes
KPrimitiveFields = {
    "GeomPoint": frozenset({"X", "Y", "Z"}),
    "LineSegment": frozenset({"StartX", "StartY", "StartZ", "EndX", "EndY", "EndZ"}),
    "Circle": KCircularFields,
    "ArcOfCircle": KCircularFields | {"StartAngle", "EndAngle"},
}


# exact axis layout and finite values keep saved geometry in the original sketch plane
def ReadPlanar(NodeValue: Element, Prefix: str) -> PlaneVector:
    if abs(EditFloat(NodeValue, Prefix + "Z")) > KSketchTolerance:
        raise ValueError("FreeCAD saved sketch geometry is nonplanar")
    return PlaneVector(
        EditFloat(NodeValue, Prefix + "X"), EditFloat(NodeValue, Prefix + "Y")
    )


# strict native coordinates recover only the same bounded planar primitive family
def ReadPrimitive(NodeValue: Element, ChildName: str) -> KSketchPrimitive:
    if NodeValue.attrib.keys() != KPrimitiveFields[ChildName]:
        raise ValueError("FreeCAD saved sketch primitive fields changed")
    if ChildName == "GeomPoint":
        return PointGeometry(ReadPlanar(NodeValue, ""))
    if ChildName == "LineSegment":
        Start, EndPoint = ReadPlanar(NodeValue, "Start"), ReadPlanar(NodeValue, "End")
        Length = Hypot(Start.x - EndPoint.x, Start.y - EndPoint.y)
        if not KSketchTolerance < Length < float("inf"):
            raise ValueError("FreeCAD saved sketch segment is degenerate")
        return LineGeometry(Start, EndPoint)
    Center = ReadPlanar(NodeValue, "Center")
    for AttrName, Expected in (
        ("NormalX", 0),
        ("NormalY", 0),
        ("NormalZ", 1),
        ("AngleXU", 0),
    ):
        if abs(EditFloat(NodeValue, AttrName) - Expected) > KSketchTolerance:
            raise ValueError("FreeCAD saved sketch circular reference frame changed")
    Radius = EditFloat(NodeValue, "Radius")
    if Radius <= KSketchTolerance:
        raise ValueError("FreeCAD saved sketch circular radius is degenerate")
    if ChildName == "Circle":
        return CircleGeometry(Center, Radius)
    StartAngle, EndAngle = EditFloat(NodeValue, "StartAngle"), EditFloat(
        NodeValue, "EndAngle"
    )
    SpanValue = EndAngle - StartAngle
    if (
        max(abs(StartAngle), abs(EndAngle)) > 2 * FullTurn
        or not KSketchTolerance < SpanValue < FullTurn - KSketchTolerance
    ):
        raise ValueError("FreeCAD saved sketch arc trim is degenerate")
    StartAngle %= FullTurn
    return ArcGeometry(Center, Radius, StartAngle, StartAngle + SpanValue)
