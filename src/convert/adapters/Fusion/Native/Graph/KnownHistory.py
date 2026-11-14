from typing import TypeAlias

from convert.formats.Fusion.BrepCodec.Frustum.Models.FrustumHistory import (
    FrustumHistory,
)
from convert.formats.Fusion.BrepCodec.Models.HistoryModel import HistoryModel
from convert.formats.Fusion.BrepCodec.Prism.Models.PrismHistory import PrismHistory

KKnownHistory: TypeAlias = (  # lgtm[py/unused-global-variable]
    HistoryModel | FrustumHistory | PrismHistory
)
