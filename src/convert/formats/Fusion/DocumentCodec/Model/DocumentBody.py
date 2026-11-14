from dataclasses import dataclass as MakeDataClass
from typing import TypeAlias

from convert.formats.Fusion.BrepCodec.Frustum.Models.FrustumHistory import (
    FrustumHistory,
)
from convert.formats.Fusion.BrepCodec.Models.HistoryModel import HistoryModel
from convert.formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.formats.Fusion.BrepCodec.Prism.Models.PrismHistory import PrismHistory

KBodyHistory: TypeAlias = HistoryModel | PrismHistory | FrustumHistory | JournalModel


@MakeDataClass(frozen=True, slots=True)
class DocumentBody:
    PartName: str
    History: KBodyHistory
