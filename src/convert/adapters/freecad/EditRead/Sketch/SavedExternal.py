# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt


from xml.etree.ElementTree import Element

from convert.adapters.freecad.EditRead.Sketch.SavedPrimitive import ReadPrimitive
from convert.adapters.freecad.EditRead.XmlField import EditChild, EditScalar
from convert.adapters.freecad.Native import NativeObject
from interchange.geometry.models.GeometryCurves import LineGeometry
from interchange.geometry.models.VectorPlane import PlaneVector


# freecad regenerates these two coordinate axes without creating external source dependencies
def CheckAxis(NodeValue: Element, Identity: str, EndPoint: PlaneVector) -> None:
    if (
        NodeValue.tag != "Geometry"
        or NodeValue.attrib
        != {"type": "Part::GeomLineSegment", "id": Identity, "migrated": "1"}
        or tuple(Value.tag for Value in NodeValue)
        != ("GeoExtensions", "LineSegment", "Construction")
        or len(NodeValue[1])
    ):
        raise ValueError("FreeCAD saved sketch external geometry changed")
    Extensions, Segment, Construction = NodeValue
    if (
        Extensions.attrib != {"count": "2"}
        or len(Extensions) != 2
        or any(Value.tag != "GeoExtension" or len(Value) for Value in Extensions)
        or Extensions[0].attrib
        != {
            "type": "Sketcher::SketchGeometryExtension",
            "id": Identity,
            "internalGeometryType": "0",
            "geometryModeFlags": "0" * 30 + "10",
            "geometryLayer": "0",
        }
        or Extensions[1].attrib
        != {"type": "Sketcher::ExternalGeometryExtension", "Ref": "", "Flags": "0"}
        or Construction.attrib != {"value": "1"}
        or len(Construction)
        or ReadPrimitive(Segment, "LineSegment")
        != LineGeometry(PlaneVector(0, 0), EndPoint)
    ):
        raise ValueError("FreeCAD saved sketch external axes changed")


# only built in axis caches can appear beside a self contained sketch
def CheckExternal(Native: NativeObject) -> None:
    if "ExternalGeometry" in Native.properties:
        LinkList = EditChild(
            Native, "ExternalGeometry", "App::PropertyLinkSubList", "LinkSubList"
        )
        if len(LinkList) or LinkList.attrib != {"count": "0"}:
            raise ValueError("FreeCAD saved sketch added external geometry links")
    if "ExternalGeo" in Native.properties:
        Geometries = EditChild(
            Native, "ExternalGeo", "Part::PropertyGeometryList", "GeometryList"
        )
        if Geometries.get("count") != "2" or len(Geometries) != 2:
            raise ValueError("FreeCAD saved sketch external geometry changed")
        CheckAxis(Geometries[0], "-1", PlaneVector(1, 0))
        CheckAxis(Geometries[1], "-2", PlaneVector(0, 1))
    if "ExternalTypes" in Native.properties:
        Types = EditChild(
            Native, "ExternalTypes", "App::PropertyIntegerList", "IntegerList"
        )
        if (
            Types.get("count") != "1"
            or len(Types) != 1
            or Types[0].tag != "I"
            or Types[0].attrib != {"v": "0"}
            or len(Types[0])
        ):
            raise ValueError("FreeCAD saved sketch external geometry types changed")
    for NameValue, TypeName, ChildName, Expected in (
        ("_ExternalGeoVersion", "App::PropertyInteger", "Integer", "0"),
        ("MakeInternals", "App::PropertyBool", "Bool", "false"),
    ):
        if (
            NameValue in Native.properties
            and EditScalar(Native, NameValue, TypeName, ChildName) != Expected
        ):
            raise ValueError(
                "FreeCAD saved sketch external or internal geometry mode changed"
            )
