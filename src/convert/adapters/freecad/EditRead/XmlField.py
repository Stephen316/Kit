# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from math import isfinite as IsFinite
from re import compile as CompilePattern
from xml.etree.ElementTree import Element

from convert.adapters.freecad.Native import NativeObject

# strict numeric tokens prevent permissive fallback values from concealing archive edits
KEditNumber = CompilePattern(
    r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?"
)


# duplicate child records cannot establish which value the native object used
def OnlyEditChild(Parent: Element, TagName: str) -> Element:
    if len(Parent) != 1 or Parent[0].tag != TagName:
        raise ValueError(
            f"FreeCAD editable {Parent.get('name', Parent.tag)} has an invalid {TagName} record"
        )
    return Parent[0]


# proof reads declared native property types without silent coercion or missing defaults
def EditChild(
    ObjectValue: NativeObject, NameValue: str, TypeName: str, ChildName: str
) -> Element:
    PropValue = ObjectValue.properties.get(NameValue)
    if PropValue is None or PropValue.get("type") != TypeName:
        raise ValueError(
            f"FreeCAD editable {ObjectValue.name}.{NameValue} has a missing or changed property type"
        )
    return OnlyEditChild(PropValue, ChildName)


# missing values differ from explicitly empty native links
def EditAttr(NodeValue: Element, AttrName: str) -> str:
    TextValue = NodeValue.get(AttrName)
    if TextValue is None:
        raise ValueError(f"FreeCAD editable {NodeValue.tag} lacks {AttrName}")
    return TextValue


# quantities from validated xml must still have a finite exact numeric representation
def EditFloat(NodeValue: Element, AttrName: str) -> float:
    TextValue = EditAttr(NodeValue, AttrName)
    if len(TextValue) > 128 or KEditNumber.fullmatch(TextValue) is None:
        raise ValueError(
            f"FreeCAD editable {NodeValue.tag}.{AttrName} is not a numeric value"
        )
    Number = float(TextValue)
    if not IsFinite(Number):
        raise ValueError(f"FreeCAD editable {NodeValue.tag}.{AttrName} is nonfinite")
    return Number


# simple values share the strict typed property and child qualification
def EditScalar(
    ObjectValue: NativeObject, NameValue: str, TypeName: str, ChildName: str
) -> str:
    return EditAttr(EditChild(ObjectValue, NameValue, TypeName, ChildName), "value")


# native depth and placement expressions must retain their single direct reference
def CheckEditExpr(ObjectValue: NativeObject, PathValue: str, Expected: str) -> None:
    Engine = EditChild(
        ObjectValue,
        "ExpressionEngine",
        "App::PropertyExpressionEngine",
        "ExpressionEngine",
    )
    Expression = OnlyEditChild(Engine, "Expression")
    if (
        Engine.get("count") != "1"
        or Expression.get("path") != PathValue
        or Expression.get("expression") != Expected
    ):
        raise ValueError(
            f"FreeCAD editable {ObjectValue.name}.{PathValue} expression binding changed"
        )


# undriven saved objects must not acquire a second expression path
def CheckNoEditExpr(ObjectValue: NativeObject) -> None:
    Engine = EditChild(
        ObjectValue,
        "ExpressionEngine",
        "App::PropertyExpressionEngine",
        "ExpressionEngine",
    )
    if len(Engine) or Engine.get("count") != "0":
        raise ValueError(
            f"FreeCAD editable {ObjectValue.name} property expressions changed"
        )
