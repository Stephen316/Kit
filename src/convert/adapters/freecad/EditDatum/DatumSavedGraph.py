# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt


from xml.etree.ElementTree import Element

from convert.adapters.freecad.EditRead.EditPlacement import (
    CheckEditFrame,
    ReadEditFrame,
)
from convert.adapters.freecad.EditRead.PlaneRev.PlaneNativeExpr import CheckPlaneExpr
from convert.adapters.freecad.EditRead.Sketch.SketchGraph import (
    CheckObjFields,
    CheckObjState,
    IsSameNode,
)
from convert.adapters.freecad.EditRead.XmlField import OnlyEditChild
from convert.adapters.freecad.EditScale.ScaleSavedGraphFields import CheckScaleAttr
from convert.adapters.freecad.EditScale.ScaleSavedGraphXml import CheckGraphTree
from convert.adapters.freecad.Native import NativeObject, ParseObjects

# plane expressions and placements are checked against separate native controls
KDatumMutable = frozenset({"ExpressionEngine"})


# shape free native saves retain only an empty inline string hasher
def CheckDatumTree(RootValue: Element) -> None:
    Hasher = RootValue.find("StringHasher")
    if Hasher is not None:
        if (
            not len(RootValue)
            or RootValue[0] is not Hasher
            or RootValue.get("StringHasher") != "1"
            or Hasher.attrib != {"saveall": "0", "threshold": "0", "count": "0"}
            or len(Hasher)
            or (Hasher.text or "").strip()
        ):
            raise ValueError("FreeCAD editable datum native string hasher changed")
        Unhashed = Element(RootValue.tag, RootValue.attrib)
        Unhashed.extend(RootValue[1:])
        RootValue = Unhashed
    try:
        CheckGraphTree(RootValue)
    except ValueError as ErrorInfo:
        raise ValueError(
            "FreeCAD editable datum native document framing changed"
        ) from ErrorInfo


# the original object graph excludes new features and changed native links
def ReadDatumGraph(
    RootValue: Element, Template: Element
) -> tuple[dict[str, NativeObject], dict[str, NativeObject], bool]:
    CheckDatumTree(RootValue)
    Native = {Value.name: Value for Value in ParseObjects(RootValue)}
    Original = {Value.name: Value for Value in ParseObjects(Template)}
    if Native.keys() != Original.keys():
        raise ValueError("FreeCAD editable datum native object inventory changed")
    Touched = {Value.name for Value in Native.values() if Value.touched}
    SeedTouched = {Value.name for Value in Original.values() if Value.touched}
    if Touched and Touched != SeedTouched:
        raise ValueError("FreeCAD editable datum native rebuild is pending")
    for NameValue, Value in Native.items():
        Expected = Original[NameValue]
        if (
            Value.type_id != Expected.type_id
            or Value.object_id != Expected.object_id
            or set(Value.dependencies) != set(Expected.dependencies)
        ):
            raise ValueError(
                f"FreeCAD editable datum native {NameValue} routing changed"
            )
        CheckDatumObj(Value, Expected)
    return Native, Original, bool(Touched)


# saved native defaults may add display fields but cannot add modeling behavior
def CheckDatumObj(Native: NativeObject, Expected: NativeObject) -> None:
    CheckObjFields(Native, Expected, Mutable=KDatumMutable)
    CheckObjState(Native, Expected)
    if {"Shape", "InternalShape"} & Native.properties.keys():
        raise ValueError("FreeCAD editable datum includes an unexpected shape")
    for NameValue, Property in Native.properties.items():
        Before = Expected.properties.get(NameValue)
        if Before is not None:
            CheckScaleAttr(Before, Property)
        elif Property.attrib.keys() - {"name", "type", "status"}:
            raise ValueError("FreeCAD editable datum native property metadata changed")
    if "Visibility" in Expected.properties and not IsSameNode(
        OnlyEditChild(Native.properties["Visibility"], "Bool"),
        Expected.properties["Visibility"][0],
    ):
        raise ValueError("FreeCAD editable datum native visibility changed")
    Engine = Expected.properties.get("ExpressionEngine")
    if Engine is not None:
        try:
            CheckPlaneExpr(
                Native,
                tuple(
                    (Value.attrib["path"], Value.attrib["expression"])
                    for Value in Engine[0]
                ),
            )
        except ValueError as ErrorInfo:
            raise ValueError(
                "FreeCAD editable datum placement expression changed"
            ) from ErrorInfo
    if "Placement" in Native.properties and "KitFeatureId" not in Expected.properties:
        CheckEditFrame(Native, "Placement", ReadEditFrame(Expected, "Placement"))
