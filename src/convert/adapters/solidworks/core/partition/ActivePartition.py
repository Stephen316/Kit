from collections.abc import Iterable, Sequence
from dataclasses import dataclass as Dataclass, replace as Replace
from re import compile as CompileRegex

from convert.adapters.solidworks.container.Parasolid import decode_brep_model as DecodeBrep
from interchange.brep.topology.BrepModel import BrepModel
from interchange import BrepPayload


# named part stations are authoritative before transport decoding has succeeded
KPartitionName = CompileRegex(r"Contents/Config-[0-9]+-Partition")


# a recognized active partition may be present even if its body is unsupported
@Dataclass(frozen=True, slots=True)
class ActivePartition:
    ModelValue: BrepModel | None
    PayloadId: str | None


# source identity selects the active configuration rather than an embedded profile packet
def ReadActivePart(
    Payloads: Sequence[BrepPayload],
    ConfigId: int | None,
    BodyId: str | None,
    RawStreams: Iterable[str],
) -> ActivePartition | None:
    if ConfigId is None:
        return None
    Stream = f"Contents/Config-{ConfigId}-Partition"
    Matches = tuple(Value for Value in Payloads if Value.source_stream == Stream)
    if not Matches:
        IsOwned = BodyId is not None or any(
            KPartitionName.fullmatch(NameValue) for NameValue in RawStreams
        )
        return ActivePartition(None, None) if IsOwned else None
    Partitions = tuple(Value for Value in Matches if Value.kind == "partition")
    if len(Partitions) != 1:
        return ActivePartition(None, None)
    (Source,) = Partitions
    ModelValue = DecodeBrep(Source.data) if Source.data is not None else None
    if (
        BodyId is not None
        and ModelValue is not None
        and len(ModelValue.bodies) == 1
        and len(ModelValue.regions) == 1
        and ModelValue.regions[0].solid
    ):
        (BodyValue,) = ModelValue.bodies
        if (
            BodyValue.design_body_id in ("", BodyId)
            and BodyValue.region_ids == (ModelValue.regions[0].id,)
        ):
            ModelValue = Replace(ModelValue, bodies=(Replace(BodyValue, design_body_id=BodyId),))
    return ActivePartition(ModelValue, Source.id)
