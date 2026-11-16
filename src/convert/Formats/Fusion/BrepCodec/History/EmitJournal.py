from convert.Formats.Fusion.BrepCodec.History.EmptyState import MakeEmptyState
from convert.Formats.Fusion.BrepCodec.History.InsertState import MakeInsertState
from convert.Formats.Fusion.BrepCodec.History.Preamble import MakePreamble
from convert.Formats.Fusion.BrepCodec.Models.HistoryState import HistoryState
from convert.Formats.Fusion.BrepCodec.Wire.EmitBrepRecord import EmitBrepRecord
from convert.Formats.Fusion.GeometryCodec.EncodeSmbName import EncodeSmbName


# the journal operation needs a consistent construction rule so topology identity survives native history reconstruction
def EmitJournal(History: HistoryState, RecordCount: int) -> bytes:
    return (
        EncodeSmbName("Begin-of-ASM-History-Data")
        + EmitBrepRecord(MakePreamble(History))
        + EmitBrepRecord(MakeInsertState(History, RecordCount))
        + EmitBrepRecord(MakeEmptyState(History))
        + EncodeSmbName("End-of-ASM-History-Section")
        + EncodeSmbName("End-of-ASM-data")
    )
