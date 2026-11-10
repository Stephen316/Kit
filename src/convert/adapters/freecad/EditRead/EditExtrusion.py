# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from math import isclose as IsClose

from convert.adapters.freecad.EditRead.EditPlacement import CheckEditFrame
from convert.adapters.freecad.EditRead.XmlField import (
    EditAttr,
    EditChild,
    EditFloat,
    EditScalar,
)
from convert.adapters.freecad.Native import EntryName, NativeObject
from interchange.geometry.models.Transform import Transform
from interchange.geometry.models.VectorSpace import SpaceVector


# nondepth controls must remain in the exact independent blind extrusion family
def CheckEditOpts(Feature: NativeObject) -> None:
    for Field, Expected in (
        ("Solid", "true"),
        ("Reversed", "false"),
        ("Symmetric", "false"),
        ("Suppressed", "false"),
    ):
        if EditScalar(Feature, Field, "App::PropertyBool", "Bool") != Expected:
            raise ValueError(f"FreeCAD editable extrusion {Field} changed")
    for Field, Expected in (
        ("KitRole", "feature"),
        ("FeatureKind", "extrusion"),
        ("Operation", "create"),
        ("EndCondition", "blind"),
    ):
        if EditScalar(Feature, Field, "App::PropertyString", "String") != Expected:
            raise ValueError(f"FreeCAD editable extrusion {Field} changed")
    if EditScalar(Feature, "DirMode", "App::PropertyEnumeration", "Integer") != "0":
        raise ValueError("FreeCAD editable extrusion direction mode changed")
    if "DirLink" in Feature.properties:
        LinkValue = EditChild(Feature, "DirLink", "App::PropertyLinkSub", "LinkSub")
        if (
            len(LinkValue)
            or LinkValue.get("value") != ""
            or LinkValue.get("count") != "0"
        ):
            raise ValueError("FreeCAD editable extrusion direction link changed")
    for Field in ("TaperAngle", "TaperAngleRev"):
        if (
            Field in Feature.properties
            and EditFloat(
                EditChild(Feature, Field, "App::PropertyAngle", "Float"), "value"
            )
            != 0.0
        ):
            raise ValueError(f"FreeCAD editable extrusion {Field} changed")


# face construction defaults persisted by freecad must still describe the original profile mode
def CheckEditMaker(Feature: NativeObject) -> None:
    for Field, KindValue, TagName, Expected in (
        ("FaceMakerClass", "App::PropertyString", "String", "Part::FaceMakerExtrusion"),
        ("InnerWireTaper", "App::PropertyEnumeration", "Integer", "1"),
    ):
        if (
            Field in Feature.properties
            and EditScalar(Feature, Field, KindValue, TagName) != Expected
        ):
            raise ValueError(f"FreeCAD editable extrusion {Field} changed")
    ModeValue = Feature.properties.get("FaceMakerMode")
    if ModeValue is not None:
        Selected = ModeValue.findall("./Integer")
        Choices = ModeValue.findall("./CustomEnumList")
        if (
            ModeValue.get("type") != "App::PropertyEnumeration"
            or len(Selected) != 1
            or Selected[0].get("value") != "2"
            or len(Choices) != 1
            or tuple(Value.get("value") for Value in Choices[0])
            != ("Simple", "Cheese", "Extrusion", "Bullseye")
        ):
            raise ValueError("FreeCAD editable extrusion face maker mode changed")


# the signed forward property is usable only when every other shape control is unchanged
def ReadEditDepth(Feature: NativeObject, Direction: SpaceVector) -> float:
    CheckEditOpts(Feature)
    CheckEditMaker(Feature)
    CheckEditFrame(Feature, "Placement", Transform(), Optional=True)
    DirNode = EditChild(Feature, "Dir", "App::PropertyVector", "PropertyVector")
    if any(
        not IsClose(EditFloat(DirNode, Field), Value, rel_tol=0.0, abs_tol=1e-9)
        for Field, Value in zip(
            ("valueX", "valueY", "valueZ"),
            (Direction.x, Direction.y, Direction.z),
            strict=True,
        )
    ):
        raise ValueError("FreeCAD editable extrusion direction changed")
    Forward = EditFloat(
        EditChild(Feature, "LengthFwd", "App::PropertyDistance", "Float"), "value"
    )
    Reverse = EditFloat(
        EditChild(Feature, "LengthRev", "App::PropertyDistance", "Float"), "value"
    )
    if Forward == 0.0 or Reverse != 0.0:
        raise ValueError("FreeCAD editable extrusion has zero or reverse distance")
    return Forward


# native recompute evidence comes from the linked feature shape rather than a static carrier
def ReadShapeEntry(Feature: NativeObject) -> str:
    Shape = Feature.properties.get("Shape")
    Parts = () if Shape is None else Shape.findall("./Part")
    if (
        Shape is None
        or Shape.get("type") != "Part::PropertyPartShape"
        or len(Parts) != 1
    ):
        raise ValueError("FreeCAD editable extrusion is missing its native shape")
    return EntryName(EditAttr(Parts[0], "file"))
