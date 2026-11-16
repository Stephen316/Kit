from typing import TypeAlias

from convert.Formats.Fusion.BrepCodec.Frustum.Models.FrustumHistory import (
    FrustumHistory,
)
from convert.Formats.Fusion.BrepCodec.Models.HistoryModel import HistoryModel
from convert.Formats.Fusion.BrepCodec.Prism.Models.PrismHistory import PrismHistory

# the known history variants need one shared contract so native adapter translation cannot omit a supported value shape
KKnownHistory: TypeAlias = (  # lgtm[py/unused-global-variable]
    HistoryModel | FrustumHistory | PrismHistory
)
