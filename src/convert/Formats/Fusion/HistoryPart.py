from dataclasses import dataclass as Dataclass

from convert.Formats.Fusion.HistoryGroup import HistoryGroup
from interchange.Features.FeatureStep import FeatureStep


# each native owner keeps its own chronology and group information
@Dataclass(frozen=True, slots=True)
class HistoryPart:
    HistoryId: int
    OwnerId: int
    EntryIds: tuple[int, ...]
    Groups: tuple[HistoryGroup, ...]
    Steps: tuple[FeatureStep, ...]
