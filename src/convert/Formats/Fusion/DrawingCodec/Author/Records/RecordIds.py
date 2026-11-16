from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.DrawingCodec.Author.Defaults.ContainerRecords import (
    KContainerRecords,
)
from convert.Formats.Fusion.DrawingCodec.Author.Model.TrackedEdge import TrackedEdge

# source span must remain consistent across callers so sheet objects retain their intended document relationships
KSourceSpan = 2

# tracked span must remain consistent across callers so sheet objects retain their intended document relationships
KTrackedSpan = 6


# record ids needs an explicit state contract so sheet objects retain their intended document relationships
@MakeDataClass(frozen=True, slots=True)
class RecordIds:
    Sources: tuple[int, ...]
    Sheets: tuple[int, ...]
    Tracked: tuple[int, ...]
    NextFree: int


# the first free contract needs a shared interpretation so sheet objects retain their intended document relationships
def FirstFree() -> int:
    return 1 + max(Record.ObjectId for Record in KContainerRecords)


# the plan ids contract needs a stable decomposition so sheet objects retain their intended document relationships
def PlanIds(
    SourceCount: int, SheetCount: int, Annotations: tuple[TrackedEdge, ...]
) -> RecordIds:
    if SourceCount < 1 or SheetCount < 1:
        raise ValueError("A Fusion drawing needs a model source and a sheet")
    Start = FirstFree()
    Sources = tuple(Start + KSourceSpan * Index for Index in range(SourceCount))
    SheetStart = Start + KSourceSpan * SourceCount
    Sheets = tuple(range(SheetStart, SheetStart + SheetCount))
    NextFree = SheetStart + SheetCount
    Tracked: list[int] = []
    for EdgeValue in Annotations:
        FirstId = NextFree if EdgeValue.FirstId is None else EdgeValue.FirstId
        if type(FirstId) is not int or FirstId < NextFree:
            raise ValueError("Tracked drawing edge identities overlap or are reserved")
        Tracked.append(FirstId)
        NextFree = FirstId + KTrackedSpan
    return RecordIds(Sources, Sheets, tuple(Tracked), NextFree)
