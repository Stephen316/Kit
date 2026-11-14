from convert.formats.Fusion.BrepCodec.Frustum.Models.FrustumHistory import (
    FrustumHistory,
)
from convert.formats.Fusion.BrepCodec.Frustum.ReadFrustumHist import ReadFrustumHist
from convert.formats.Fusion.BrepCodec.Models.HistoryModel import HistoryModel
from convert.formats.Fusion.BrepCodec.Prism.Models.PrismHistory import PrismHistory
from convert.formats.Fusion.BrepCodec.Prism.ReadPrismHist import ReadPrismHist
from convert.formats.Fusion.BrepCodec.ReadHistory import ReadHistory


def ReadTypedBody(
    Payload: bytes, Profile: str
) -> HistoryModel | PrismHistory | FrustumHistory | None:
    try:
        if Profile == "frustum":
            return ReadFrustumHist(Payload)
        if Profile == "cylinder":
            return ReadHistory(Payload)
        if Profile == "prism":
            return ReadPrismHist(Payload)
    except ValueError:
        return None
    return None
