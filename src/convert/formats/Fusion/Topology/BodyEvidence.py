from collections.abc import Mapping
from dataclasses import replace as Replace

from convert.formats.Fusion.Topology.NativeBody import NativeBody
from interchange.core.Common import FreezeMapping
from interchange.features.FeatureBody import DesignBody

# native body inventory remains separate from final geometry and feature assertions
KBodyInventoryKey = "fusion.body_inventory"


# wire evidence distinguishes an empty saved name from an unqualified name field
def GetBodyEvidence(
    ComponentId: int,
    Members: tuple[NativeBody, ...],
    LinkedIds: Mapping[int, str],
) -> Mapping[str, object]:
    return FreezeMapping(
        {
            "component_id": ComponentId,
            "members": tuple(
                FreezeMapping(
                    {
                        "object_id": Member.ObjectId,
                        "collection_id": Member.CollectionId,
                        "stored_name": (
                            Member.Name if Member.NameHelperId is not None else None
                        ),
                        "name_helper_id": Member.NameHelperId,
                        "design_body_id": LinkedIds.get(Member.ObjectId),
                    }
                )
                for Member in Members
            ),
        }
    )


# a proven native match enriches the existing body without replacing its interchange identity
def LinkBodyRecords(
    Bodies: tuple[DesignBody, ...], Members: tuple[NativeBody, ...]
) -> tuple[tuple[DesignBody, ...], dict[int, str]]:
    ByIdentity = {str(Member.ObjectId): Member for Member in Members}
    Projected: list[DesignBody] = []
    LinkedIds: dict[int, str] = {}
    for BodyValue in Bodies:
        Member = (
            ByIdentity.get(BodyValue.provenance.native_id)
            if BodyValue.provenance
            else None
        )
        if (
            Member is not None
            and BodyValue.attributes.get("fusion.native_body_collection_id")
            == Member.CollectionId
        ):
            LinkedIds[Member.ObjectId] = BodyValue.id
            BodyValue = Replace(
                BodyValue,
                name=(
                    Member.Name
                    if Member.NameHelperId is not None and Member.Name
                    else BodyValue.name
                ),
                attributes=FreezeMapping(
                    {
                        **BodyValue.attributes,
                        "fusion.component_object_id": Member.ComponentId,
                    }
                ),
            )
        Projected.append(BodyValue)
    return tuple(Projected), LinkedIds
