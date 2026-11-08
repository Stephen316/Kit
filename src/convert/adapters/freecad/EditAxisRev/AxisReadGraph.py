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
from convert.adapters.freecad.EditAxisRev.AxisRevPlan import AxisRevPlan
from convert.adapters.freecad.EditRead.EditObjects import RequireEditObj
from convert.adapters.freecad.EditRead.EditPlacement import CheckEditFrame
from convert.adapters.freecad.EditRead.EditProfile import CheckEditPlane
from convert.adapters.freecad.EditRead.Sketch.SketchGraph import (
    CheckObjFields,
    CheckObjState,
)
from convert.adapters.freecad.Native import NativeObject, ParseObjects
from interchange.document.models.DocumentModel import CadDocument
from interchange.geometry.models.Transform import KTransformIdentity

# these solver outputs are independently witnessed by the edited controls and caches
KLiveRevFields = frozenset({"Angle", "Axis", "AxisLink", "Base", "ExpressionEngine"})

# freecad can omit the unused identity placement on a document group
KGroupOptional = frozenset({"Placement"})


# the original compiler remains the authority for every generated native connection
@MakeDataClass(frozen=True, slots=True)
class AxisGraph:
    Feature: NativeObject
    Profile: NativeObject
    AxisSketch: NativeObject
    ParamSheet: NativeObject
    Objects: dict[str, NativeObject]
    Template: dict[str, NativeObject]


# native state and connections must still belong to the exact editable writer graph
def ReadAxisGraph(
    RootValue: Element,
    Manifest: Mapping[str, object],
    DocValue: CadDocument,
    PlanValue: AxisRevPlan,
) -> AxisGraph:
    StepValue = DocValue.feature_timeline[-1]
    Editable: set[str] = set()
    XmlData, _ = BuildDocXmlMut(Manifest, "", "", EditableFeatures=Editable)
    Template = {Value.name: Value for Value in ParseObjects(ParseUntrusted(XmlData))}
    Objects = ParseObjects(RootValue)
    ByName = {Value.name: Value for Value in Objects}
    if Editable != {StepValue.id} or ByName.keys() != Template.keys():
        raise ValueError("FreeCAD editable sketch axis native object graph changed")
    for Node in RootValue.findall("./Objects/Object"):
        if Node.get("Invalid") or Node.get("Error"):
            raise ValueError("FreeCAD editable sketch axis rebuild is invalid")
    for Actual in Objects:
        CheckAxisObject(Actual, Template[Actual.name])
    Feature = RequireEditObj(Objects, StepValue.id, "Part::Revolution")
    Profile = RequireEditObj(
        Objects, PlanValue.Revolve.SketchId, "Sketcher::SketchObject"
    )
    AxisSketch = RequireEditObj(
        Objects, PlanValue.AxisSketchId, "Sketcher::SketchObject"
    )
    Sketches = {Value.id: Value for Value in DocValue.sketches}
    Planes = {Value.id: Value for Value in DocValue.support_planes}
    for Native, Identity in (
        (Profile, PlanValue.Revolve.SketchId),
        (AxisSketch, PlanValue.AxisSketchId),
    ):
        Plane = Planes[Sketches[Identity].support_plane_id]
        CheckEditPlane(Native, RequireEditObj(Objects, Plane.id, "App::Plane"), Plane)
    return AxisGraph(
        Feature, Profile, AxisSketch, ByName["Parameters"], ByName, Template
    )


# generated object fields isolate editable geometry from passive history and metadata
def CheckAxisObject(Actual: NativeObject, Expected: NativeObject) -> None:
    if Actual.type_id != Expected.type_id or set(Actual.dependencies) != set(
        Expected.dependencies
    ):
        raise ValueError("FreeCAD editable sketch axis native dependencies changed")
    IsRevolution = Actual.type_id == "Part::Revolution"
    IsGroup = Actual.type_id == "App::DocumentObjectGroup"
    CheckObjFields(
        Actual,
        Expected,
        Mutable=KLiveRevFields if IsRevolution else frozenset(),
        Optional=KGroupOptional if IsGroup else frozenset(),
    )
    CheckObjState(Actual, Expected)
    if IsGroup or IsRevolution:
        CheckEditFrame(Actual, "Placement", KTransformIdentity, Optional=True)
