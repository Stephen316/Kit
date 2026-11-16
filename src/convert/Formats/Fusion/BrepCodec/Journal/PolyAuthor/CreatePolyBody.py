from convert.Formats.Fusion.BrepCodec.Journal.Geometry.TransformNode import (
    TransformNode,
)
from convert.Formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.Formats.Fusion.BrepCodec.Journal.Planar.ReadPlanarState import (
    ReadPlanarState,
)
from convert.Formats.Fusion.BrepCodec.Journal.PolyAuthor.MakePolyLayout import (
    MakePolyLayout,
)
from convert.Formats.Fusion.BrepCodec.Journal.PolyAuthor.MakePolyNodes import (
    MakePolyNodes,
)
from convert.Formats.Fusion.BrepCodec.Journal.PolyAuthor.MakePolyStates import (
    MakePolyStates,
)
from convert.Formats.Fusion.BrepCodec.Journal.PolyAuthor.Polyhedron import Polyhedron
from convert.Formats.Fusion.BrepCodec.Journal.States.StreamState import StreamState
from convert.Formats.Fusion.BrepCodec.Models.BrepHeader import BrepHeader
from convert.Formats.Fusion.BrepCodec.Models.HistoryState import HistoryState
from convert.Formats.Fusion.GeometryCodec.GeometryStamp import GeometryStamp


# create poly body needs an explicit validity boundary so topology changes retain their native revision relationships
def CreatePolyBody(
    Model: Polyhedron,
    History: HistoryState,
    Stamp: GeometryStamp,
    Placement: TransformNode | None = None,
) -> JournalModel:
    Layout = MakePolyLayout(Model)
    Entities = MakePolyNodes(Layout, Model.EntityTag, Placement)
    if History.MaxStateId is None:
        raise ValueError("Fusion polyhedron requires an explicit history maximum")
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
    _ = ReadPlanarState(Result)
    return Result
