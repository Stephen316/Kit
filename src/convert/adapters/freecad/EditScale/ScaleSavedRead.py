# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from collections.abc import Mapping
from dataclasses import replace as Replace
from xml.etree.ElementTree import Element
from zipfile import ZipFile, ZipInfo

from convert.adapters.freecad.Archive import Items, ParamCatalog
from convert.adapters.freecad.EditRead.EditPlacement import CheckEditFrame
from convert.adapters.freecad.EditRead.Sketch.SketchGraph import IndexSketchObjs
from convert.adapters.freecad.EditScale.ScalePointPlan import (
    ReadPointPlan,
    ReadPointScope,
)
from convert.adapters.freecad.EditScale.ScaleSavedGraph import CheckScaleGraph
from convert.adapters.freecad.EditScale.ScaleSavedParams import ReadScaleParams
from convert.adapters.freecad.EditScale.ScaleSavedShapes import ReadScaleShapes
from convert.adapters.freecad.EditScale.ScaleSavedSketch import ReadScaleRings
from convert.adapters.freecad.EditScale.ScaleSavedSolids import RebuildScale
from convert.adapters.freecad.EditScale.ScaleWritePlan import ScaleWritePlan
from convert.adapters.freecad.Native import NativeObject, ParseObjects
from interchange.document.models.DocumentModel import CadDocument
from interchange.features.BoundScaleValues import GetScaleValues
from interchange.features.FeatureBoundScale import BoundScale
from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.Selection import Selection
from interchange.geometry.models.Transform import Transform


# a scale point derives from the solved source sketch before its own placement is trusted
def ReadSavedCenter(
    Document: CadDocument,
    Feature: FeatureStep,
    PlanValue: ScaleWritePlan,
    Center: Selection,
    Objects: Mapping[str, NativeObject],
) -> Selection:
    Point = PlanValue.Center
    if not Point.SketchId:
        return Center
    Derived = ReadPointPlan(
        Document,
        Feature,
        ReadPointScope(Document, Feature, Center),
        Point.SketchId,
        Point.PointId,
        Point.FeatureId,
    ).Point
    (Native,) = tuple(
        Value for Value in Objects.values() if Value.type_id == "App::Point"
    )
    CheckEditFrame(Native, "Placement", Transform(origin=Derived))
    return Center if Derived == Point.Point else Replace(Center, point=Derived)


# native evidence is applied transactionally so stale source caches never escape on failure
def ReadSavedScale(
    Document: CadDocument,
    Manifest: Mapping[str, object],
    Feature: FeatureStep,
    Definition: BoundScale,
    PlanValue: ScaleWritePlan,
    Expected: Element,
    Actual: Element,
    Archive: ZipFile,
    Members: Mapping[str, ZipInfo],
) -> CadDocument:
    CheckScaleGraph(Expected, Actual)
    Objects = {Value.name: Value for Value in ParseObjects(Actual)}
    Originals = {Value.name: Value for Value in ParseObjects(Expected)}
    Catalog = ParamCatalog(Items(Manifest.get("parameters", [])))
    Editable = {
        *PlanValue.FactorIds,
        *(BodyValue.DepthId for BodyValue in PlanValue.Bodies),
    }
    Params = ReadScaleParams(
        Objects["Parameters"],
        Originals["Parameters"],
        Catalog,
        Document.parameters,
        Editable,
    )
    Shapes = ReadScaleShapes(Archive, Members, Objects)
    Updated = Replace(Document, parameters=Params)
    Sketches = ReadScaleRings(
        Updated, PlanValue, IndexSketchObjs(Objects.values()), Originals, Shapes
    )
    Updated = Replace(Updated, sketches=Sketches)
    CenterId = Definition.CenterSelectionId
    Selections = {Value.id: Value for Value in Document.selections}
    Selections[CenterId] = ReadSavedCenter(
        Updated, Feature, PlanValue, Selections[CenterId], Objects
    )
    Factors, Point = GetScaleValues(
        Feature, Definition, {Value.id: Value for Value in Params}, Selections
    )
    Final = RebuildScale(
        Replace(Updated, selections=tuple(Selections.values())),
        PlanValue,
        Definition,
        Objects,
        Shapes,
        Factors,
        Point,
    )
    return Document if Final == Document else Final
