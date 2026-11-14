from convert.formats.Fusion.BrepCodec.Journal.Validation.ReadLiveRef import ReadLiveRef
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord


def CheckUseRing(
    SlotId: int, Records: dict[int, AsmRecord], Aliases: tuple[int, ...]
) -> None:
    Record = Records[SlotId]
    OwnerLoop = ReadLiveRef(Record, 8, Aliases)
    NextUse = Records[ReadLiveRef(Record, 3, Aliases)]
    PriorUse = Records[ReadLiveRef(Record, 4, Aliases)]
    if (
        ReadLiveRef(NextUse, 4, Aliases) != SlotId
        or ReadLiveRef(PriorUse, 3, Aliases) != SlotId
        or ReadLiveRef(NextUse, 8, Aliases) != OwnerLoop
        or ReadLiveRef(PriorUse, 8, Aliases) != OwnerLoop
    ):
        raise ValueError("Fusion coedge loop links are not reciprocal")
