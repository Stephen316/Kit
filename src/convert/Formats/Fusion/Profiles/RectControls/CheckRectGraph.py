from collections import Counter

from convert.Formats.Fusion.Assembly.AssemblyHistory import HistoryLink
from convert.Formats.Fusion.Assembly.Solids.ScopeGraph import ReadScopeGraph
from convert.Formats.Fusion.Profiles.RectControls.SketchDimRows import SketchDimRow
from convert.Formats.Fusion.RecordSpan import RecordSpan


# the reciprocal graph must corroborate the six owner links without inventing expression edges
def CheckRectGraph(
    BulkData: bytes,
    Owners: dict[int, RecordSpan],
    OwnerId: int,
    DimRows: tuple[SketchDimRow, ...],
) -> RecordSpan:
    Expected = Counter((Value.OwnerId, Value.BindId, 1) for Value in DimRows)
    Watched = {
        Identity
        for Value in DimRows
        for Identity in (Value.RelationId, Value.BindId, Value.ValueId)
    }
    Graph = ReadScopeGraph(BulkData, Owners, OwnerId)
    Incidence = {
        EdgeValue: Count
        for EdgeValue, Count in Graph.items()
        if EdgeValue[0] in Watched or EdgeValue[1] in Watched
    }
    if len(Expected) != len(DimRows) or Incidence != dict(Expected):
        raise ValueError(
            "Fusion rectangle dependency graph and owned dimension bindings disagree"
        )
    return Owners[HistoryLink(BulkData, Owners[OwnerId], 44)]
