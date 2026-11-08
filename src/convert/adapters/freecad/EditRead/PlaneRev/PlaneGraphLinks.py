# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from convert.adapters.freecad.Archive import JsonProp
from convert.adapters.freecad.EditRead.EditPlacement import CheckEditFrame
from convert.adapters.freecad.EditRead.Formula.SheetScaffold import (
    CheckEmptyProxy,
    CheckLinkList,
)
from convert.adapters.freecad.EditRead.Revolve.RevGraphLinks import (
    CheckRevDeps,
    CheckRevStep,
)
from convert.adapters.freecad.EditRead.Sketch.SketchDefaults import CheckExtensions
from convert.adapters.freecad.EditRead.XmlField import (
    CheckNoEditExpr,
    EditChild,
    EditScalar,
)
from convert.adapters.freecad.Native import NativeObject
from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.Selection import Selection
from interchange.geometry.models.Transform import KTransformIdentity
from interchange.serialization.EncodeData import ToData


# generated source snapshots corroborate the native object identity and role
def CheckPlaneJson(Native: NativeObject, NameValue: str, Original: object) -> None:
    Expected = JsonProp(NameValue, ToData(Original))[0].get("value")
    if EditScalar(Native, NameValue, "App::PropertyString", "String") != Expected:
        raise ValueError(f"FreeCAD editable plane Revolve {NameValue} changed")


# native links must refer to the resolved source object without changing its role
def CheckPlaneLink(Native: NativeObject, Field: str, Target: str) -> None:
    if EditScalar(Native, Field, "App::PropertyLink", "Link") != Target:
        raise ValueError(f"FreeCAD editable plane Revolve {Field} link changed")


# each selected datum has exactly one support plane link without subelement
def CheckTargetPick(Native: NativeObject, PickValue: Selection, PlaneName: str) -> None:
    CheckExtensions(Native)
    CheckEmptyProxy(Native)
    CheckRevDeps(Native, (PlaneName,))
    CheckPlaneJson(Native, "QueryJSON", PickValue.query)
    CheckPlaneJson(Native, "SourceSelectionJSON", PickValue)
    Paths = EditChild(Native, "Selection", "App::PropertyLinkSubList", "LinkSubList")
    if (
        Paths.attrib != {"count": "1"}
        or len(Paths) != 1
        or Paths[0].tag != "Link"
        or len(Paths[0])
        or Paths[0].attrib != {"obj": PlaneName, "sub": ""}
    ):
        raise ValueError("FreeCAD editable plane Revolve target selection changed")
    CheckStringRows(Native, "EntityKinds", ("support_plane",))
    if "ExpressionEngine" in Native.properties:
        CheckNoEditExpr(Native)


# passive datum timeline rows retain their owned parameters and construction geometry
def CheckDatumStep(
    Native: NativeObject, StepValue: FeatureStep, PlaneName: str
) -> None:
    CheckRevStep(Native, StepValue, "feature-data")
    CheckRevDeps(Native, ("Parameters", PlaneName))
    CheckPlaneLink(Native, "Parameters", "Parameters")
    CheckPlaneLink(Native, "ConstructionPlane", PlaneName)
    CheckStringRows(Native, "ParameterIds", StepValue.parameter_ids)
    CheckNoEditExpr(Native)
    CheckEditFrame(Native, "Placement", KTransformIdentity, Optional=True)


# source string lists must retain their exact identities and ordering
def CheckStringRows(
    Native: NativeObject, Field: str, Expected: tuple[str, ...]
) -> None:
    RowsValue = EditChild(Native, Field, "App::PropertyStringList", "StringList")
    if (
        RowsValue.attrib != {"count": str(len(Expected))}
        or len(RowsValue) != len(Expected)
        or any(
            Value.tag != "String" or len(Value) or Value.attrib != {"value": TextValue}
            for Value, TextValue in zip(RowsValue, Expected, strict=True)
        )
    ):
        raise ValueError(f"FreeCAD editable plane Revolve {Field} changed")


# native result links are corroborated separately from the saved feature expression
def CheckPlaneLinks(
    Native: NativeObject,
    StepValue: FeatureStep,
    ProfileName: str,
    TargetNames: tuple[str, ...],
    SelectionNames: tuple[str, ...],
) -> None:
    if (
        Native.extensions
        or any(
            Value.get("name") != "_ElementMapVersion"
            or Value.get("type") != "App::PropertyString"
            or len(Value)
            for Value in Native.transient_properties
        )
        or len(Native.transient_properties) > 1
    ):
        raise ValueError("FreeCAD editable plane Revolve native extensions changed")
    CheckRevStep(Native, StepValue, "feature")
    CheckRevDeps(Native, (ProfileName, *TargetNames, *SelectionNames, "Sketches"))
    CheckLinkList(Native, "Selections", SelectionNames)
    CheckPlaneLink(Native, "Source", ProfileName)
    CheckPlaneLink(Native, "Sketches", "Sketches")
