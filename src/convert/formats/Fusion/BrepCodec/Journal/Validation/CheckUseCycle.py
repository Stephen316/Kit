from convert.formats.Fusion.BrepCodec.Journal.Validation.ReadLiveRef import ReadLiveRef
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord


def CheckUseCycle(
    UseSlots: tuple[int, ...], Records: dict[int, AsmRecord], Aliases: tuple[int, ...]
) -> None:
    Order = [UseSlots[0]]
    while len(Order) < len(UseSlots):
        Partner = ReadLiveRef(Records[Order[-1]], 5, Aliases)
        if Partner not in UseSlots or Partner in Order:
            raise ValueError("Fusion nonmanifold edge partners do not form one ring")
        Order.append(Partner)
    if ReadLiveRef(Records[Order[-1]], 5, Aliases) != Order[0]:
        raise ValueError("Fusion nonmanifold edge partners do not form one ring")
    if len({Records[SlotId].Tokens[7] for SlotId in Order}) != 2:
        raise ValueError("Fusion nonmanifold edge uses need both senses")
