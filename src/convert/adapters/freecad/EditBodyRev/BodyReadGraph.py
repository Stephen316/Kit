# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from collections.abc import Mapping
from dataclasses import dataclass as MakeDataClass
from xml.etree.ElementTree import Element

from convert.adapters.base import ParseUntrusted
from convert.adapters.freecad.Archive import BuildDocXmlMut
from convert.adapters.freecad.EditAxisRev.AxisReadGraph import (
    KGroupOptional,
    KLiveRevFields,
)
from convert.adapters.freecad.EditBodyRev.BodyRevPlan import BodyRevPlan
from convert.adapters.freecad.EditRead.EditObjects import RequireEditObj
from convert.adapters.freecad.EditRead.EditPlacement import CheckEditFrame
from convert.adapters.freecad.EditRead.Revolve.RevGraphLinks import RequireRevProp
from convert.adapters.freecad.EditRead.Sketch.SketchGraph import (
    CheckObjFields,
    CheckObjState,
)
from convert.adapters.freecad.Native import NativeObject, ParseObjects
from interchange.document.models.DocumentModel import CadDocument
from interchange.geometry.models.Transform import KTransformIdentity

# independent cache and solver witnesses qualify these live extrusion fields separately
KLiveExtFields = frozenset({"Dir", "LengthFwd", "ExpressionEngine"})

# native saves add the persistent shadow name to the exact original edge selection
KLivePickFields = frozenset({"Selection"})


# compiled source names bind every mutable native control to its original feature
@MakeDataClass(frozen=True, slots=True)
class BodyGraph:
    Seed: NativeObject
    Revolve: NativeObject
    Source: NativeObject
    Profile: NativeObject
    Pick: NativeObject
    Sheet: NativeObject
    Objects: dict[str, NativeObject]
    Template: dict[str, NativeObject]


# the original writer graph excludes additional features or replacement links
def ReadBodyGraph(
    RootValue: Element,
    Manifest: Mapping[str, object],
    DocValue: CadDocument,
    Plan: BodyRevPlan,
) -> BodyGraph:
    Editable: set[str] = set()
    XmlData, _ = BuildDocXmlMut(Manifest, "", "", EditableFeatures=Editable)
    Template = {Value.name: Value for Value in ParseObjects(ParseUntrusted(XmlData))}
    Objects = ParseObjects(RootValue)
    ByName = {Value.name: Value for Value in Objects}
    if Editable != {Plan.ExtrudeId, Plan.RevolveId} or ByName.keys() != Template.keys():
        raise ValueError("FreeCAD editable body axis native object graph changed")
    if any(
        Node.get("Invalid") or Node.get("Error")
        for Node in RootValue.findall("./Objects/Object")
    ):
        raise ValueError("FreeCAD editable body axis native rebuild is invalid")
    Pick = RequireRevProp(
        Objects, "KitSelectionId", DocValue.selections[0].id, "App::FeaturePython"
    )
    for Actual in Objects:
        CheckBodyObject(Actual, Template[Actual.name], Pick.name)
    return BodyGraph(
        RequireEditObj(Objects, Plan.ExtrudeId, "Part::Extrusion"),
        RequireEditObj(Objects, Plan.RevolveId, "Part::Revolution"),
        RequireEditObj(Objects, Plan.Extrude.SketchId, "Sketcher::SketchObject"),
        RequireEditObj(Objects, Plan.Revolve.SketchId, "Sketcher::SketchObject"),
        Pick,
        ByName["Parameters"],
        ByName,
        Template,
    )


# each generated object keeps its original dependency set and every passive property
def CheckBodyObject(
    Actual: NativeObject, Expected: NativeObject, PickName: str
) -> None:
    Kind = Actual.type_id
    if Kind != Expected.type_id or set(Actual.dependencies) != set(
        Expected.dependencies
    ):
        raise ValueError("FreeCAD editable body axis native dependencies changed")
    Mutable = (
        KLivePickFields
        if Actual.name == PickName
        else {
            "Part::Extrusion": KLiveExtFields,
            "Part::Revolution": KLiveRevFields,
        }.get(Kind, frozenset())
    )
    IsGroup = Kind == "App::DocumentObjectGroup"
    CheckObjFields(
        Actual,
        Expected,
        Mutable=Mutable,
        Optional=KGroupOptional if IsGroup else frozenset(),
    )
    CheckObjState(Actual, Expected)
    if IsGroup or Kind in {"Part::Extrusion", "Part::Revolution"}:
        CheckEditFrame(Actual, "Placement", KTransformIdentity, Optional=True)
