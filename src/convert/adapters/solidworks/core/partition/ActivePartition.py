from collections.abc import Sequence
from dataclasses import dataclass as Dataclass, replace as Replace

from convert.adapters.solidworks.container.Parasolid import decode_brep_model as DecodeBrep
from interchange.brep.topology.BrepModel import BrepModel
from interchange import BrepPayload


# a recognized active partition may be present even if its body is unsupported
@Dataclass(frozen=True, slots=True)
class ActivePartition:
    ModelValue: BrepModel | None
    PayloadId: str | None


# source identity selects the active configuration rather than an embedded profile packet
def ReadActivePart(
    Payloads: Sequence[BrepPayload], ConfigId: int | None, BodyId: str
) -> ActivePartition | None:
    if ConfigId is None:
        return None
    Stream = f"Contents/Config-{ConfigId}-Partition"
    Matches = tuple(Value for Value in Payloads if Value.source_stream == Stream)
    if not Matches:
        return None
    Partitions = tuple(Value for Value in Matches if Value.kind == "partition")
    if len(Partitions) != 1:
        return ActivePartition(None, None)
    (Source,) = Partitions
    ModelValue = DecodeBrep(Source.data) if Source.data is not None else None
    if ModelValue is not None and len(ModelValue.bodies) == 1:
        (BodyValue,) = ModelValue.bodies
        if BodyValue.design_body_id in ("", BodyId):
            ModelValue = Replace(ModelValue, bodies=(Replace(BodyValue, design_body_id=BodyId),))
    return ActivePartition(ModelValue, Source.id)
