# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import dataclass as MakeDataClass
from math import hypot as Hypot

from convert.formats.Fusion.Extrudes.SolidCreators import IsSavedActive
from convert.formats.Fusion.Scales.ConstructionCenter import KWorkPointStep
from convert.formats.Fusion.SelectionRef import KSelectDesc
from convert.formats.Fusion.Sketches.SketchPlacement import KSketchFeature
from convert.geometry.Extrude.Polygon.PrismFrame import CheckPrismFrame, PlacePrismPoint
from interchange.brep.topology.BrepMath import IsFiniteSpace
from interchange.document.models.DocumentModel import CadDocument
from interchange.features.FeatureBoundScale import BoundScale
from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.GeometryCurves import PointGeometry
from interchange.geometry.models.Selection import SelectPathElem, Selection
from interchange.geometry.models.Transform import KOriginZero
from interchange.geometry.models.VectorSpace import SpaceVector


# native scaling needs a point source that can continue driving the target after edits
@MakeDataClass(frozen=True, slots=True)
class ScalePointPlan:
    SketchId: str
    PointId: str
    FeatureId: str
    Point: SpaceVector


# the selected point and every selected body must refer to the same native component
def ReadPointScope(
    DocValue: CadDocument, Feature: FeatureStep, Center: Selection
) -> int:
    Definition = Feature.definition
    Origin = Center.provenance
    ComponentId = Center.query.get("native_component_id")
    if (
        not isinstance(Definition, BoundScale)
        or Definition.CenterSelectionId != Center.id
        or Center.id not in Feature.selection_ids
        or Center not in DocValue.selections
        or Origin is None
        or Origin.adapter != "fusion.f3d"
        or tuple(Span.record_kind for Span in Origin.spans) != (KSelectDesc,)
        or type(ComponentId) is not int
        or ComponentId <= 0
    ):
        raise ValueError("FreeCAD editable Scale center selection is unresolved")
    BySelection = {Value.id: Value for Value in DocValue.selections}
    for Identity in Definition.BodySelectionIds:
        BodyPick = BySelection.get(Identity)
        if (
            BodyPick is None
            or BodyPick.query.get("kind") != "historical_body"
            or BodyPick.query.get("native_component_id") != ComponentId
        ):
            raise ValueError("FreeCAD editable Scale center component disagrees")
    return ComponentId


# typed timeline owners distinguish authored references from similarly named features
def IsPointOwner(StepValue: FeatureStep, ClassGuid: str) -> bool:
    Origin = StepValue.provenance
    return (
        Origin is not None
        and Origin.adapter == "fusion.f3d"
        and bool(Origin.spans)
        and Origin.spans[0].record_kind == ClassGuid
    )


# the source sketch and datum must precede the scale that consumes their selected point
def ReadPointPlan(
    DocValue: CadDocument,
    Feature: FeatureStep,
    ComponentId: int,
    SketchId: str,
    PointId: str,
    FeatureId: str,
) -> ScalePointPlan:
    (SketchValue,) = tuple(Value for Value in DocValue.sketches if Value.id == SketchId)
    (Frame,) = tuple(
        Value
        for Value in DocValue.support_planes
        if Value.id == SketchValue.support_plane_id
        and Value.attributes.get("fusion.component_object_id") == ComponentId
        and Value.attributes.get("fusion.coordinate_space") == "component"
    )
    (Entity,) = tuple(Value for Value in SketchValue.entities if Value.id == PointId)
    (SketchStep,) = tuple(
        Value
        for Value in DocValue.feature_timeline
        if Value.sketch_id == SketchId and IsPointOwner(Value, KSketchFeature)
    )
    OwnerStep = Feature
    if FeatureId:
        (OwnerStep,) = tuple(
            Value for Value in DocValue.feature_timeline if Value.id == FeatureId
        )
        if (
            not IsPointOwner(OwnerStep, KWorkPointStep)
            or OwnerStep.order >= Feature.order
            or not IsSavedActive(OwnerStep)
        ):
            raise ValueError("FreeCAD editable Scale ByPoint feature is unresolved")
    if (
        SketchValue.suppressed
        or SketchStep.order >= OwnerStep.order
        or not IsSavedActive(SketchStep)
        or not isinstance(Entity.geometry, PointGeometry)
    ):
        raise ValueError("FreeCAD editable Scale center needs a preceding sketch point")
    CheckPrismFrame(Frame.transform)
    Point = PlacePrismPoint(Frame.transform, Entity.geometry.point, 0.0)
    return ScalePointPlan(SketchId, PointId, FeatureId, Point)


# the point used by the native solver must corroborate the source selection coordinates
def ReadScalePoint(
    DocValue: CadDocument, Feature: FeatureStep, Center: Selection
) -> ScalePointPlan:
    ComponentId = ReadPointScope(DocValue, Feature, Center)
    Point = Center.point
    Query = Center.query
    KindValue = Query.get("kind")
    NativePoint = Query.get("native_point_id")
    if Point is None or not IsFiniteSpace(Point):
        raise ValueError("FreeCAD editable Scale center is not finite")
    if KindValue == "component_origin_point":
        if (
            Center.path
            or type(NativePoint) is not int
            or NativePoint <= 0
            or Point != KOriginZero
        ):
            raise ValueError("FreeCAD editable Scale component origin disagrees")
        return ScalePointPlan("", "", "", Point)
    if KindValue == "sketch_point" and len(Center.path) == 2:
        SketchPath, PointPath = Center.path
        SketchId, PointId = SketchPath.entity_id, PointPath.entity_id
        FeatureId = ""
        if Center.path != (
            SelectPathElem("sketch", SketchId),
            SelectPathElem("sketch_entity", PointId),
        ):
            raise ValueError("FreeCAD editable Scale center sketch path disagrees")
    elif (
        KindValue == "construction_point"
        and not Center.path
        and type(NativePoint) is int
        and NativePoint > 0
    ):
        SketchId = Query.get("support_sketch_id")
        PointId = Query.get("support_point_id")
        FeatureId = Query.get("source_feature_id")
        if not isinstance(FeatureId, str) or not FeatureId:
            raise ValueError("FreeCAD editable Scale ByPoint owner is missing")
    else:
        raise ValueError("Unsupported FreeCAD editable Scale center")
    if (
        not isinstance(SketchId, str)
        or not SketchId
        or not isinstance(PointId, str)
        or not PointId
    ):
        raise ValueError("FreeCAD editable Scale center sketch or point is missing")
    Plan = ReadPointPlan(DocValue, Feature, ComponentId, SketchId, PointId, FeatureId)
    Derived = Plan.Point
    if (
        not IsFiniteSpace(Derived)
        or Hypot(Point.x - Derived.x, Point.y - Derived.y, Point.z - Derived.z) > 1e-8
    ):
        raise ValueError("FreeCAD editable Scale center coordinates disagree")
    return Plan
