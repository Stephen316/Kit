from collections.abc import Sequence
from hashlib import sha256 as ShaDigest

from convert.adapters.solidworks.Container.Archive import ArchiveError
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Core.Partition.ScopedPartition import KScopeSchema
from interchange.Payloads.PayloadRecord import BrepPayload
from interchange.Payloads.PayloadRoles import PayloadRole


# partition identity comes from the selected configuration and must bind the exact native bytes
def ReadPartBytes(
    Payloads: Sequence[BrepPayload], ConfigId: int
) -> tuple[BrepPayload, bytes]:
    RequireArch(
        type(ConfigId) is int and ConfigId >= 0, True, "active configuration identity"
    )
    Stream = f"Contents/Config-{ConfigId}-Partition"
    Matches = [
        ItemValue
        for ItemValue in Payloads
        if ItemValue.source_stream == Stream and ItemValue.kind == "partition"
    ]
    RequireArch(len(Matches), 1, "unique active scoped partition payload")
    (Payload,) = Matches
    RequireArch(
        (Payload.format_id, Payload.role, Payload.schema),
        ("parasolid", PayloadRole.BREP, KScopeSchema),
        "active scoped Parasolid payload identity",
    )
    RequireArch(
        bool(Payload.id) and sum(Value.id == Payload.id for Value in Payloads) == 1,
        True,
        "unique active partition payload ID",
    )
    DataValue = Payload.data
    if DataValue is None or ShaDigest(DataValue).hexdigest() != Payload.sha256:
        raise ArchiveError(
            "active scoped partition payload bytes do not match their digest"
        )
    if Payload.provenance is not None:
        RequireArch(
            all(
                SpanValue.stream == Stream
                and SpanValue.offset >= 0
                and SpanValue.length > 0
                for SpanValue in Payload.provenance.spans
            ),
            True,
            "active partition payload provenance stays in its configured stream",
        )
    return Payload, DataValue
