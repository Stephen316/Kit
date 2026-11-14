from typing import cast as CastValue

from convert.formats.Fusion.BrepCodec.Frustum.EmitFrustumHist import EmitFrustumHist
from convert.formats.Fusion.BrepCodec.Frustum.Models.FrustumHistory import (
    FrustumHistory,
)
from convert.formats.Fusion.BrepCodec.EmitHistory import EmitHistory
from convert.formats.Fusion.BrepCodec.Journal.EmitJournal import EmitJournal
from convert.formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.formats.Fusion.BrepCodec.Models.BrepHeader import BrepHeader
from convert.formats.Fusion.BrepCodec.Models.HistoryModel import HistoryModel
from convert.formats.Fusion.BrepCodec.Prism.EmitPrismHist import EmitPrismHist
from convert.formats.Fusion.BrepCodec.Prism.Models.PrismHistory import PrismHistory
from convert.formats.Fusion.ContainerCodec.Model.ContainerPart import ContainerPart
from convert.formats.Fusion.DocumentCodec.Model.DocumentBody import DocumentBody


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
