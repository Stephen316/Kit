from convert.Formats.Fusion.BrepCodec.Journal.Complex.Authoring.CheckNurbsBody import (
    CheckNurbsBody,
)
from convert.Formats.Fusion.BrepCodec.Journal.Complex.Authoring.MakeNurbsNodes import (
    MakeNurbsCurves,
    MakeNurbsEdges,
    MakeNurbsFaces,
    MakeNurbsUses,
)
from convert.Formats.Fusion.BrepCodec.Journal.Complex.Authoring.NurbsBody import (
    NurbsBody,
)
from convert.Formats.Fusion.BrepCodec.Journal.Complex.Authoring.NurbsLayout import (
    MakeNurbsLayout,
)
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.AsmRoot import AsmRoot
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.BodyNode import BodyNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.EntityPrefix import EntityPrefix
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.LumpNode import LumpNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.ShellNode import ShellNode
from convert.Formats.Fusion.BrepCodec.Journal.JournalEntity import KJournalEntity
from convert.Formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.Formats.Fusion.BrepCodec.Journal.Materialize import Materialize
from convert.Formats.Fusion.BrepCodec.Journal.PolyAuthor.MakePolyStates import (
    MakePolyStates,
)
from convert.Formats.Fusion.BrepCodec.Journal.States.StreamState import StreamState
from convert.Formats.Fusion.BrepCodec.Models.BrepHeader import BrepHeader
from convert.Formats.Fusion.BrepCodec.Models.HistoryState import HistoryState
from convert.Formats.Fusion.GeometryCodec.GeometryStamp import GeometryStamp


# the nurbs nodes operation needs a consistent construction rule so nested spline and surface records retain their relationships
def MakeNurbsNodes(Model: NurbsBody) -> tuple[KJournalEntity, ...]:
    CheckNurbsBody(Model)
    Layout = MakeNurbsLayout(Model)
    Prefix = EntityPrefix(-1, -1)
    Coedges = MakeNurbsUses(Model, Layout)
    Entities = (
        AsmRoot(-1, -1, "232.5.0.65535"),
        BodyNode(EntityPrefix(-1, Model.EntityTag), 2),
        LumpNode(Prefix, -1, 3, 1),
        ShellNode(Prefix, -1, 4, 2),
        *MakeNurbsFaces(Model, Layout),
        *Coedges,
        *MakeNurbsEdges(Model, Layout, Coedges),
        *MakeNurbsCurves(Model, Layout),
    )
    if len(Entities) != Layout.EntityCount:
        raise ValueError("Fusion NURBS body layout does not match its records")
    return Entities


# create nurbs body needs an explicit validity boundary so nested spline and surface records retain their relationships
def CreateNurbsBody(
    Model: NurbsBody, History: HistoryState, Stamp: GeometryStamp
) -> JournalModel:
    if History.MaxStateId is None:
        raise ValueError("Fusion NURBS body requires an explicit history maximum")
    Entities = MakeNurbsNodes(Model)
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
