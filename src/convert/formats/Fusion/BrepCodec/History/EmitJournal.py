from convert.formats.Fusion.BrepCodec.History.EmptyState import MakeEmptyState
from convert.formats.Fusion.BrepCodec.History.InsertState import MakeInsertState
from convert.formats.Fusion.BrepCodec.History.Preamble import MakePreamble
from convert.formats.Fusion.BrepCodec.Models.HistoryState import HistoryState
from convert.formats.Fusion.BrepCodec.Wire.EmitBrepRecord import EmitBrepRecord
from convert.formats.Fusion.GeometryCodec.EncodeSmbName import EncodeSmbName


def EmitJournal(History: HistoryState, RecordCount: int) -> bytes:
    return (
        EncodeSmbName("Begin-of-ASM-History-Data")
        + EmitBrepRecord(MakePreamble(History))
        + EmitBrepRecord(MakeInsertState(History, RecordCount))
        + EmitBrepRecord(MakeEmptyState(History))
        + EncodeSmbName("End-of-ASM-History-Section")
        + EncodeSmbName("End-of-ASM-data")
    )
