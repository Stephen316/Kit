from collections.abc import Iterable, Sequence
from dataclasses import dataclass as Dataclass, replace as Replace
from re import compile as CompileRegex

from convert.adapters.solidworks.Container.Parasolid import (
    decode_brep_model as DecodeBrep,
)
from convert.Geometry.Parasolid import KBlankDeltaBody, KBlankPartBody, ParaHeaderData
from convert.Geometry.ReadParaSection import ReadEmptyFrame
from interchange.brep.Topology.BrepModel import BrepModel
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
        if BodyValue.design_body_id in ("", BodyId) and BodyValue.region_ids == (
            ModelValue.regions[0].id,
        ):
            ModelValue = Replace(
                ModelValue, bodies=(Replace(BodyValue, design_body_id=BodyId),)
            )
    return ActivePartition(ModelValue, Source.id)


# this schema bounds the two independently observed empty frame bodies
KEmptySchema = "SCH_3701250_37102_13006"

# exact header text separates the active partition from its delta companion
KEmptyPartDesc = ": TRANSMIT FILE (partition) created by modeller version 3701250"

# an empty delta table must carry the matching transmit version
KEmptyDeltaDesc = ": TRANSMIT FILE (deltas) created by modeller version 3701250"


# both complete frames and all empty table bytes must belong to the witnessed schema
def IsEmptyStream(Partition: bytes) -> bool:
    if len(Partition) > 1024:
        return False
    PartSize = 10 + len(KEmptyPartDesc) + len(KEmptySchema) + len(KBlankPartBody)
    FirstSection = ReadEmptyFrame(Partition, 0, PartSize)
    if FirstSection is None:
        return False
    DeltaSize = 10 + len(KEmptyDeltaDesc) + len(KEmptySchema) + len(KBlankDeltaBody)
    LastSection = ReadEmptyFrame(Partition, FirstSection.End, DeltaSize)
    if LastSection is None or LastSection.End != len(Partition):
        return False
    PartHead = ParaHeaderData(FirstSection.Data)
    DeltaHead = ParaHeaderData(LastSection.Data)
    if (
        PartHead is None
        or DeltaHead is None
        or (PartHead.schema, PartHead.description) != (KEmptySchema, KEmptyPartDesc)
        or (DeltaHead.schema, DeltaHead.description) != (KEmptySchema, KEmptyDeltaDesc)
    ):
        return False
    PartBody = FirstSection.Data[PartHead.body_offset :]
    DeltaBody = LastSection.Data[DeltaHead.body_offset :]
    return (
        PartBody[:2] == b"\x00\xef"
        and PartBody[2:] == KBlankPartBody[2:]
        and DeltaBody[:2] == b"\x00\xef"
        and DeltaBody[2:45] == KBlankDeltaBody[2:45]
        and DeltaBody[45:46] == b"\x02"
        and DeltaBody[46:] == KBlankDeltaBody[46:]
    )
