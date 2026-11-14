from convert.formats.Fusion.BrepCodec.Journal.Validation.CheckUseCycle import (
    CheckUseCycle,
)
from convert.formats.Fusion.BrepCodec.Journal.Validation.ReadLiveRef import ReadLiveRef
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord


def CheckUsePairs(
    EdgeRef: int,
    UseSlots: tuple[int, ...],
    Records: dict[int, AsmRecord],
    Aliases: tuple[int, ...],
) -> None:
    if len(UseSlots) not in (1, 2, 3, 4):
        raise ValueError("Unsupported Fusion nonmanifold edge-use count")
    if ReadLiveRef(Records[EdgeRef], 7, Aliases) not in UseSlots:
        raise ValueError("Fusion edge owner is not an incident coedge")
    if len(UseSlots) > 2:
        CheckUseCycle(UseSlots, Records, Aliases)
        return
    for SlotId in UseSlots:
        Expected = (
            -1
            if len(UseSlots) == 1
            else next(Value for Value in UseSlots if Value != SlotId)
        )
        if ReadLiveRef(Records[SlotId], 5, Aliases) != Expected:
            raise ValueError("Fusion edge partners disagree with boundary incidence")
