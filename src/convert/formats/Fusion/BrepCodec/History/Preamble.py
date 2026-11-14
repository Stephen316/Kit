from convert.formats.Fusion.BrepCodec.Models.HistoryState import HistoryState
from convert.formats.Fusion.GeometryCodec.EntityRef import EntityRef
from convert.formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord


def MakePreamble(History: HistoryState) -> GeometryRecord:
    return GeometryRecord(
        "history_stream",
        (
            History.CurrentStateId,
            (
                History.CurrentStateId
                if History.MaxStateId is None
                else History.MaxStateId
            ),
            0,
            History.NextEntityTag,
            EntityRef(-1),
            EntityRef(0),
            EntityRef(1),
            EntityRef(-1),
        ),
    )
