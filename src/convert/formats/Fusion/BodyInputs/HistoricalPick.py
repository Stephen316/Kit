# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.formats.Fusion.Assembly.Solids.CreatorScopes import CreatorScope
from convert.formats.Fusion.BodyInputs.BodyInput import BodyInput
from convert.formats.Fusion.BodyInputs.InputContext import InputContext
from convert.formats.Fusion.BodyInputs.SourceBody import CheckBodySource
from convert.formats.Fusion.ParamProjection import ParamOrigin
from convert.formats.Fusion.Topology.BodyPick import ReadBodyPick
from convert.formats.Fusion.Topology.BodyPickContext import CheckBodyCtx
from interchange.core.Common import FreezeMapping
from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.Selection import Selection


# ordered queries preserve consumed inputs without requiring a current body path
def MakeHistoryPick(
    BulkData: bytes,
    Context: InputContext,
    Receiver: FeatureStep,
    FeatureId: int,
    Scope: CreatorScope,
    Input: BodyInput,
    Ordinal: int,
) -> Selection:
    Pick = ReadBodyPick(BulkData, Context.Owners, Input.DescriptorId, FeatureId)
    if (Input.Role == "tool" and len(Pick.ContextIds) != 1) or (
        Input.Role != "tool" and Pick.ContextIds
    ):
        raise ValueError("Unsupported Fusion body input context for role")
    if Input.AssociationId is not None:
        CheckBodyCtx(
            BulkData,
            Context.Owners,
            Input.AssociationId,
            Pick.Namespace,
            Pick.EntityGuid,
            Pick.AnchorId,
        )
    Source = CheckBodySource(BulkData, Context, Receiver, Scope, Pick)
    return Selection(
        id=f"fusion-body-pick-{Context.HistoryId}-{FeatureId}-{Pick.DescriptorId}",
        name=f"Historical body {Pick.BodyId}",
        path=(),
        query=FreezeMapping(
            {
                "kind": "historical_body",
                "role": Input.Role,
                "ordinal": Ordinal,
                "native_body_id": Pick.BodyId,
                "native_anchor_id": Pick.AnchorId,
                "native_source_id": Pick.SourceId,
                "source_feature_id": Source.id,
                "native_component_id": Scope.ComponentId,
                "native_scope_id": Scope.ScopeId,
                "native_history_id": Context.HistoryId,
            }
        ),
        provenance=ParamOrigin(Context.Owners[Pick.DescriptorId]),
        attributes=FreezeMapping(
            {
                "fusion.proxy_object_id": Input.ProxyId,
                "fusion.descriptor_object_id": Pick.DescriptorId,
                "fusion.association_object_id": Input.AssociationId,
                "fusion.support_object_id": Pick.SupportId,
                "fusion.recipe_object_id": Pick.RecipeId,
                "fusion.context_object_ids": Pick.ContextIds,
                "fusion.anchor_guid": Pick.AnchorGuid,
            }
        ),
    )
