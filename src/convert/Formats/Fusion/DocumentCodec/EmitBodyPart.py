from typing import cast as CastValue

from convert.Formats.Fusion.BrepCodec.Frustum.EmitFrustumHist import EmitFrustumHist
from convert.Formats.Fusion.BrepCodec.Frustum.Models.FrustumHistory import (
    FrustumHistory,
)
from convert.Formats.Fusion.BrepCodec.EmitHistory import EmitHistory
from convert.Formats.Fusion.BrepCodec.Journal.EmitJournal import EmitJournal
from convert.Formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.Formats.Fusion.BrepCodec.Models.BrepHeader import BrepHeader
from convert.Formats.Fusion.BrepCodec.Models.HistoryModel import HistoryModel
from convert.Formats.Fusion.BrepCodec.Prism.EmitPrismHist import EmitPrismHist
from convert.Formats.Fusion.BrepCodec.Prism.Models.PrismHistory import PrismHistory
from convert.Formats.Fusion.ContainerCodec.Model.ContainerPart import ContainerPart
from convert.Formats.Fusion.DocumentCodec.Model.DocumentBody import DocumentBody


# the body part operation needs a consistent construction rule so model state retains its native feature and ownership relationships
def EmitBodyPart(Value: DocumentBody) -> ContainerPart:
    History = Value.History
    if isinstance(History, JournalModel):
        return ContainerPart(Value.PartName, EmitJournal(History))
    if not isinstance(
        CastValue(object, History), (HistoryModel, PrismHistory, FrustumHistory)
    ):
        raise ValueError("Unsupported typed Fusion document history")
    if History.Header != BrepHeader(23200, 2, 3, 50.0, 1e-6, 1e-10):
        raise ValueError("Unsupported Fusion document BRep header")
    if isinstance(History, HistoryModel):
        Payload = EmitHistory(
            History.Model,
            History.Identity,
            History.TagSet,
            History.History,
            History.Stamp,
            History.Vertices,
            History.Tracking,
        )
    elif isinstance(History, PrismHistory):
        Payload = EmitPrismHist(
            History.Model,
            History.Identity,
            History.TagSet,
            History.History,
            History.Stamp,
            History.Frame,
        )
    else:
        Payload = EmitFrustumHist(
            History.Model,
            History.Identity,
            History.TagSet,
            History.History,
            History.Stamp,
            History.Frame,
            History.Tracking,
        )
    return ContainerPart(Value.PartName, Payload)
