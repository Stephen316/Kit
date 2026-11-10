# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from base64 import b64decode as DecodeBase
from binascii import Error as BaseError
from collections.abc import Mapping
from json import loads as LoadJson

from convert.adapters.freecad.EditRead.XmlField import (
    CheckNoEditExpr,
    EditChild,
    EditScalar,
)
from convert.adapters.freecad.Native import NativeObject

# freecad native saves add only display properties and an empty property expression engine
KCommonFields = {
    "Label": "App::PropertyString",
    "Label2": "App::PropertyString",
    "Visibility": "App::PropertyBool",
    "ExpressionEngine": "App::PropertyExpressionEngine",
}


# known property names and types prevent auxiliary objects from holding modeling data
def CheckProperties(ObjectValue: NativeObject, Fields: Mapping[str, str]) -> None:
    for NameValue, Property in ObjectValue.properties.items():
        Expected = Fields.get(NameValue, KCommonFields.get(NameValue))
        if Expected is None or Property.get("type") != Expected:
            raise ValueError(
                "FreeCAD editable spreadsheet has an additional or changed native property"
            )
        if any(Value.get("file") for Value in Property.iter()):
            raise ValueError(
                "FreeCAD editable spreadsheet has an additional native file reference"
            )
    if "ExpressionEngine" in ObjectValue.properties:
        CheckNoEditExpr(ObjectValue)


# native feature python metadata may have only the built in null proxy
def CheckEmptyProxy(ObjectValue: NativeObject) -> None:
    if "Proxy" not in ObjectValue.properties:
        return
    Proxy = EditChild(ObjectValue, "Proxy", "App::PropertyPythonObject", "Python")
    if (
        len(Proxy)
        or set(Proxy.attrib) != {"value", "encoded", "json"}
        or Proxy.get("encoded") != "yes"
        or Proxy.get("json") != "yes"
        or len(Proxy.get("value", "")) > 16
    ):
        raise ValueError("FreeCAD editable spreadsheet has an additional native proxy")
    try:
        Value = DecodeBase(Proxy.get("value", ""), validate=True)
    except (BaseError, ValueError) as ErrorInfo:
        raise ValueError(
            "FreeCAD editable spreadsheet has an invalid native proxy"
        ) from ErrorInfo
    if Value != b"null":
        raise ValueError("FreeCAD editable spreadsheet has an additional native proxy")


# the native dependency graph must still consist only of generated document links
def CheckSheetDeps(ObjectValue: NativeObject, Expected: tuple[str, ...]) -> None:
    if len(ObjectValue.dependencies) != len(Expected) or set(
        ObjectValue.dependencies
    ) != set(Expected):
        raise ValueError("FreeCAD editable spreadsheet native dependencies changed")


# standalone groups do not hold geometry or newly added native objects
def CheckLinkList(
    ObjectValue: NativeObject, FieldName: str, Expected: tuple[str, ...]
) -> None:
    LinkList = EditChild(ObjectValue, FieldName, "App::PropertyLinkList", "LinkList")
    if (
        LinkList.get("count") != str(len(Expected))
        or tuple(Value.get("value") for Value in LinkList if Value.tag == "Link")
        != Expected
        or len(LinkList) != len(Expected)
    ):
        raise ValueError("FreeCAD editable spreadsheet native group membership changed")


# native group extensions and their transient property carry no editable geometry
def CheckGroupState(ObjectValue: NativeObject) -> None:
    if ObjectValue.extensions and (
        len(ObjectValue.extensions) != 1
        or ObjectValue.extensions[0].attrib
        != {
            "type": "App::GroupExtension",
            "name": "GroupExtension",
        }
        or len(ObjectValue.extensions[0])
    ):
        raise ValueError(
            "FreeCAD editable spreadsheet has an additional native extension"
        )
    if ObjectValue.transient_properties and (
        len(ObjectValue.transient_properties) != 1
        or ObjectValue.transient_properties[0].get("name") != "_GroupTouched"
        or ObjectValue.transient_properties[0].get("type") != "App::PropertyBool"
    ):
        raise ValueError(
            "FreeCAD editable spreadsheet has an additional native transient property"
        )


# one readback configuration may only retain its original empty override record
def CheckSheetCfg(ObjectValue: NativeObject) -> None:
    for NameValue, TypeName, TagName, Expected in (
        ("KitConfigurationId", "App::PropertyString", "String", "fusion-projection"),
        ("Active", "App::PropertyBool", "Bool", "true"),
        ("Parameters", "App::PropertyLink", "Link", "Parameters"),
        ("ParameterOverridesJSON", "App::PropertyString", "String", '{"$tuple":[]}'),
    ):
        if EditScalar(ObjectValue, NameValue, TypeName, TagName) != Expected:
            raise ValueError("FreeCAD editable spreadsheet configuration changed")
    CheckLinkList(ObjectValue, "SuppressedFeatures", ())
    ConfigText = EditScalar(
        ObjectValue, "SourceConfigurationJSON", "App::PropertyString", "String"
    )
    if len(ConfigText) > 512 or LoadJson(ConfigText) != {
        "$type": "Configuration",
        "id": "fusion-projection",
        "name": "History projection",
        "active": True,
        "parent_id": None,
        "overrides": {"$tuple": []},
        "suppressed_feature_ids": {"$tuple": []},
        "attributes": {},
    }:
        raise ValueError("FreeCAD editable spreadsheet source configuration changed")
