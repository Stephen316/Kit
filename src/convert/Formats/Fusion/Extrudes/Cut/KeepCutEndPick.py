from dataclasses import replace as Replace

from convert.Formats.Fusion.ParamProjection import ParamOrigin
from convert.Formats.Fusion.RecordSpan import RecordSpan
from convert.Formats.Fusion.Topology.BodyPick import BodyPick
from interchange.Core.Common import FreezeMapping
from interchange.geometry.Models.Selection import Selection


# the distinct extent role preserves the original selector without declaring an up to limit
def KeepCutEndPick(
    Owners: dict[int, RecordSpan], Target: Selection, PickValue: BodyPick, ProxyId: int
) -> Selection:
    DescriptorId = PickValue.DescriptorId
    Origin = ParamOrigin(Owners[DescriptorId])
    Records = (
        ProxyId,
        PickValue.HelperId,
        PickValue.SupportId,
        PickValue.RecipeId,
        PickValue.AnchorId,
        *PickValue.ContextIds,
    )
    return Selection(
        id=f"{Target.id}-extent-{DescriptorId}",
        name=f"Historical extent reference {PickValue.BodyId}",
        path=(),
        query=FreezeMapping({**Target.query, "role": "extent_reference"}),
        attributes=FreezeMapping(
            {
                "fusion.proxy_object_id": ProxyId,
                "fusion.descriptor_object_id": DescriptorId,
                "fusion.support_object_id": PickValue.SupportId,
                "fusion.recipe_object_id": PickValue.RecipeId,
                "fusion.context_object_ids": PickValue.ContextIds,
                "fusion.anchor_guid": PickValue.AnchorGuid,
            }
        ),
        provenance=Replace(
            Origin,
            spans=Origin.spans
            + tuple(ParamOrigin(Owners[Identity]).spans[0] for Identity in Records),
        ),
    )
