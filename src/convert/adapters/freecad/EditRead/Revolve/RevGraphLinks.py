# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from convert.adapters.freecad.Archive import JsonProp
from convert.adapters.freecad.EditRead.Formula.SheetScaffold import (
    CheckEmptyProxy,
    CheckGroupState,
    CheckLinkList,
    CheckSheetCfg,
)
from convert.adapters.freecad.EditRead.XmlField import (
    CheckNoEditExpr,
    EditChild,
    EditScalar,
)
from convert.adapters.freecad.Native import NativeObject
from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.Selection import Selection
from interchange.geometry.models.Transform import KTransformIdentity
from convert.adapters.freecad.EditRead.EditPlacement import CheckEditFrame
from interchange.serialization.EncodeData import ToData


# metadata identities must not resolve to two independent native objects
def RequireRevProp(
    Objects: tuple[NativeObject, ...],
    Field: str,
    Identity: str,
    TypeName: str,
) -> NativeObject:
    Matches = tuple(
        Value
        for Value in Objects
        if (PropValue := Value.properties.get(Field)) is not None
        and any(
            NodeValue.get("value") == Identity
            for NodeValue in PropValue.findall("./String")
        )
    )
    if (
        len(Matches) != 1
        or Matches[0].type_id != TypeName
        or EditScalar(Matches[0], Field, "App::PropertyString", "String") != Identity
    ):
        raise ValueError(
            "FreeCAD editable Revolve native object identity is unresolved"
        )
    return Matches[0]


# native dependency lists can repeat a link once for its expression reference
def CheckRevDeps(Native: NativeObject, Expected: tuple[str, ...]) -> None:
    if set(Native.dependencies) != set(Expected):
        raise ValueError("FreeCAD editable Revolve native dependencies changed")


# group membership cannot hide additional native geometry or a replaced body tip
def CheckRevGroup(Native: NativeObject, Members: tuple[str, ...]) -> None:
    if Native.type_id != "App::DocumentObjectGroup":
        raise ValueError("FreeCAD editable Revolve native group type changed")
    CheckGroupState(Native)
    CheckLinkList(Native, "Group", Members)
    CheckRevDeps(Native, Members)
    if "ExpressionEngine" in Native.properties:
        CheckNoEditExpr(Native)


# current angular features and passive sketch history retain their original kit roles
def CheckRevStep(Native: NativeObject, Feature: FeatureStep, RoleName: str) -> None:
    for Field, Expected in (
        ("KitRole", RoleName),
        ("FeatureKind", Feature.kind.value),
        ("Operation", Feature.operation.value if Feature.operation is not None else ""),
        (
            "SourceFeatureJSON",
            JsonProp("SourceFeatureJSON", ToData(Feature))[0].get("value"),
        ),
    ):
        if EditScalar(Native, Field, "App::PropertyString", "String") != Expected:
            raise ValueError(f"FreeCAD editable Revolve native {Field} changed")
    if (
        EditScalar(Native, "TimelineOrder", "App::PropertyInteger", "Integer")
        != str(Feature.order)
        or EditScalar(Native, "Suppressed", "App::PropertyBool", "Bool") != "false"
    ):
        raise ValueError("FreeCAD editable Revolve timeline state changed")


# the selected built in axis stays a source query with no editable native link
def CheckRevPick(Native: NativeObject, PickValue: Selection) -> None:
    CheckEmptyProxy(Native)
    CheckRevDeps(Native, ())
    for Field, TypeName, ChildName in (
        ("Selection", "App::PropertyLinkSubList", "LinkSubList"),
        ("EntityKinds", "App::PropertyStringList", "StringList"),
    ):
        ListValue = EditChild(Native, Field, TypeName, ChildName)
        if len(ListValue) or ListValue.get("count") != "0":
            raise ValueError("FreeCAD editable Revolve axis selection links changed")
    for Field, Source in (
        ("QueryJSON", ToData(PickValue.query)),
        ("SourceSelectionJSON", ToData(PickValue)),
    ):
        Expected = JsonProp(Field, Source)[0].get("value")
        if EditScalar(Native, Field, "App::PropertyString", "String") != Expected:
            raise ValueError("FreeCAD editable Revolve origin axis provenance changed")
    if "ExpressionEngine" in Native.properties:
        CheckNoEditExpr(Native)


# the original configuration has no independent edits or suppression controls
def CheckRevConfig(Native: NativeObject) -> None:
    CheckSheetCfg(Native)
    CheckRevDeps(Native, ("Parameters",))
    CheckEmptyProxy(Native)
    if "ExpressionEngine" in Native.properties:
        CheckNoEditExpr(Native)


# a passive timeline object cannot replace its sketch or introduce a second placement
def CheckRevCarrier(
    Native: NativeObject, Feature: FeatureStep, SketchName: str
) -> None:
    CheckRevStep(Native, Feature, "feature-data")
    CheckRevDeps(Native, (SketchName, "Parameters"))
    for Field, Expected in (("Profile", SketchName), ("Parameters", "Parameters")):
        if EditScalar(Native, Field, "App::PropertyLink", "Link") != Expected:
            raise ValueError("FreeCAD editable Revolve passive timeline link changed")
    CheckNoEditExpr(Native)
    CheckEditFrame(Native, "Placement", KTransformIdentity, Optional=True)
