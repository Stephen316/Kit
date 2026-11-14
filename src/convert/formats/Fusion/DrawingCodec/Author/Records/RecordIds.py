from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.DrawingCodec.Author.Defaults.ContainerRecords import (
    KContainerRecords,
)
from convert.formats.Fusion.DrawingCodec.Author.Model.TrackedEdge import TrackedEdge

KSourceSpan = 2
KTrackedSpan = 6


@MakeDataClass(frozen=True, slots=True)
class RecordIds:
    Sources: tuple[int, ...]
    Sheets: tuple[int, ...]
    Tracked: tuple[int, ...]
    NextFree: int


def FirstFree() -> int:
    return 1 + max(Record.ObjectId for Record in KContainerRecords)


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
