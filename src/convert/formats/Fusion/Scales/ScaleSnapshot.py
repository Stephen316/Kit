# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from collections.abc import Callable
from dataclasses import replace as Replace

from convert.formats.Fusion.BodyInputs.InputContext import ReadInputScope
from convert.formats.Fusion.BodyInputs.ScaleControls import ReadScaleData
from convert.formats.Fusion.HistoryPart import HistoryPart
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.Scales.ScaleBodies import ReadScaleBodies
from convert.formats.Fusion.Scales.ScaleCenter import ReadScaleCenter
from convert.formats.Fusion.Scales.ScaleFactorIds import ReadScaleParams
from convert.formats.Fusion.Topology.BodyEvidence import (
    GetBodyEvidence,
    KBodyInventoryKey,
    LinkBodyRecords,
)
from convert.formats.Fusion.Topology.BodyInventory import ReadBodyInventory
from interchange.core.Common import FreezeMapping
from interchange.document.models.DocumentModel import CadDocument
from interchange.enums.EnumDocument import Capability
from interchange.features.BoundScaleValues import GetScaleValues
from interchange.features.FeatureBoundScale import BoundScale
from interchange.features.FeatureStep import FeatureStep


# only a complete terminal scale replaces the saved final body set
def ReadScaleSnap(
    Document: CadDocument,
    BulkData: bytes,
    Spans: tuple[RecordSpan, ...],
    History: HistoryPart,
    Feature: FeatureStep,
    FeatureId: int,
    LoadBlob: Callable[[str], bytes],
) -> CadDocument:
    Context = ReadInputScope(BulkData, Spans, History, Document.feature_timeline)
    Scope = Context.Scopes.get(FeatureId)
    if (
        Scope is None
        or Scope.ComponentId != Context.ComponentId
        or Scope.SnapshotId is not None
    ):
        raise ValueError("Fusion Scale requires its own local history scope")
    Inventory, Issues = ReadBodyInventory(
        BulkData, Spans, frozenset((Context.ComponentId,))
    )
    Members = Inventory.get(Context.ComponentId)
    if Members is None:
        raise ValueError(
            Issues.get(Context.ComponentId, "Fusion Scale body inventory is missing")
        )
    Fields = ReadScaleData(BulkData, Context.Owners, FeatureId)
    Center = ReadScaleCenter(
        BulkData, Context, Document, Feature, Scope, FeatureId, Fields.CenterId
    )
    Definition = BoundScale(
        ReadScaleParams(Document, Feature, FeatureId, Fields),
        Center.id,
        Feature.selection_ids,
    )
    Updated = Replace(
        Feature,
        definition=Definition,
        selection_ids=(*Feature.selection_ids, Center.id),
    )
    Selections = (*Document.selections, Center)
    Factors, Point = GetScaleValues(
        Updated,
        Definition,
        {Value.id: Value for Value in Document.parameters},
        {Value.id: Value for Value in Selections},
    )
    Bodies, Model = ReadScaleBodies(
        Document,
        BulkData,
        Context,
        Feature,
        FeatureId,
        Members,
        Factors,
        Point,
        LoadBlob,
    )
    Bodies, Links = LinkBodyRecords(Bodies, Members)
    return Replace(
        Document,
        feature_timeline=(*Document.feature_timeline[:-1], Updated),
        selections=Selections,
        bodies=Bodies,
        brep=Model,
        capabilities=Document.capabilities
        | {Capability.KBodyStructure, Capability.KBrep},
        diagnostics=tuple(
            Value
            for Value in Document.diagnostics
            if Value.code != "fusion.extrude.body_unsupported"
        ),
        metadata=FreezeMapping(
            {
                **Document.metadata,
                KBodyInventoryKey: GetBodyEvidence(Context.ComponentId, Members, Links),
            }
        ),
    )
