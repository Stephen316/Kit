from convert.adapters.solidworks.Container.Format import KPartFormatId
from convert.adapters.solidworks.Core.Partition.ScopedPartition import ScopedRegion
from convert.adapters.solidworks.Resolved.Cut.ScopeTypes import ScopeBody, ScopeOwner
from interchange.Core.Common import FreezeMapping
from interchange.Features.FeatureBody import DesignBody
from interchange.Payloads.PayloadRecord import BrepPayload
from interchange.Records.RecordProvenance import Provenance, ProvenanceSpan


# resolved span offsets and partition wrapper provenance refer to different native streams
def GetScopeSpans(
    Payload: BrepPayload, ConfigId: int, BodyRecord: ScopeBody | None
) -> tuple[ProvenanceSpan, ...]:
    Spans = Payload.provenance.spans if Payload.provenance is not None else ()
    if BodyRecord is None:
        return Spans
    Offset = BodyRecord["offset"]
    return (
        ProvenanceSpan(
            f"Contents/Config-{ConfigId}-ResolvedFeatures",
            Offset,
            BodyRecord["end"] - Offset,
            "resolved-cut-scope-body",
        ),
        *Spans,
    )


# the design identity belongs to its original producer while the final feature can change
def MakeScopeBody(
    ConfigId: int,
    Payload: BrepPayload,
    Region: ScopedRegion,
    Owner: ScopeOwner,
    BodyRecord: ScopeBody | None,
    CutId: int,
) -> DesignBody:
    FinalId = Owner.FeatureId if BodyRecord is None else CutId
    return DesignBody(
        id=Region.BodyValue.design_body_id,
        name=f"Body {Owner.BodyId}",
        final_feature_id=f"sldprt:feature:{FinalId}",
        topology=Region.Topology,
        provenance=Provenance(
            adapter=KPartFormatId,
            native_id=str(Owner.BodyId),
            spans=GetScopeSpans(Payload, ConfigId, BodyRecord),
        ),
        attributes=FreezeMapping(
            {
                "native_body_id": Owner.BodyId,
                "native_producer_feature_id": Owner.FeatureId,
                "native_producer_transfer_object": Owner.TransferObject,
                "native_recent_atom_id": Region.RecentAtomId,
                "native_partition_owner": Region.NativeOwner,
                "native_partition_region": Region.NativeRegion,
                "parasolid_active_payload_id": Payload.id,
                "solidworks.body_centroid_mm": Region.MassValue.Centroid,
                **(
                    {
                        "native_scope_object": BodyRecord["object_index"],
                        "native_scope_owner_word": BodyRecord["raw_owner_word"],
                        "native_scope_terminal_word": BodyRecord["raw_terminal_word"],
                    }
                    if BodyRecord is not None
                    else {}
                ),
            }
        ),
    )
