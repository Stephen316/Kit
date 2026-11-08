# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.adapters.freecad.EditRead.EditPlacement import CheckEditFrame
from convert.adapters.freecad.EditRead.Formula.SheetScaffold import CheckGroupState
from convert.adapters.freecad.EditRead.XmlField import EditChild, EditFloat, EditScalar
from convert.adapters.freecad.Native import NativeObject
from interchange.geometry.models.Transform import KTransformIdentity

# native saves add attachment and display properties absent from generated sketches
KSketchExtras = {
    "ArcFitTolerance": "App::PropertyPrecision",
    "AttacherEngine": "App::PropertyEnumeration",
    "AttacherType": "App::PropertyString",
    "AttachmentOffset": "App::PropertyPlacement",
    "Exports": "App::PropertyLinkListHidden",
    "ExternalGeo": "Part::PropertyGeometryList",
    "ExternalGeometry": "App::PropertyLinkSubList",
    "ExternalTypes": "App::PropertyIntegerList",
    "FullyConstrained": "App::PropertyBool",
    "MakeInternals": "App::PropertyBool",
    "MapMode": "App::PropertyEnumeration",
    "MapPathParameter": "App::PropertyFloat",
    "MapReversed": "App::PropertyBool",
    "ShapeMaterial": "Materials::PropertyMaterial",
    "_ExternalGeoVersion": "App::PropertyInteger",
}

# the standalone graph has only the observed default native extension families
KSketchObjExtra = {
    "Sketcher::SketchObject": KSketchExtras,
    "App::Plane": {"Role": "App::PropertyString"},
    "App::FeaturePython": {"Proxy": "App::PropertyPythonObject"},
    "Part::Feature": {
        "Placement": "App::PropertyPlacement",
        "ShapeMaterial": "Materials::PropertyMaterial",
    },
    "Part::Revolution": {
        "Placement": "App::PropertyPlacement",
        "ShapeMaterial": "Materials::PropertyMaterial",
    },
}


# only generated attachment and non geometric native extension state may be present
def CheckExtensions(ObjectValue: NativeObject) -> None:
    KindValue = ObjectValue.type_id
    if KindValue == "App::DocumentObjectGroup":
        CheckGroupState(ObjectValue)
        return
    Extensions = ObjectValue.extensions
    if Extensions and (
        KindValue != "Sketcher::SketchObject"
        or len(Extensions) != 1
        or Extensions[0].attrib
        != {"type": "Part::AttachExtension", "name": "AttachExtension"}
        or len(Extensions[0])
    ):
        raise ValueError("FreeCAD editable sketch has additional native extensions")
    Transient = ObjectValue.transient_properties
    if Transient and (
        KindValue
        not in {
            "App::Plane",
            "Sketcher::SketchObject",
            "Part::Feature",
            "Part::Revolution",
        }
        or len(Transient) != 1
        or Transient[0].get("name") != "_ElementMapVersion"
        or Transient[0].get("type") != "App::PropertyString"
        or len(Transient[0])
    ):
        raise ValueError("FreeCAD editable sketch has additional transient properties")


# supported attachments remain disabled so the saved local frame retains its original meaning
def CheckSketchOpts(ObjectValue: NativeObject) -> None:
    CheckEditFrame(ObjectValue, "AttachmentOffset", KTransformIdentity, Optional=True)
    Properties = ObjectValue.properties
    for Field, TagName, Expected in (
        ("AttacherType", "String", "Attacher::AttachEnginePlane"),
        ("MapMode", "Integer", "0"),
        ("MapReversed", "Bool", "false"),
        ("MakeInternals", "Bool", "false"),
    ):
        if (
            Field in Properties
            and EditScalar(ObjectValue, Field, KSketchExtras[Field], TagName)
            != Expected
        ):
            raise ValueError(f"FreeCAD editable sketch {Field} changed")
    for Field in ("ArcFitTolerance", "MapPathParameter"):
        if (
            Field in Properties
            and EditFloat(
                EditChild(ObjectValue, Field, KSketchExtras[Field], "Float"), "value"
            )
            != 0.0
        ):
            raise ValueError(f"FreeCAD editable sketch {Field} changed")
    if "Exports" in Properties:
        Exports = EditChild(
            ObjectValue, "Exports", KSketchExtras["Exports"], "LinkList"
        )
        if len(Exports) or Exports.get("count") != "0":
            raise ValueError("FreeCAD editable sketch external exports changed")
    Engine = Properties.get("AttacherEngine")
    if Engine is not None and (
        len(Engine) != 2
        or Engine[0].tag != "Integer"
        or Engine[0].attrib != {"value": "1", "CustomEnum": "true"}
        or Engine[1].tag != "CustomEnumList"
        or Engine[1].get("count") != "4"
        or tuple(Value.get("value") for Value in Engine[1] if Value.tag == "Enum")
        != ("Engine 3D", "Engine Plane", "Engine Line", "Engine Point")
        or len(Engine[1]) != 4
    ):
        raise ValueError("FreeCAD editable sketch attachment engine changed")
