# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from collections.abc import Callable, Mapping
from dataclasses import replace as Replace
from math import hypot as Hypot, isfinite as IsFinite

from convert.formats.Fusion.BodyBlob import KHistoryPrefix
from convert.formats.Fusion.Extrudes.SolidCreators import IsSavedActive
from convert.formats.Fusion.ParamProjection import ParamOrigin
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.Revolves.EdgeAxis.EdgeAxisSeed import (
    BuildEdgeSeed,
    CheckEdgeHist,
)
from convert.formats.Fusion.SelectionProxy import ReadSelectDesc, SelectCursor
from convert.formats.Fusion.Topology.BodyAsmMap import ReadBodyAsmRef
from convert.formats.Fusion.Topology.LineContext import ReadLineCtx
from convert.formats.Fusion.Topology.PickDescriptor import ReadTopoPick
from convert.formats.Fusion.Topology.RecipeRead import KRecipeGuid, ReadRecipe
from convert.formats.Fusion.Topology.SolidEdge import ResolveSolidEdge
from interchange.core.Common import FreezeMapping
from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.Selection import SelectPathElem, Selection
from interchange.geometry.models.Sketch import Sketch
from interchange.geometry.models.SupportPlane import SupportPlane
from interchange.geometry.models.VectorSpace import SpaceVector
from interchange.records.RecordParameter import Parameter
from interchange.records.RecordProvenance import ProvenanceSpan


# native recipe identity precedes the separate geometric and neutral edge witnesses
def ReadEdgeAxis(
    BulkData: bytes,
    Owners: dict[int, RecordSpan],
    StepValue: FeatureStep,
    FeatureLinks: dict[int, FeatureStep],
    Frames: dict[str, SupportPlane],
    Sketches: dict[str, Sketch],
    Params: dict[str, Parameter],
    LoadBody: Callable[[str], bytes],
) -> tuple[Selection, SpaceVector, SpaceVector]:
    Origin = StepValue.provenance
    Attrs = StepValue.attributes
    Evidence = Attrs.get("fusion.revolve.axis_edge_source")
    SelectId = Attrs.get("fusion.revolve.axis_selection_id")
    if Origin is None or type(SelectId) is not int or not isinstance(Evidence, Mapping):
        raise ValueError("Missing Fusion Revolve body edge selection evidence")
    BodyId = Evidence.get("native_body_id")
    SourceId = Evidence.get("native_source_feature_id")
    if type(BodyId) is not int or type(SourceId) is not int:
        raise ValueError("Missing Fusion Revolve body edge creator identity")
    Creator = FeatureLinks.get(SourceId)
    Source = None if Creator is None else Sketches.get(Creator.sketch_id or "")
    Profile = Sketches.get(StepValue.sketch_id or "")
    Frame = None if Source is None else Frames.get(Source.support_plane_id)
    ProfileFrame = None if Profile is None else Frames.get(Profile.support_plane_id)
    if Creator is None or Source is None or Frame is None or ProfileFrame is None:
        raise ValueError("Missing Fusion Revolve body edge source sketches or frames")
    Inputs = tuple(
        Value
        for Value in FeatureLinks.values()
        if Value.id in Creator.input_feature_ids
    )
    if (
        len(Inputs) != 1
        or Inputs[0].sketch_id != Source.id
        or Inputs[0].order >= Creator.order
        or not IsSavedActive(Inputs[0])
        or Source.suppressed
    ):
        raise ValueError("Fusion Revolve edge source sketch history is unresolved")
    Component = Frame.attributes.get("fusion.component_object_id")
    if type(Component) is not int or Component != ProfileFrame.attributes.get(
        "fusion.component_object_id"
    ):
        raise ValueError("Fusion Revolve edge and profile components disagree")
    CheckEdgeHist(StepValue, Creator, FeatureLinks)
    ResultId, Model, Entities = BuildEdgeSeed(
        BulkData, Owners, Creator, SourceId, BodyId, Source, Frame, Params
    )
    Asset = ReadBodyAsmRef(BulkData, Owners, BodyId, Component)
    Blob = LoadBody(Asset.FileName)
    FeatureId = int(Origin.native_id)
    Descriptor = ReadSelectDesc(BulkData, Owners, SelectId, FeatureId)
    PickValue = ReadTopoPick(BulkData, Owners, Descriptor, FeatureId)
    Recipe = SelectCursor(BulkData, Owners, PickValue.RecipeId, KRecipeGuid)
    RecipeKind, Terms, Payload = ReadRecipe(Recipe)
    if RecipeKind != "edge_recipe_data":
        raise ValueError("Fusion Revolve axis is missing a native edge recipe")
    Start, EndValue = ReadLineCtx(BulkData, Owners, PickValue.ContextId)
    CachedStart = SpaceVector(*(Value * 10.0 for Value in Start))
    CachedEnd = SpaceVector(*(Value * 10.0 for Value in EndValue))
    EdgeId, AxisStart, AxisEnd = ResolveSolidEdge(
        Blob,
        Asset.Handle,
        Terms,
        Payload,
        Model,
        CachedStart,
        CachedEnd,
        Entities,
        Asset.Handles,
    )
    Delta = (AxisEnd.x - AxisStart.x, AxisEnd.y - AxisStart.y, AxisEnd.z - AxisStart.z)
    Length = Hypot(*Delta)
    if not IsFinite(Length) or Length <= 1e-9:
        raise ValueError("Fusion Revolve edge geometry is degenerate")
    SelectOrigin = ParamOrigin(Owners[SelectId])
    EvidenceIds = (
        Descriptor,
        PickValue.RecipeId,
        PickValue.ContextId,
        PickValue.AnchorId,
        PickValue.HelperId,
        PickValue.SupportId,
        BodyId,
        SourceId,
        Asset.RecordId,
    )
    Spans = tuple(ParamOrigin(Owners[Identity]).spans[0] for Identity in EvidenceIds)
    BlobSpan = ProvenanceSpan(
        KHistoryPrefix + Asset.FileName, 0, len(Blob), "asm_history"
    )
    SelectionValue = Selection(
        id=f"fusion-selection-{SelectId}-axis",
        name="axis",
        path=(SelectPathElem("body", ResultId), SelectPathElem("edge", EdgeId)),
        query=FreezeMapping({"kind": "body_edge"}),
        provenance=Replace(SelectOrigin, spans=(*SelectOrigin.spans, *Spans, BlobSpan)),
        attributes=FreezeMapping({**Evidence, "asm_body_handle": Asset.Handle}),
    )
    return SelectionValue, AxisStart, SpaceVector(*(Value / Length for Value in Delta))
