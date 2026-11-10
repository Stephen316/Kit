# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from math import isclose as IsClose
from xml.etree.ElementTree import Element

from convert.adapters.freecad.EditRead.EditGeometry import KSketchTolerance
from convert.adapters.freecad.EditRead.XmlField import EditAttr, EditChild, EditFloat
from convert.adapters.freecad.Native import NativeObject
from interchange.geometry.models.GeometryCurves import LineGeometry, PointGeometry
from interchange.geometry.models.Sketch import Sketch, SketchEntity


# independent sketch points and line endpoints must retain their exact local coordinates
def CheckOpenEntity(NodeValue: Element, Entity: SketchEntity) -> None:
    Geometry = Entity.geometry
    Coordinates: tuple[tuple[str, float], ...]
    if isinstance(Geometry, PointGeometry):
        TypeName, ChildName = "Part::GeomPoint", "GeomPoint"
        Coordinates = (("X", Geometry.point.x), ("Y", Geometry.point.y), ("Z", 0.0))
    elif isinstance(Geometry, LineGeometry):
        TypeName, ChildName = "Part::GeomLineSegment", "LineSegment"
        Coordinates = (
            ("StartX", Geometry.start.x),
            ("StartY", Geometry.start.y),
            ("StartZ", 0.0),
            ("EndX", Geometry.end.x),
            ("EndY", Geometry.end.y),
            ("EndZ", 0.0),
        )
    else:
        raise ValueError("FreeCAD independent sketch geometry is unsupported")
    Nodes = NodeValue.findall(f"./{ChildName}")
    if NodeValue.get("type") != TypeName or tuple(Value.tag for Value in NodeValue) != (
        "GeoExtensions",
        ChildName,
        "Construction",
    ):
        raise ValueError("FreeCAD independent sketch geometry type changed")
    if any(
        not IsClose(
            EditFloat(Nodes[0], Field), Expected, rel_tol=0.0, abs_tol=KSketchTolerance
        )
        for Field, Expected in Coordinates
    ):
        raise ValueError("FreeCAD independent sketch geometry coordinates changed")
    Extensions = NodeValue.findall("./GeoExtensions")
    if (
        len(Extensions) != 1
        or Extensions[0].get("count") != "1"
        or len(Extensions[0]) != 1
    ):
        raise ValueError("FreeCAD independent sketch geometry extension changed")
    Flags = Extensions[0][0]
    Construction = NodeValue.findall("./Construction")
    if (
        Flags.tag != "GeoExtension"
        or Flags.get("type") != "Sketcher::SketchGeometryExtension"
        or Flags.get("id") != NodeValue.get("id")
        or Flags.get("internalGeometryType") != "0"
        or Flags.get("geometryLayer") != "0"
        or EditAttr(Flags, "geometryModeFlags") != "0" * 32
        or len(Construction) != 1
        or Construction[0].get("value") != "0"
    ):
        raise ValueError("FreeCAD independent sketch construction flags changed")


# solver and external bindings can otherwise silently alter a preserved open sketch
def CheckOpenXml(Native: NativeObject, Original: Sketch) -> None:
    Geometries = EditChild(
        Native, "Geometry", "Part::PropertyGeometryList", "GeometryList"
    )
    if Geometries.get("count") != str(len(Original.entities)) or len(Geometries) != len(
        Original.entities
    ):
        raise ValueError("FreeCAD independent sketch geometry count changed")
    for Index, (NodeValue, Entity) in enumerate(
        zip(Geometries, Original.entities, strict=True), 1
    ):
        if NodeValue.tag != "Geometry" or NodeValue.get("id") != str(Index):
            raise ValueError("FreeCAD independent sketch geometry order changed")
        CheckOpenEntity(NodeValue, Entity)
    Rules = EditChild(
        Native, "Constraints", "Sketcher::PropertyConstraintList", "ConstraintList"
    )
    if len(Rules) or Rules.get("count") != "0":
        raise ValueError("FreeCAD independent sketch constraints changed")
    if "ExternalGeometry" in Native.properties:
        External = EditChild(
            Native, "ExternalGeometry", "App::PropertyLinkSubList", "LinkSubList"
        )
        if len(External) or External.get("count") != "0":
            raise ValueError("FreeCAD independent sketch external references changed")
