from datetime import UTC, datetime as DateTime

from convert.formats.Fusion.BrepCodec.Journal.EmitJournal import EmitJournal
from convert.formats.Fusion.BrepCodec.Journal.Geometry.BodyNode import BodyNode
from convert.formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.formats.Fusion.BrepCodec.Journal.Materialize import Materialize
from convert.formats.Fusion.BrepCodec.Journal.States.StreamState import StreamState
from convert.formats.Fusion.BrepCodec.Models.BrepHeader import BrepHeader
from convert.formats.Fusion.DocumentCodec.PartFeatures.History.AssembleHist import (
    AssembleNodes,
    LifeSlots,
    StateChanges,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.History.ChainStates import (
    ChainStates,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.History.DraftState import (
    DraftState,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.History.StateLedger import (
    StateContents,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.History.TagLedger import (
    TagLedger,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.History.VersionTable import (
    VersionTable,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.ShapeBody import ShapeBody
from convert.formats.Fusion.GeometryCodec.GeometryStamp import GeometryStamp


def PartJournal(
    Stages: tuple[tuple[ShapeBody, ...], ...],
    StateIds: tuple[int, ...],
    InitialId: int,
    UnixMicros: float,
) -> JournalModel:
    if not Stages or len(Stages) != len(StateIds):
        raise ValueError("Fusion part history requires one state per timeline solid")
    Ledger = TagLedger()
    Drafts = tuple(DraftState(Bodies, Ledger, UnixMicros) for Bodies in Stages)
    Contents = StateContents(Drafts)
    Positions, ActiveCount, Order = VersionTable(Contents)
    Lives = LifeSlots(Contents, Positions)
    Entities = AssembleNodes(Contents, Positions, Order, Lives)
    Changes = [
        StateChanges(Contents, Positions, Lives, Index) for Index in range(len(Stages))
    ]
    Stream = StreamState(StateIds[-1], StateIds[-1], 0, Ledger.NextTag, -1, 0, 1, -1)
    Bodies = sum(
        isinstance(NodeValue, BodyNode) for NodeValue in Entities[:ActiveCount]
    )
    Stamp = GeometryStamp(
        "Kit", "Fusion native document codec", DateTime.now(UTC).isoformat()
    )
    Header = BrepHeader(23200, Bodies + 1, 3, 50.0, 1e-6, 1e-10)
    Model = JournalModel(
        Header,
        Stamp,
        ActiveCount,
        Entities,
        Stream,
        ChainStates(StateIds, InitialId, Changes),
    )
    _ = Materialize(Model)
    return Model


def EmitPartHist(
    Stages: tuple[tuple[ShapeBody, ...], ...],
    StateIds: tuple[int, ...],
    InitialId: int,
    UnixMicros: float,
) -> bytes:
    return EmitJournal(PartJournal(Stages, StateIds, InitialId, UnixMicros))
