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
    PickValue = ReadBodyPick(BulkData, Context.Owners, Input.DescriptorId, FeatureId)
    if (Input.Role == "tool" and len(PickValue.ContextIds) != 1) or (
        Input.Role != "tool" and PickValue.ContextIds
    ):
        raise ValueError("Unsupported Fusion body input context for role")
    if Input.AssociationId is not None:
        CheckBodyCtx(
            BulkData,
            Context.Owners,
            Input.AssociationId,
            PickValue.Namespace,
            PickValue.EntityGuid,
            PickValue.AnchorId,
        )
    Source = CheckBodySource(BulkData, Context, Receiver, Scope, PickValue)
    return Selection(
        id=f"fusion-body-pick-{Context.HistoryId}-{FeatureId}-{PickValue.DescriptorId}",
        name=f"Historical body {PickValue.BodyId}",
        path=(),
        query=FreezeMapping(
            {
                "kind": "historical_body",
                "role": Input.Role,
                "ordinal": Ordinal,
                "native_body_id": PickValue.BodyId,
                "native_anchor_id": PickValue.AnchorId,
                "native_source_id": PickValue.SourceId,
                "source_feature_id": Source.id,
                "native_component_id": Scope.ComponentId,
                "native_scope_id": Scope.ScopeId,
                "native_history_id": Context.HistoryId,
            }
        ),
        provenance=ParamOrigin(Context.Owners[PickValue.DescriptorId]),
        attributes=FreezeMapping(
            {
                "fusion.proxy_object_id": Input.ProxyId,
                "fusion.descriptor_object_id": PickValue.DescriptorId,
                "fusion.association_object_id": Input.AssociationId,
                "fusion.support_object_id": PickValue.SupportId,
                "fusion.recipe_object_id": PickValue.RecipeId,
                "fusion.context_object_ids": PickValue.ContextIds,
                "fusion.anchor_guid": PickValue.AnchorGuid,
            }
        ),
    )
