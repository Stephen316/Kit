from convert.Formats.Fusion.BrepCodec.Frustum.Models.FrustumHistory import (
    FrustumHistory,
)
from convert.Formats.Fusion.BrepCodec.Frustum.ReadFrustumHist import ReadFrustumHist
from convert.Formats.Fusion.BrepCodec.Models.HistoryModel import HistoryModel
from convert.Formats.Fusion.BrepCodec.Prism.Models.PrismHistory import PrismHistory
from convert.Formats.Fusion.BrepCodec.Prism.ReadPrismHist import ReadPrismHist
from convert.Formats.Fusion.BrepCodec.ReadHistory import ReadHistory


# the typed body operation needs a distinct decoding boundary so model state retains its native feature and ownership relationships
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
