from dataclasses import dataclass as MakeDataClass
from typing import TypeAlias

from convert.formats.Fusion.BrepCodec.Frustum.Models.FrustumHistory import (
    FrustumHistory,
)
from convert.formats.Fusion.BrepCodec.Models.HistoryModel import HistoryModel
from convert.formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.formats.Fusion.BrepCodec.Prism.Models.PrismHistory import PrismHistory

# the body history variants need one shared contract so document reconstruction cannot omit a supported value shape
KBodyHistory: TypeAlias = HistoryModel | PrismHistory | FrustumHistory | JournalModel


# document body needs an explicit state contract so model state retains its native feature and ownership relationships
@MakeDataClass(frozen=True, slots=True)
class DocumentBody:
    PartName: str
    History: KBodyHistory
