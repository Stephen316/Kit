from dataclasses import dataclass as MakeDataClass

from typing import cast as CastValue

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
from interchange.brep.topology.BrepModel import BrepModel
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
        CastValue(object, Document.source) is None
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
    SketchIds: set[str] = set()
    Sources: set[str] = set()
    BodyPlans: list[ScaleBodyPlan] = []
    Models: list[BrepModel] = []
    for BodyValue, Identity in zip(
        Document.bodies, Definition.BodySelectionIds, strict=True
    ):
        PickValue = Picks[Identity]
        SourceId = PickValue.query.get("source_feature_id")
        if (
            not isinstance(SourceId, str)
            or SourceId not in Steps
            or SourceId in Sources
        ):
            raise ValueError("FreeCAD Scale input source is missing or repeated")
        PlanValue, Model = ReadScaleBody(
            Document, Feature, Steps[SourceId], BodyValue, PickValue, Factors, Center
        )
        Sources.add(SourceId)
        SketchIds.add(PlanValue.SketchId)
        BodyPlans.append(PlanValue)
        Models.append(Model)
    CheckStepsMut(Feature, Point, Steps, Sources, SketchIds, Models, Document)
    return ScaleWritePlan(
        Feature.id, Definition.FactorParameterIds, Factors, Point, tuple(BodyPlans)
    )


# native timeline ownership and the rebuilt solid must agree before emission
def CheckStepsMut(
    Feature: FeatureStep,
    Point: ScalePointPlan,
    Steps: dict[str, FeatureStep],
    Sources: set[str],
    SketchIds: set[str],
    Models: list[BrepModel],
    Document: CadDocument,
) -> None:
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


# unrelated feature families retain the normal archive strategy
def GetScalePlan(Document: CadDocument) -> ScaleWritePlan | None:
    if Document.source.format_id != "fusion.f3d" or not Document.feature_timeline:
        return None
    Feature = Document.feature_timeline[-1]
    if not isinstance(Feature.definition, BoundScale):
        return None
    return ReadScalePlan(Document, Feature, Feature.definition)
