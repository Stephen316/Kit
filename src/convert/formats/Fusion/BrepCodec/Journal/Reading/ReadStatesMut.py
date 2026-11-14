from convert.formats.Fusion.BrepCodec.Journal.JournalLimits import (
    KJournalStates,
)
from convert.formats.Fusion.BrepCodec.Journal.States.DeltaState import DeltaState
from convert.formats.Fusion.BrepCodec.Journal.Reading.ReadStateNode import ReadStateNode
from convert.formats.Fusion.MetaCursor import MetaCursor
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import ReadAsmName, ReadAsmRecord


def ReadStatesMut(Cursor: MetaCursor, Width: int = 8) -> tuple[DeltaState, ...]:
    States: list[DeltaState] = []
    while (NameValue := ReadAsmName(Cursor)) != "End-of-ASM-History-Section":
        if NameValue != "delta_state" or len(States) >= KJournalStates:
            raise ValueError("Unsupported Fusion journal state table")
        States.append(ReadStateNode(ReadAsmRecord(Cursor, NameValue, Width)))
    return tuple(States)
