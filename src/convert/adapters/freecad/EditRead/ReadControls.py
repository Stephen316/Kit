# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import dataclass as MakeDataClass
from xml.etree.ElementTree import Element

from convert.adapters.freecad.EditableExt import EditExtrude
from convert.adapters.freecad.EditRead.EditExtrusion import (
    ReadEditDepth,
    ReadShapeEntry,
)
from convert.adapters.freecad.EditRead.EditObjects import FindEditObject, RequireEditObj
from convert.adapters.freecad.EditRead.EditProfile import CheckEditProf
from convert.adapters.freecad.EditRead.EditSheet import ReadEditText
from convert.adapters.freecad.EditRead.XmlField import EditScalar
from convert.adapters.freecad.Native import ParseObjects
from interchange.document.models.DocumentModel import CadDocument
from interchange.features.FeatureDistExt import DistanceExtrude


# live control evidence travels with the exact sidecar needed for independent shape proof
@MakeDataClass(frozen=True, slots=True)
class EditFields:
    DistanceMm: float
    ShapeEntry: str
    SourceText: str


# reconciling a depth requires an unchanged linked profile and corroborated native controls
def ReadEditFields(
    RootValue: Element, DocValue: CadDocument, PlanValue: EditExtrude
) -> EditFields | None:
    if (
        not DocValue.feature_timeline
        or len(DocValue.sketches) != 1
        or len(DocValue.support_planes) != 1
        or len(DocValue.bodies) != 1
    ):
        raise ValueError(
            "FreeCAD editable extrusion snapshot has an invalid document scope"
        )
    StepValue = DocValue.feature_timeline[-1]
    Definition = StepValue.definition
    SketchValue = DocValue.sketches[0]
    PlaneValue = DocValue.support_planes[0]
    BodyValue = DocValue.bodies[0]
    if (
        not isinstance(Definition, DistanceExtrude)
        or Definition.AlongParameterId != PlanValue.ParameterId
        or Definition.Direction != PlanValue.Direction
        or SketchValue.id != PlanValue.SketchId
        or BodyValue.final_feature_id != StepValue.id
    ):
        raise ValueError(
            "FreeCAD editable extrusion plan disagrees with the embedded document"
        )
    Objects = ParseObjects(RootValue)
    Feature = FindEditObject(Objects, StepValue.id)
    if Feature is None or Feature.type_id == "Part::Feature":
        return None
    if Feature.type_id != "Part::Extrusion":
        raise ValueError("FreeCAD editable extrusion object has the wrong native type")
    BodyObj = RequireEditObj(Objects, BodyValue.id, "App::DocumentObjectGroup")
    if EditScalar(BodyObj, "Tip", "App::PropertyLink", "Link") != Feature.name:
        raise ValueError("FreeCAD editable extrusion body tip changed")
    CheckEditProf(Objects, Feature, SketchValue, PlaneValue)
    DepthMm = ReadEditDepth(Feature, PlanValue.Direction)
    SourceText = ReadEditText(Objects, Feature, DocValue, Definition, DepthMm)
    return EditFields(DepthMm, ReadShapeEntry(Feature), SourceText)
