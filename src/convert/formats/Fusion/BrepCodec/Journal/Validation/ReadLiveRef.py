from convert.formats.Fusion.BrepCodec.Journal.Validation.ResolveSlot import ResolveSlot
from convert.formats.Fusion.Topology.AsmEdge.AsmFields import ReadAsmPtr
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord


def ReadLiveRef(Record: AsmRecord, Index: int, Aliases: tuple[int, ...]) -> int:
    Reference = ReadAsmPtr(Record, Index)
    return -1 if Reference == -1 else ResolveSlot(Aliases, Reference)
