from convert.formats.Fusion.BrepCodec.History.EmptyState import MakeEmptyState
from convert.formats.Fusion.BrepCodec.History.Preamble import MakePreamble
from convert.formats.Fusion.BrepCodec.History.StateHeader import MakeStateHead
from convert.formats.Fusion.BrepCodec.Models.HistoryState import HistoryState
from convert.formats.Fusion.BrepCodec.Reading.GeometryTokens import GeometryTokens
from convert.formats.Fusion.GeometryCodec.EntityRef import EntityRef
from convert.formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord
from convert.formats.Fusion.Topology.AsmEdge.AsmFields import ReadAsmInt, ReadAsmPtr
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord


def ReadJournal(Records: tuple[AsmRecord, ...], EntityCount: int) -> HistoryState:
    if len(Records) != 3 or tuple(Entry.Name for Entry in Records) != (
        "history_stream",
        "delta_state",
        "delta_state",
    ):
        raise ValueError("Unsupported Fusion BRep history state graph")
    Preamble, Current, Initial = Records
    History = HistoryState(
        ReadAsmInt(Current, 0),
        ReadAsmInt(Initial, 0),
        ReadAsmInt(Preamble, 0),
        ReadAsmInt(Preamble, 3),
        ReadAsmInt(Current, 11),
        ReadAsmInt(Preamble, 1),
    )
    Expected = GeometryTokens((MakePreamble(History), MakeEmptyState(History)))
    if (Preamble, Initial) != Expected:
        raise ValueError("Unsupported Fusion BRep history preamble or initial state")
    Prefix = GeometryRecord(
        "delta_state",
        (
            *MakeStateHead(History.CurrentId, 0, -1, 1),
            1,
            EntityRef(0),
            History.BoardStatus,
        ),
    )
    PrefixTokens = GeometryTokens((Prefix,))[0].Tokens
    if Current.Tokens[:12] != PrefixTokens or len(Current.Tokens) != 15 + 3 * (
        EntityCount - 1
    ):
        raise ValueError("Unsupported Fusion BRep history board framing")
    Insertions: set[int] = set()
    for Offset in range(12, len(Current.Tokens) - 3, 3):
        if ReadAsmInt(Current, Offset) != 1 or ReadAsmPtr(Current, Offset + 1) != -1:
            raise ValueError("Unsupported Fusion BRep non-insertion history change")
        Identity = ReadAsmPtr(Current, Offset + 2)
        if not 1 <= Identity < EntityCount or Identity in Insertions:
            raise ValueError("Invalid Fusion BRep history insertion identity")
        Insertions.add(Identity)
    if (
        Current.Tokens[-3:] != ((4, 0), (4, 0), (4, 0))
        or len(Insertions) != EntityCount - 1
    ):
        raise ValueError("Incomplete Fusion BRep insertion journal")
    return History
