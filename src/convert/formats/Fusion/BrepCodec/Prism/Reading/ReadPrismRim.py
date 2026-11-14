from convert.formats.Fusion.Topology.AsmEdge.AsmFields import (
    IsAsmFlag,
    ReadAsmPtr,
    RequireAsm,
)
from convert.formats.Fusion.Topology.AsmEdge.AsmRim import AsmUse
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmTable


def ReadPrismRim(Table: AsmTable, FaceId: int, LoopId: int) -> tuple[AsmUse, ...]:
    LoopValue = RequireAsm(Table, LoopId, "loop", 6)
    if ReadAsmPtr(LoopValue, 3) != -1 or ReadAsmPtr(LoopValue, 5) != FaceId:
        raise ValueError("Unsupported prism face loop ownership")
    First = ReadAsmPtr(LoopValue, 4)
    Current = First
    Values: list[AsmUse] = []
    for _ in range(4):
        Record = RequireAsm(Table, Current, "coedge", 11)
        if ReadAsmPtr(Record, 8) != LoopId or ReadAsmPtr(Record, 10) != -1:
            raise ValueError("Unsupported prism coedge owner or pcurve")
        Values.append(
            AsmUse(
                Current,
                FaceId,
                ReadAsmPtr(Record, 6),
                ReadAsmPtr(Record, 5),
                ReadAsmPtr(Record, 4),
                IsAsmFlag(Record, 7),
                None,
            )
        )
        Current = ReadAsmPtr(Record, 3)
    if Current != First or len({Value.Identity for Value in Values}) != 4:
        raise ValueError("Prism face must have one four-edge ring")
    if any(
        Value.Before != Values[Index - 1].Identity for Index, Value in enumerate(Values)
    ):
        raise ValueError("Prism coedge ring is not reciprocal")
    return tuple(Values)
