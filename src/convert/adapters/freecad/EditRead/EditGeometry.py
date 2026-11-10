# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from math import isclose as IsClose
from xml.etree.ElementTree import Element

from convert.adapters.freecad.EditRead.XmlField import EditAttr, EditFloat
from interchange.geometry.models.GeometryCurves import CircleGeometry, PointGeometry
from interchange.geometry.models.Sketch import SketchEntity

# native decimal formatting can move a restored coordinate by machine precision
KSketchTolerance = 1e-9


# the only live loop remains the selected circle and its construction point coordinates
def CheckEditGeom(NodeValue: Element, Entity: SketchEntity, Selected: bool) -> None:
    Geometry = Entity.geometry
    Coordinates: tuple[tuple[str, float], ...]
    if Selected and isinstance(Geometry, CircleGeometry):
        TypeName, ChildName = "Part::GeomCircle", "Circle"
        Coordinates = (
            ("CenterX", Geometry.center.x),
            ("CenterY", Geometry.center.y),
            ("CenterZ", 0.0),
            ("NormalX", 0.0),
            ("NormalY", 0.0),
            ("NormalZ", 1.0),
            ("AngleXU", 0.0),
            ("Radius", Geometry.radius),
        )
    elif not Selected and isinstance(Geometry, PointGeometry):
        TypeName, ChildName = "Part::GeomPoint", "GeomPoint"
        Coordinates = (("X", Geometry.point.x), ("Y", Geometry.point.y), ("Z", 0.0))
    else:
        raise ValueError("FreeCAD editable sketch has an unsupported original geometry")
    Nodes = NodeValue.findall(f"./{ChildName}")
    if NodeValue.get("type") != TypeName or len(Nodes) != 1:
        raise ValueError("FreeCAD editable sketch geometry type changed")
    if any(
        not IsClose(
            EditFloat(Nodes[0], Field), Expected, rel_tol=0.0, abs_tol=KSketchTolerance
        )
        for Field, Expected in Coordinates
    ):
        raise ValueError("FreeCAD editable sketch geometry coordinates changed")
    Flags = NodeValue.findall(
        "./GeoExtensions/GeoExtension[@type='Sketcher::SketchGeometryExtension']"
    )
    Construction = NodeValue.findall("./Construction")
    ExpectedFlag = "0" if Selected else "1"
    if (
        len(Flags) != 1
        or EditAttr(Flags[0], "geometryModeFlags")
        != "0" * 30 + ("00" if Selected else "10")
        or len(Construction) != 1
        or Construction[0].get("value") != ExpectedFlag
    ):
        raise ValueError("FreeCAD editable sketch construction flags changed")
