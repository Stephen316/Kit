from convert.formats.Fusion.BrepCodec.History.StateHeader import MakeStateHead
from convert.formats.Fusion.BrepCodec.Models.HistoryState import HistoryState
from convert.formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord


# the empty state operation needs a consistent construction rule so topology identity survives native history reconstruction
def MakeEmptyState(History: HistoryState) -> GeometryRecord:
    return GeometryRecord(
        "delta_state", (*MakeStateHead(History.InitialId, 1, 0, -1), 0, 0)
    )
