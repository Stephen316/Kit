from convert.formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.formats.Fusion.BrepCodec.Journal.Materialize import Materialize
from convert.formats.Fusion.BrepCodec.Journal.PolyAuthor.MakePolyStates import (
    MakePolyStates,
)
from convert.formats.Fusion.BrepCodec.Journal.Round.MakeRoundNodes import MakeRoundNodes
from convert.formats.Fusion.BrepCodec.Journal.Round.SphereBody import SphereBody
from convert.formats.Fusion.BrepCodec.Journal.Round.TorusBody import TorusBody
from convert.formats.Fusion.BrepCodec.Journal.States.StreamState import StreamState
from convert.formats.Fusion.BrepCodec.Models.BrepHeader import BrepHeader
from convert.formats.Fusion.BrepCodec.Models.HistoryState import HistoryState
from convert.formats.Fusion.GeometryCodec.GeometryStamp import GeometryStamp


def CreateRoundBody(
    Model: SphereBody | TorusBody, History: HistoryState, Stamp: GeometryStamp
) -> JournalModel:
    if History.MaxStateId is None:
        raise ValueError("Fusion round body requires an explicit history maximum")
    Entities = MakeRoundNodes(Model)
    Stream = StreamState(
        History.CurrentStateId,
        History.MaxStateId,
        0,
        History.NextEntityTag,
        -1,
        0,
        1,
        -1,
    )
    Result = JournalModel(
        BrepHeader(23200, 2, 3, 50.0, 1e-6, 1e-10),
        Stamp,
        len(Entities),
        Entities,
        Stream,
        MakePolyStates(History, len(Entities)),
    )
    _ = Materialize(Result)
    return Result
