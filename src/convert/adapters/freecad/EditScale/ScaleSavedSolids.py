# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from collections.abc import Mapping
from dataclasses import replace as Replace
from math import isclose as IsClose

from convert.adapters.freecad.EditBodyRev.BodyRevModels import GetBodyTopology
from convert.adapters.freecad.EditRead.EditExtrusion import ReadEditDepth
from convert.adapters.freecad.EditRead.EditPlacement import CheckEditFrame
from convert.adapters.freecad.EditRead.XmlField import EditChild, EditFloat, EditScalar
from convert.adapters.freecad.EditScale.ScaleExpressions import ScaleOffset
from convert.adapters.freecad.EditScale.ScaleWritePlan import ScaleWritePlan
from convert.adapters.freecad.EditShape.PrismShape import IsEditPrism
from convert.adapters.freecad.EditShape.ScalePrismShape import IsScalePrism
from convert.adapters.freecad.Native import NativeObject
from convert.formats.Fusion.Revolves.JoinRevModels import JoinRevModels
from convert.formats.Fusion.Scales.ScaleSeed import ReadScaleSeed
from convert.geometry.Extrude.Polygon.PrismRing import ReadPrismRing
from convert.geometry.Scale.ScalePrism import BuildScalePrism
from interchange.document.models.DocumentModel import CadDocument
from interchange.features.FeatureBoundScale import BoundScale
from interchange.geometry.models.Transform import Transform
from interchange.geometry.models.VectorSpace import SpaceVector


# matching the evaluated factor prevents accepting a stale spreadsheet dependency
def CheckResultFactors(
    Native: NativeObject, Uniform: bool, Factors: SpaceVector
) -> None:
    Controls = (
        (("UniformScale", Factors.x),)
        if Uniform
        else (("XScale", Factors.x), ("YScale", Factors.y), ("ZScale", Factors.z))
    )
    for Name, Value in Controls:
        Saved = EditFloat(
            EditChild(Native, Name, "App::PropertyFloat", "Float"), "value"
        )
        if not IsClose(Saved, Value, rel_tol=1e-12, abs_tol=0.0):
            raise ValueError(
                "FreeCAD editable Scale cached factor disagrees with its cell"
            )


# exact ids correlate each independently witnessed native cache to its ordered source body
def RebuildScaleSolids(
    Document: CadDocument,
    Plan: ScaleWritePlan,
    Definition: BoundScale,
    Objects: Mapping[str, NativeObject],
    Shapes: Mapping[str, bytes],
    Factors: SpaceVector,
    Center: SpaceVector,
) -> CadDocument:
    Steps = {Value.id: Value for Value in Document.feature_timeline}
    Selections = {Value.id: Value for Value in Document.selections}
    Sources = {
        EditScalar(Value, "KitId", "App::PropertyString", "String"): Value
        for Value in Objects.values()
        if Value.type_id == "Part::Extrusion"
    }
    Results = {
        EditScalar(Value, "KitBodyId", "App::PropertyString", "String"): Value
        for Value in Objects.values()
        if Value.type_id == "Part::Scale"
    }
    Shift = ScaleOffset(Center, Factors)
    Bodies, Models = [], []
    for Body, BodyPlan, PickId in zip(
        Document.bodies, Plan.Bodies, Definition.BodySelectionIds, strict=True
    ):
        Seed = ReadScaleSeed(
            Document,
            Steps[BodyPlan.SourceId],
            Selections[PickId].query["native_component_id"],
        )
        Source, Result = Sources[BodyPlan.SourceId], Results[Body.id]
        Depth = ReadEditDepth(Source, Seed.Frame.z_axis)
        if not IsClose(
            Depth, Seed.Depth, rel_tol=1e-12, abs_tol=0.0
        ) or not IsEditPrism(
            Shapes.get(Source.name, b""),
            Seed.Frame,
            ReadPrismRing(Seed.Profile),
            Seed.Depth,
        ):
            raise ValueError(
                "FreeCAD editable Scale source solid disagrees with its profile or depth"
            )
        CheckResultFactors(Result, len(Plan.FactorIds) == 1, Factors)
        CheckEditFrame(Result, "Placement", Transform(origin=Shift))
        Geometry = BuildScalePrism(
            Body.id, Seed.Profile, Seed.Frame, Seed.Depth, Factors, Center
        )
        if not IsScalePrism(Shapes.get(Result.name, b""), Geometry[0], Shift):
            raise ValueError(
                "FreeCAD editable Scale result solid disagrees with its live controls"
            )
        Bodies.append(Replace(Body, topology=GetBodyTopology(Geometry)))
        Models.append(Geometry[0])
    return Replace(Document, bodies=tuple(Bodies), brep=JoinRevModels(tuple(Models)))
