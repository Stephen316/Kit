from dataclasses import replace as Replace
from math import fmod as TurnResidue, tau as FullTurn
from xml.etree.ElementTree import Element

from convert.adapters.freecad.EditRead.EditGeometry import KSketchTolerance
from convert.adapters.freecad.EditRead.Sketch.SavedPrimitive import (
    KSketchPrimitive,
    ReadPrimitive,
)
from convert.adapters.freecad.EditRead.XmlField import OnlyEditChild
from interchange.enums.EnumGeometry import GeometryKind
from interchange.geometry.models.GeometryCurves import (
    ArcGeometry,
    CircleGeometry,
    LineGeometry,
    PointGeometry,
)
from interchange.geometry.models.Sketch import SketchEntity
from interchange.geometry.models.VectorPlane import PlaneVector

# only writer emitted planar entity layouts have stable editable index semantics
KEntityLayouts: dict[str, tuple[str, str, type[KSketchPrimitive]]] = {
    GeometryKind.KPoint: ("Part::GeomPoint", "GeomPoint", PointGeometry),
    GeometryKind.KLine: ("Part::GeomLineSegment", "LineSegment", LineGeometry),
    GeometryKind.KCircle: ("Part::GeomCircle", "Circle", CircleGeometry),
    GeometryKind.KArcGeometry: ("Part::GeomArcOfCircle", "ArcOfCircle", ArcGeometry),
}


# native serialization noise must not replace otherwise unchanged source points
def IsSameCoord(First: PlaneVector, Second: PlaneVector) -> bool:
    return (
        abs(First.x - Second.x) <= KSketchTolerance
        and abs(First.y - Second.y) <= KSketchTolerance
    )


# the neutral value comparison preserves stable arc starts across whole turns
def IsSameGeom(First: KSketchPrimitive, Second: KSketchPrimitive) -> bool:
    if isinstance(First, PointGeometry) and isinstance(Second, PointGeometry):
        return IsSameCoord(First.point, Second.point)
    if isinstance(First, LineGeometry) and isinstance(Second, LineGeometry):
        return IsSameCoord(First.start, Second.start) and IsSameCoord(
            First.end, Second.end
        )
    if isinstance(First, (CircleGeometry, ArcGeometry)) and isinstance(
        Second, (CircleGeometry, ArcGeometry)
    ):
        if (
            not IsSameCoord(First.center, Second.center)
            or abs(First.radius - Second.radius) > KSketchTolerance
        ):
            return False
        if isinstance(First, ArcGeometry) and isinstance(Second, ArcGeometry):
            Difference = abs(
                TurnResidue(First.start_angle - Second.start_angle, FullTurn)
            )
            return (
                min(Difference, FullTurn - Difference) <= KSketchTolerance
                and abs(
                    (First.end_angle - First.start_angle)
                    - (Second.end_angle - Second.start_angle)
                )
                <= KSketchTolerance
            )
        return type(First) is type(Second)
    return False


# native construction and index flags must still identify the original entity slot
def CheckGeomFlags(
    NodeValue: Element, Identity: str, IsConstruction: bool, IsFixed: bool
) -> None:
    Extensions, _, Construction = NodeValue
    Extension = OnlyEditChild(Extensions, "GeoExtension")
    FlagValue = "1" if IsConstruction else "0"
    Flags = "0" * 30 + FlagValue
    AllowedModes = {Flags + "0", Flags + ("1" if IsFixed else "0")}
    Expected = {
        "type": "Sketcher::SketchGeometryExtension",
        "id": Identity,
        "internalGeometryType": "0",
        "geometryModeFlags": Extension.get("geometryModeFlags", ""),
        "geometryLayer": "0",
    }
    if (
        Extensions.attrib != {"count": "1"}
        or Extension.attrib != Expected
        or Expected["geometryModeFlags"] not in AllowedModes
        or len(Extension)
        or Construction.attrib != {"value": FlagValue}
        or len(Construction)
    ):
        raise ValueError("FreeCAD saved sketch geometry flags changed")


# a native edit can move values without changing type order construction or fixed intent
def ReadSavedEntity(
    NodeValue: Element, Original: SketchEntity, Identity: str, IsConstruction: bool
) -> SketchEntity:
    Layout = KEntityLayouts.get(Original.kind)
    if Layout is None:
        raise ValueError("FreeCAD saved sketch has an unsupported original geometry")
    TypeName, ChildName, ModelType = Layout
    if (
        not isinstance(Original.geometry, ModelType)
        or NodeValue.tag != "Geometry"
        or NodeValue.attrib != {"type": TypeName, "id": Identity, "migrated": "1"}
        or tuple(Value.tag for Value in NodeValue)
        != ("GeoExtensions", ChildName, "Construction")
        or len(NodeValue[1])
    ):
        raise ValueError("FreeCAD saved sketch geometry identity or type changed")
    CheckGeomFlags(NodeValue, Identity, IsConstruction, Original.fixed)
    Geometry = ReadPrimitive(NodeValue[1], ChildName)
    if IsSameGeom(Original.geometry, Geometry):
        return Original
    if Original.fixed:
        raise ValueError("FreeCAD saved sketch fixed geometry changed")
    return Replace(Original, geometry=Geometry)
