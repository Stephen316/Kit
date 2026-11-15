from convert.formats.Fusion.BrepCodec.Journal.Validation.ResolveSlot import ResolveSlot
from convert.formats.Fusion.Topology.AsmEdge.AsmFields import ReadAsmPtr
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord


# the live reference operation needs a distinct decoding boundary so inconsistent revision links fail before history reconstruction
def ReadLiveRef(Record: AsmRecord, Index: int, Aliases: tuple[int, ...]) -> int:
    Reference = ReadAsmPtr(Record, Index)
    return -1 if Reference == -1 else ResolveSlot(Aliases, Reference)
