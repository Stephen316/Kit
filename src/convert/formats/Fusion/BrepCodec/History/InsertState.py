from convert.formats.Fusion.BrepCodec.History.StateHeader import MakeStateHead
from convert.formats.Fusion.BrepCodec.Models.HistoryState import HistoryState
from convert.formats.Fusion.GeometryCodec.EntityRef import EntityRef
from convert.formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord
from convert.formats.Fusion.GeometryCodec.GeometryValue import KGeometryValue


def MakeInsertState(History: HistoryState, RecordCount: int) -> GeometryRecord:
    Values: list[KGeometryValue] = [
        *MakeStateHead(History.CurrentId, 0, -1, 1),
        1,
        EntityRef(0),
        History.BoardStatus,
    ]
    for Index in range(1, RecordCount):
        Values.extend((1, EntityRef(-1), EntityRef(Index)))
    return GeometryRecord("delta_state", (*Values, 0, 0, 0))
