# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import dataclass as MakeDataClass

from convert.adapters.freecad.EditExtDepth import IsLiteralParam
from convert.adapters.freecad.EditScale.ScaleBodyPlan import ScaleBodyPlan
from convert.adapters.freecad.EditScale.ScalePointPlan import (
    ReadScalePoint,
    ScalePointPlan,
)
from convert.adapters.freecad.EditScale.ScaleSourcePlan import ReadScaleBody
from convert.formats.Fusion.Extrudes.SolidCreators import IsSavedActive
from convert.formats.Fusion.Revolves.JoinRevModels import JoinRevModels
from convert.formats.Fusion.Sketches.SketchPlacement import KSketchFeature
from interchange.document.models.DocumentModel import CadDocument
from interchange.features.BoundScaleValues import GetScaleValues
from interchange.features.FeatureBoundScale import BoundScale
from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.VectorSpace import SpaceVector


# a checked native scale plan owns the complete editable source tree and final body order
@MakeDataClass(frozen=True, slots=True)
class ScaleWritePlan:
    FeatureId: str
    FactorIds: tuple[str, ...]
    Factors: SpaceVector
    Center: ScalePointPlan
    Bodies: tuple[ScaleBodyPlan, ...]


# model qualification is separate from graph emission so partial scale objects cannot leak
def ReadScalePlan(
    Document: CadDocument, Feature: FeatureStep, Definition: BoundScale
) -> ScaleWritePlan:
    if (
        Document.source is None
        or Document.source.format_id != "fusion.f3d"
        or Document.assembly is not None
        or Document.brep is None
        or not IsSavedActive(Feature)
        or len(Definition.BodySelectionIds) != len(Document.bodies)
    ):
        raise ValueError("FreeCAD Scale requires a complete local Fusion result")
    Params = {Value.id: Value for Value in Document.parameters}
    Picks = {Value.id: Value for Value in Document.selections}
    Factors, Center = GetScaleValues(Feature, Definition, Params, Picks)
    if not all(
        IsLiteralParam(Params[Identity]) for Identity in Definition.FactorParameterIds
    ):
        raise ValueError("FreeCAD Scale requires literal writable factor controls")
    Point = ReadScalePoint(Document, Feature, Picks[Definition.CenterSelectionId])
    Steps = {Value.id: Value for Value in Document.feature_timeline}
    SketchIds = set()
    Sources = set()
    BodyPlans = []
    Models = []
    for Body, Identity in zip(
        Document.bodies, Definition.BodySelectionIds, strict=True
    ):
        Pick = Picks[Identity]
        SourceId = Pick.query.get("source_feature_id")
        if (
            not isinstance(SourceId, str)
            or SourceId not in Steps
            or SourceId in Sources
        ):
            raise ValueError("FreeCAD Scale input source is missing or repeated")
        Plan, Model = ReadScaleBody(
            Document, Feature, Steps[SourceId], Body, Pick, Factors, Center
        )
        Sources.add(SourceId)
        SketchIds.add(Plan.SketchId)
        BodyPlans.append(Plan)
        Models.append(Model)
    if Point.SketchId:
        SketchIds.add(Point.SketchId)
    SketchSteps = {
        Value.id: Value.sketch_id
        for Value in Steps.values()
        if Value.sketch_id in SketchIds
        and Value.id not in Sources
        and Value.provenance is not None
        and Value.provenance.spans
        and Value.provenance.spans[0].record_kind == KSketchFeature
        and IsSavedActive(Value)
    }
    if len(SketchSteps) != len(SketchIds) or set(SketchSteps.values()) != SketchIds:
        raise ValueError(
            "FreeCAD Scale needs one native timeline sketch for each profile or point"
        )
    Allowed = {Feature.id, *Sources, *SketchSteps}
    if Point.FeatureId:
        Allowed.add(Point.FeatureId)
    if Allowed != Steps.keys() or JoinRevModels(tuple(Models)) != Document.brep:
        raise ValueError("FreeCAD Scale source timeline or final solid model disagrees")
    return ScaleWritePlan(
        Feature.id, Definition.FactorParameterIds, Factors, Point, tuple(BodyPlans)
    )


# unrelated feature families retain the normal archive strategy
def GetScalePlan(Document: CadDocument) -> ScaleWritePlan | None:
    if not Document.feature_timeline:
        return None
    Feature = Document.feature_timeline[-1]
    if not isinstance(Feature.definition, BoundScale):
        return None
    try:
        return ReadScalePlan(Document, Feature, Feature.definition)
    except ValueError:
        return None
