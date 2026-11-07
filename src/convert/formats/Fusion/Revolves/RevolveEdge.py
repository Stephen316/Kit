# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.Revolves.RevolvePick import RevolvePick
from convert.formats.Fusion.SelectionProxy import SelectCursor
from convert.formats.Fusion.Topology.BodyAnchor import ReadBodyAnchor
from convert.formats.Fusion.Topology.LineContext import ReadLineCtx
from convert.formats.Fusion.Topology.PickDescriptor import ReadTopoPick
from convert.formats.Fusion.Topology.PickSupport import ReadPickSupport
from convert.formats.Fusion.Topology.RecipeRead import KRecipeGuid, ReadRecipe
from interchange.core.Common import FreezeMapping
from interchange.features.FeatureStep import FeatureStep


# an edge recipe and its cached line retain source evidence without claiming an edge id
def ResolveRevEdge(
    BulkData: bytes,
    Owners: dict[int, RecordSpan],
    Descriptor: int,
    FeatureId: int,
    FeatureOrder: int,
    FeatureLinks: dict[int, FeatureStep],
) -> RevolvePick:
    PickValue = ReadTopoPick(BulkData, Owners, Descriptor, FeatureId)
    Recipe = SelectCursor(BulkData, Owners, PickValue.RecipeId, KRecipeGuid)
    RecipeKind, Terms, Payload = ReadRecipe(Recipe)
    if (
        RecipeKind != "edge_recipe_data"
        or len(Payload) not in (116, 120)
        or Payload[-4:] not in (bytes(4), b"\xff" * 4)
    ):
        raise ValueError("Unsupported Fusion Revolve edge recipe")
    BodyId, SourceId = ReadBodyAnchor(BulkData, Owners, PickValue.AnchorId)
    ReadPickSupport(BulkData, Owners, PickValue.SupportId, Descriptor, SourceId)
    Source = FeatureLinks.get(SourceId)
    if Source is None or Source.order >= FeatureOrder:
        raise ValueError("Fusion Revolve edge source is outside prior history")
    Start, EndValue = ReadLineCtx(BulkData, Owners, PickValue.ContextId)
    return RevolvePick(
        None,
        Descriptor,
        PickValue.RecipeId,
        DependencyId=Source.id,
        RelatedIds=(
            PickValue.ContextId,
            PickValue.AnchorId,
            PickValue.HelperId,
            PickValue.SupportId,
            BodyId,
            SourceId,
        ),
        EdgeSource=FreezeMapping(
            {
                "native_body_id": BodyId,
                "native_source_feature_id": SourceId,
                "native_body_anchor_id": PickValue.AnchorId,
                "native_recipe_id": PickValue.RecipeId,
                "native_line_context_id": PickValue.ContextId,
                "native_namespace": PickValue.Namespace,
                "native_entity_guid": PickValue.EntityGuid,
                "recipe_terms": Terms,
                "cached_start_cm": Start,
                "cached_end_cm": EndValue,
            }
        ),
    )
