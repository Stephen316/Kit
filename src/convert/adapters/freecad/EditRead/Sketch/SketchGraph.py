# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from collections.abc import Collection, Iterable
from xml.etree.ElementTree import Element

from convert.adapters.freecad.EditRead.EditPlacement import CheckEditFrame
from convert.adapters.freecad.EditRead.Formula.SheetScaffold import CheckEmptyProxy
from convert.adapters.freecad.EditRead.Sketch.SketchDefaults import (
    CheckExtensions,
    CheckSketchOpts,
    KSketchObjExtra,
)
from convert.adapters.freecad.EditRead.XmlField import CheckNoEditExpr, EditScalar
from convert.adapters.freecad.Native import NativeObject, ParseObjects
from interchange.geometry.models.Transform import KTransformIdentity

# these mutable properties are validated separately or carry only presentation state
KCheckedElsewhere = frozenset(
    {
        "Label",
        "Visibility",
        "KitManifestData",
        "KitManifestSHA256",
        "Placement",
        "Geometry",
        "Constraints",
        "Shape",
        "InternalShape",
        "cells",
        "columnWidths",
        "rowHeights",
    }
)


# comparing the generated property payload avoids trusting replacement native links or formulas
def IsSameNode(Actual: Element, Expected: Element) -> bool:
    return (
        Actual.tag == Expected.tag
        and Actual.attrib == Expected.attrib
        and (Actual.text or "").strip() == (Expected.text or "").strip()
        and len(Actual) == len(Expected)
        and all(
            IsSameNode(Value, Original)
            for Value, Original in zip(Actual, Expected, strict=True)
        )
    )


# native saves can add only the expected typed defaults for each generated object
def CheckObjFields(
    Actual: NativeObject,
    Expected: NativeObject,
    *,
    Mutable: Collection[str] = (),
    Optional: Collection[str] = (),
) -> None:
    Extra = KSketchObjExtra.get(Actual.type_id, {})
    Common = {
        "Label2": "App::PropertyString",
        "ExpressionEngine": "App::PropertyExpressionEngine",
    }
    if not Expected.properties.keys() - Optional <= Actual.properties.keys():
        raise ValueError("FreeCAD editable sketch object is missing a native property")
    for NameValue, Property in Actual.properties.items():
        Original = Expected.properties.get(NameValue)
        TypeName = (
            Original.get("type")
            if Original is not None
            else Extra.get(NameValue, Common.get(NameValue))
        )
        if TypeName is None or Property.get("type") != TypeName:
            raise ValueError(
                f"FreeCAD editable sketch {Actual.name}.{NameValue} native property changed"
            )
        if (
            Original is not None
            and NameValue not in KCheckedElsewhere
            and NameValue not in Mutable
            and (
                len(Property) != len(Original)
                or not all(
                    IsSameNode(Value, OldValue)
                    for Value, OldValue in zip(Property, Original, strict=True)
                )
            )
        ):
            raise ValueError(
                f"FreeCAD editable sketch {Actual.name}.{NameValue} binding changed"
            )
        if NameValue not in {"Shape", "InternalShape"} and any(
            Value.get("file") for Value in Property.iter()
        ):
            raise ValueError(
                "FreeCAD editable sketch has additional native file references"
            )


# unrelated carrier objects retain empty default behavior while sketch options stay fixed
def CheckObjState(Actual: NativeObject, Expected: NativeObject) -> None:
    CheckExtensions(Actual)
    CheckEmptyProxy(Actual)
    if (
        "ExpressionEngine" in Actual.properties
        and "ExpressionEngine" not in Expected.properties
    ):
        CheckNoEditExpr(Actual)
    if Actual.type_id == "Sketcher::SketchObject":
        CheckSketchOpts(Actual)
    if Actual.type_id == "Part::Feature":
        CheckEditFrame(Actual, "Placement", KTransformIdentity, Optional=True)
    if (
        Actual.type_id == "App::Plane"
        and "Role" in Actual.properties
        and EditScalar(Actual, "Role", "App::PropertyString", "String")
    ):
        raise ValueError("FreeCAD editable sketch plane role changed")


# exact generated objects and dependency sets delimit all mutable sketch state
def ReadSketchGraph(
    RootValue: Element, Template: Element
) -> tuple[dict[str, NativeObject], dict[str, NativeObject]]:
    Objects = {Value.name: Value for Value in ParseObjects(RootValue)}
    Expected = {Value.name: Value for Value in ParseObjects(Template)}
    if Objects.keys() != Expected.keys():
        raise ValueError(
            "FreeCAD editable sketch has an additional or missing native object"
        )
    for NameValue, Actual in Objects.items():
        Original = Expected[NameValue]
        if Actual.type_id != Original.type_id or set(Actual.dependencies) != set(
            Original.dependencies
        ):
            raise ValueError("FreeCAD editable sketch native dependency graph changed")
        CheckObjFields(Actual, Original)
        CheckObjState(Actual, Original)
    return Objects, Expected


# indexing native identities once keeps multi sketch readback linear
def IndexSketchObjs(Objects: Iterable[NativeObject]) -> dict[str, NativeObject]:
    Result: dict[str, NativeObject] = {}
    for Native in Objects:
        if Native.type_id not in {"App::Plane", "Sketcher::SketchObject"}:
            continue
        Identity = EditScalar(Native, "KitId", "App::PropertyString", "String")
        if not Identity or Identity in Result:
            raise ValueError("FreeCAD editable sketch native identity is ambiguous")
        Result[Identity] = Native
    return Result
