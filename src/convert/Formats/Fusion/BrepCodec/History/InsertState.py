from convert.Formats.Fusion.BrepCodec.History.StateHeader import MakeStateHead
from convert.Formats.Fusion.BrepCodec.Models.HistoryState import HistoryState
from convert.Formats.Fusion.GeometryCodec.EntityRef import EntityRef
from convert.Formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord
from convert.Formats.Fusion.GeometryCodec.GeometryValue import KGeometryValue


# the insert state operation needs a consistent construction rule so topology identity survives native history reconstruction
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
